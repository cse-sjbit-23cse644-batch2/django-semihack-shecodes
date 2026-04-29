# curriculum/utils.py - Pixel-Perfect PDF matching exact syllabus format
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, cm, mm
from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer, Table,
                                 TableStyle, PageBreak, Image, KeepTogether)
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY, TA_RIGHT
from reportlab.platypus.flowables import HRFlowable
from reportlab.pdfgen import canvas
from reportlab.platypus import BaseDocTemplate, PageTemplate, Frame
from django.conf import settings
import os
from datetime import datetime


# ── Page geometry ──────────────────────────────────────────────────────────────
PAGE_W, PAGE_H = A4          # 595.27 x 841.89 pts
L_MARGIN  = 1.5 * cm
R_MARGIN  = 1.5 * cm
T_MARGIN  = 1.5 * cm
B_MARGIN  = 2.0 * cm
INNER_W   = PAGE_W - L_MARGIN - R_MARGIN   # usable content width

# Colours
BLACK  = colors.black
WHITE  = colors.white
LGREY  = colors.HexColor('#f0f0f0')   # light-grey cell shading
DGREY  = colors.HexColor('#d0d0d0')   # darker separator shading


# ── Styles ─────────────────────────────────────────────────────────────────────
def make_styles():
    base = getSampleStyleSheet()

    section_heading = ParagraphStyle(
        'SectionHeading',
        parent=base['Normal'],
        fontName='Helvetica-Bold',
        fontSize=10,
        alignment=TA_CENTER,
        spaceAfter=0,
        spaceBefore=0,
        leading=14,
    )
    module_heading = ParagraphStyle(
        'ModuleHeading',
        parent=base['Normal'],
        fontName='Helvetica-Bold',
        fontSize=9.5,
        alignment=TA_LEFT,
        spaceAfter=0,
        spaceBefore=0,
        leading=13,
    )
    normal = ParagraphStyle(
        'Body',
        parent=base['Normal'],
        fontName='Helvetica',
        fontSize=9.5,
        alignment=TA_JUSTIFY,
        spaceAfter=0,
        spaceBefore=0,
        leading=14,
    )
    bold = ParagraphStyle(
        'Bold',
        parent=normal,
        fontName='Helvetica-Bold',
    )
    header_title = ParagraphStyle(
        'HeaderTitle',
        parent=base['Normal'],
        fontName='Helvetica-Bold',
        fontSize=11,
        alignment=TA_CENTER,
        spaceAfter=0,
        spaceBefore=2,
        leading=15,
    )
    co_label = ParagraphStyle(
        'COLabel',
        parent=base['Normal'],
        fontName='Helvetica-Bold',
        fontSize=9.5,
        alignment=TA_CENTER,
        leading=14,
    )
    return {
        'section': section_heading,
        'module':  module_heading,
        'normal':  normal,
        'bold':    bold,
        'header':  header_title,
        'co':      co_label,
    }


# ── Shared table style helpers ─────────────────────────────────────────────────
def grid(t=0.5, c=BLACK):
    return ('GRID', (0, 0), (-1, -1), t, c)

def box(t=0.8, c=BLACK):
    return ('BOX', (0, 0), (-1, -1), t, c)

def pad(top=4, bot=4, left=4, right=4):
    return [
        ('TOPPADDING',    (0, 0), (-1, -1), top),
        ('BOTTOMPADDING', (0, 0), (-1, -1), bot),
        ('LEFTPADDING',   (0, 0), (-1, -1), left),
        ('RIGHTPADDING',  (0, 0), (-1, -1), right),
    ]

def valign_mid():
    return ('VALIGN', (0, 0), (-1, -1), 'MIDDLE')

def valign_top():
    return ('VALIGN', (0, 0), (-1, -1), 'TOP')

def font_size(sz):
    return ('FONTSIZE', (0, 0), (-1, -1), sz)


# ── Page canvas callback – footer ──────────────────────────────────────────────
class SyllabusDocTemplate(BaseDocTemplate):
    """Custom doc template that draws the outer border box and footer on every page."""

    def __init__(self, filepath, start_page=136, **kwargs):
        self.start_page = start_page
        super().__init__(filepath, **kwargs)

        # Single frame that sits inside the outer border
        frame = Frame(
            L_MARGIN, B_MARGIN,
            INNER_W,  PAGE_H - T_MARGIN - B_MARGIN,
            leftPadding=4, rightPadding=4,
            topPadding=4,  bottomPadding=4,
            id='main'
        )
        template = PageTemplate(id='main', frames=[frame],
                                onPage=self._draw_page_decoration)
        self.addPageTemplates([template])

    def _draw_page_decoration(self, canv, doc):
        canv.saveState()

        page_num = doc.page + self.start_page - 1

        # Outer border box (covers the whole usable area)
        canv.setLineWidth(0.8)
        canv.rect(
            L_MARGIN - 4,
            B_MARGIN - 4,
            INNER_W + 8,
            PAGE_H - T_MARGIN - B_MARGIN + 8,
            stroke=1, fill=0
        )

        # Footer: "Dept. of CSE" left, "Page X" right  – below the box
        canv.setFont('Helvetica', 9)
        footer_y = B_MARGIN - 16
        canv.drawString(L_MARGIN, footer_y, 'Dept. of CSE')
        canv.drawRightString(PAGE_W - R_MARGIN, footer_y, f'Page {page_num}')

        canv.restoreState()


# ── Main generator ─────────────────────────────────────────────────────────────
def generate_syllabus_pdf(course, user):
    """
    Generate a pixel-perfect syllabus PDF that matches the reference document.
    All content lives inside the outer-border frame; footer is drawn by the
    page template callback.
    """
    filename = f'{course.course_code}_Syllabus.pdf'
    filepath = os.path.join(settings.MEDIA_ROOT, 'syllabi_pdfs', filename)
    os.makedirs(os.path.dirname(filepath), exist_ok=True)

    doc = SyllabusDocTemplate(
        filepath,
        start_page=136,
        pagesize=A4,
        topMargin=T_MARGIN + 4,
        bottomMargin=B_MARGIN + 4,
        leftMargin=L_MARGIN,
        rightMargin=R_MARGIN,
    )

    S = make_styles()
    story = []

    # ── 1. HEADER IMAGE ────────────────────────────────────────────────────────
    header_image_path = os.path.join(settings.MEDIA_ROOT, 'logos', 'sjbit_logo.png')
    if os.path.exists(header_image_path):
        himg = Image(header_image_path, width=INNER_W, height=3.8 * cm)
        himg.hAlign = 'CENTER'
        story.append(himg)
    else:
        logo_path = os.path.join(settings.MEDIA_ROOT, 'logos', 'sjb_logo.png')
        if os.path.exists(logo_path):
            logo = Image(logo_path, width=2.5 * cm, height=2.5 * cm)
            logo.hAlign = 'CENTER'
            story.append(logo)
    story.append(Spacer(1, 2))

    # "BE in Computer Science and Engineering"
    story.append(Paragraph('BE in Computer Science and Engineering', S['header']))
    story.append(Spacer(1, 4))

    # ── 2. COURSE INFO TABLE ───────────────────────────────────────────────────
    # 6-column table to match the reference exactly (handles the 6-cell CIE row)
    course_type = 'Professional Elective' if course.credits <= 3 else 'Core Course'
    ltp = f"{course.lecture_hours}:{course.tutorial_hours}:{course.practical_hours}:{getattr(course, 'self_learning_hours', '@')}"
    N = S['normal']

    # cw6: 6 columns
    cw6 = [2.9*cm, 2.2*cm, 2.9*cm, 2.2*cm, 2.9*cm, INNER_W - 2.9*cm*3 - 2.2*cm*2]

    info_data = [
        # R0: Semester: | VI | Course Type: | ETC (cols 3-5 merged)
        [Paragraph('<b>Semester:</b>', N), Paragraph(str(course.semester), N),
         Paragraph('<b>Course Type:</b>', N), Paragraph(course_type, N), '', ''],
        # R1: Course Title spans all 6
        [Paragraph(f'<b>Course Title: {course.course_title}</b>', N), '', '', '', '', ''],
        # R2: Course Code | 23CSE644 | Credits: | 3 (cols 3-5 merged)
        [Paragraph('<b>Course Code:</b>', N), Paragraph(course.course_code, N),
         Paragraph('<b>Credits:</b>', N), Paragraph(str(course.credits), N), '', ''],
        # R3: Teaching Hours | value | Total Hours: | value (cols 3-5 merged)
        [Paragraph('<b>Teaching Hours/Week (L:T:P:O)</b>', N), Paragraph(ltp, N),
         Paragraph('<b>Total Hours:</b>', N), Paragraph(str(course.total_hours), N), '', ''],
        # R4: CIE Marks | 50 | SEE Marks | 50 | Total Marks: | 100  (all 6 cells used)
        [Paragraph('<b>CIE Marks:</b>', N), Paragraph(str(course.cie_marks), N),
         Paragraph('<b>SEE Marks:</b>', N), Paragraph(str(course.see_marks), N),
         Paragraph('<b>Total Marks:</b>', N), Paragraph('100', N)],
        # R5: SEE Type | Theory | Exam Hours: | 3 (cols 3-5 merged)
        [Paragraph('<b>SEE Type:</b>', N), Paragraph(getattr(course, 'see_type', 'Theory'), N),
         Paragraph('<b>Exam Hours:</b>', N), Paragraph(str(course.exam_duration), N), '', ''],
    ]

    info_table = Table(info_data, colWidths=cw6, hAlign='LEFT')
    info_ts = TableStyle([
        grid(0.6),
        valign_mid(),
        *pad(5, 5, 6, 6),
        font_size(9.5),
        ('SPAN', (3, 0), (5, 0)),   # Course Type value spans 3-5
        ('SPAN', (0, 1), (5, 1)),   # Course Title spans all
        ('SPAN', (3, 2), (5, 2)),   # Credits value spans 3-5
        ('SPAN', (3, 3), (5, 3)),   # Total Hours value spans 3-5
        ('SPAN', (3, 5), (5, 5)),   # Exam Hours value spans 3-5
    ])
    info_table.setStyle(info_ts)
    story.append(info_table)
    story.append(Spacer(1, 4))

    # ── 3. COURSE OBJECTIVES ──────────────────────────────────────────────────
    objectives_rows = _section_header_row('I.\u2003Course Objectives:', S)
    obj_items = []
    if course.course_objectives:
        for line in course.course_objectives.split('\n'):
            line = line.strip()
            if line:
                obj_items.append(line)
    else:
        obj_items = [
            'Explain the use of learning full stack web development.',
            'Make use of rapid application development in the design of responsive web pages.',
            'Illustrate Models, Views and Templates with their connectivity in Django for full stack web development.',
            'Demonstrate the use of state management and admin interfaces automation in Django.',
            'Design and implement Django apps containing dynamic pages with SQL databases.',
        ]

    obj_content = [Paragraph('This course will enable students to:', S['normal'])]
    for i, item in enumerate(obj_items, 1):
        obj_content.append(Paragraph(f'{i}.\u2002{item}', S['normal']))

    obj_table = _content_block(objectives_rows + obj_content, S)
    story.append(obj_table)
    story.append(Spacer(1, 2))

    # ── 4. TEACHING-LEARNING PROCESS ─────────────────────────────────────────
    tlp_header = _section_header_row('II. Teaching-Learning Process (General Instructions):', S)
    tlp_intro = [Paragraph(
        'These are sample Strategies, which teachers can use to accelerate the attainment of '
        'the various course outcomes.', S['normal'])]
    tlp_items = [
        'Lecturer method (L) need not to be only a traditional lecture method, but alternative '
        'effective teaching methods could be adopted to attain the outcomes.',
        'Use of Video/Animation to explain functioning of various concepts.',
        'Encourage collaborative (Group Learning) Learning in the class.',
        'Ask at least three HOT (Higher order Thinking) questions in the class, which promotes '
        'critical thinking.',
        'Adopt Problem Based Learning (PBL), which fosters student\'s Analytical skills, develop '
        'design thinking skills such as the ability to design, evaluate, generalize, and analyze '
        'information rather than simply recall it.',
        'Topics will be introduced in a multiple representation.',
    ]
    tlp_content = tlp_intro + [Paragraph(f'{i}. {t}', S['normal'])
                                for i, t in enumerate(tlp_items, 1)]

    tlp_table = _content_block(tlp_header + tlp_content, S)
    story.append(tlp_table)
    story.append(Spacer(1, 2))

    # ── 5. COURSE CONTENT (Modules) ───────────────────────────────────────────
    story.append(_build_course_content(course, S))
    story.append(Spacer(1, 2))

    # ── 6. COURSE OUTCOMES ────────────────────────────────────────────────────
    story.append(_build_course_outcomes(course, S))
    story.append(Spacer(1, 2))

    # ── 7. CO-PO-PSO MAPPING ─────────────────────────────────────────────────
    story.append(_build_copo_table(course, S))
    story.append(Spacer(1, 2))

    # ── 8. ASSESSMENT DETAILS ────────────────────────────────────────────────
    story.append(_build_assessment(course, S))
    story.append(Spacer(1, 2))

    # ── 9. LEARNING RESOURCES ─────────────────────────────────────────────────
    resources = _build_learning_resources(course, S)
    if isinstance(resources, list):
        story.extend(resources)
    else:
        story.append(resources)

    # Build
    doc.build(story)

    course.pdf_file.name = f'syllabi_pdfs/{filename}'
    course.pdf_generated_at = datetime.now()
    course.save()

    return filepath


# ── Helper: single full-width section-header row ──────────────────────────────
def _section_header_row(text, S):
    """Returns a list with one bold paragraph for the section heading."""
    return [Paragraph(f'<b>{text}</b>', S['normal'])]


# ── Helper: wrap a list of paragraphs in a full-width single-column table ─────
def _content_block(paragraphs, S, extra_style=None):
    """
    Wraps a list of Paragraph objects into a 1-column table that spans INNER_W,
    with a grid border, matching the reference layout.
    """
    rows = [[p] for p in paragraphs]
    t = Table(rows, colWidths=[INNER_W], hAlign='LEFT')
    ts = TableStyle([
        box(0.6),
        valign_top(),
        *pad(3, 3, 6, 6),
        font_size(9.5),
        # Grey background on the first row (section heading row)
        ('BACKGROUND', (0, 0), (0, 0), LGREY),
        ('LINEBELOW', (0, 0), (0, 0), 0.5, BLACK),
    ])
    if extra_style:
        for cmd in extra_style:
            ts.add(*cmd)
    t.setStyle(ts)
    return t


# ── Module content builder ────────────────────────────────────────────────────
def _build_course_content(course, S):
    """
    Builds the entire 'III. COURSE CONTENT' section as one big table whose
    structure exactly matches the reference: section-title row, then per-module
    rows alternating between [module-title | hours] and [full-width content].
    """
    # Section title row
    rows = [[Paragraph('<b>III.\u2003COURSE CONTENT</b>', S['section']), '']]
    span_cmds = [('SPAN', (0, 0), (1, 0)),
                 ('BACKGROUND', (0, 0), (1, 0), LGREY),
                 ('LINEBELOW', (0, 0), (1, 0), 0.5, BLACK),
                 ('ALIGN', (0, 0), (1, 0), 'CENTER')]
    row_idx = 1

    modules = course.modules if course.modules else _default_modules()

    for idx, mod in enumerate(modules, 1):
        title   = mod.get('module_title', mod.get('title', ''))
        hours   = mod.get('teaching_hours', mod.get('hours', 8))
        topics  = mod.get('topics', '')

        # Module header row: bold title left, "8Hrs" right
        mod_label = f'<b>Module-{idx}: {title}</b>'
        mod_row = [
            Paragraph(mod_label, S['module']),
            Paragraph(f'{hours}Hrs', S['normal']),
        ]
        rows.append(mod_row)
        span_cmds += [
            ('LINEABOVE', (0, row_idx), (1, row_idx), 0.5, BLACK),
        ]
        row_idx += 1

        # Content rows – span both columns
        content_paragraphs = _build_module_content(mod, idx, course, S)
        for para in content_paragraphs:
            rows.append([para, ''])
            span_cmds.append(('SPAN', (0, row_idx), (1, row_idx)))
            row_idx += 1

        # Self-Learning row (shaded)
        sl_text = mod.get('self_learning', _default_self_learning(idx))
        rows.append([Paragraph(f'<b>Self-Learning:</b> {sl_text}', S['normal']), ''])
        span_cmds += [
            ('SPAN', (0, row_idx), (1, row_idx)),
            ('BACKGROUND', (0, row_idx), (1, row_idx), LGREY),
            ('LINEABOVE', (0, row_idx), (1, row_idx), 0.5, BLACK),
        ]
        row_idx += 1

        # RBT Levels row (shaded)
        rows.append([Paragraph(
            '<b>RBT Levels:</b>L1 \u2013 Remembering, L2 \u2013 Understanding, L3 \u2013 Applying',
            S['normal']), ''])
        span_cmds += [
            ('SPAN', (0, row_idx), (1, row_idx)),
            ('BACKGROUND', (0, row_idx), (1, row_idx), LGREY),
            ('LINEABOVE', (0, row_idx), (1, row_idx), 0.5, BLACK),
        ]
        row_idx += 1

    col_widths = [INNER_W - 1.8*cm, 1.8*cm]
    t = Table(rows, colWidths=col_widths, hAlign='LEFT')
    ts = TableStyle([
        box(0.6),
        *pad(3, 3, 6, 6),
        valign_top(),
        font_size(9.5),
        ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
    ])
    for cmd in span_cmds:
        ts.add(*cmd)
    t.setStyle(ts)
    return t


def _build_module_content(mod, idx, course, S):
    """Returns a list of Paragraphs for the body of one module."""
    normal = S['normal']
    bold   = S['bold']
    result = []

    topics = mod.get('topics', '')
    if topics:
        result.append(Paragraph(topics, normal))

    # Hands on
    hands_on = mod.get('hands_on', [])
    if not hands_on and course.hands_on_exercises:
        try:
            ex = course.hands_on_exercises[idx - 1]
            if ex:
                hands_on = ex if isinstance(ex, list) else [ex.get('title', '')]
        except IndexError:
            pass
    if hands_on:
        result.append(Paragraph('<b>Hands on:</b>', normal))
        for i, h in enumerate(hands_on, 1):
            text = h if isinstance(h, str) else h.get('title', str(h))
            result.append(Paragraph(f'{i}. {text}', normal))

    # Textbook reference
    tb_ref = mod.get('textbook_ref', _default_textbook_ref(idx))
    result.append(Paragraph(f'<b>Textbook {_textbook_num(idx)}:</b> {tb_ref}', normal))

    return result


def _textbook_num(idx):
    # Modules 1-4 reference Textbook 1; Module 5 references Textbook 2
    return 2 if idx == 5 else 1


def _default_textbook_ref(idx):
    refs = {
        1: 'Chapter 1 and Chapter 3',
        2: 'Chapter 4 and Chapter 5',
        3: 'Chapters 6, 7 and 8',
        4: 'Chapters 9, 11 and 12',
        5: 'Chapters 1, 2 and 7',
    }
    return refs.get(idx, 'Chapter 1')


def _default_self_learning(idx):
    sl = {
        1: 'Wild Card patterns in URLS.',
        2: 'Schema Evolution',
        3: 'Other URLConfs.',
        4: 'Sitemap framework.',
        5: 'JQuery AJAX Facilities',
    }
    return sl.get(idx, '')


def _default_modules():
    return [
        {
            'module_title': 'MVC based Web Designing',
            'teaching_hours': 8,
            'topics': 'Web framework, MVC Design Pattern, Django Evolution, Views, Mapping URL to Views, Working of Django URL Confs and Loose Coupling, Errors in Django.',
            'hands_on': [
                'Develop a Django app that displays current date and time in server.',
                'Develop a Django app that displays date and time four hours ahead and four hours before as an offset of current date and time in server',
            ],
            'textbook_ref': 'Chapter 1 and Chapter 3',
            'self_learning': 'Wild Card patterns in URLS.',
        },
        {
            'module_title': 'Django Templates and Models',
            'teaching_hours': 8,
            'topics': 'Template System Basics, Using Django Template System, Basic Template Tags and Filters, MVT Development Pattern, Template Loading, Template Inheritance, MVT Development Pattern. Configuring Databases, Defining and Implementing Models, Basic Data Access, Adding Model String Representations, Inserting/Updating data, Selecting and deleting objects,',
            'hands_on': [
                'Develop a simple Django app that displays an unordered list of fruits and ordered list of selected students for an event.',
                'Develop a layout.html with a suitable header (containing navigation menu) and footer with copyright and developer information. Inherit this layout.html and create 3 additional pages: contact us, About Us and Home page of any website.',
                'Develop a Django app that performs student registration to a course. It should also display list of students registered for any selected course. Create students and course as models with enrolment as ManyToMany field',
            ],
            'textbook_ref': 'Chapter 4 and Chapter 5',
            'self_learning': 'Schema Evolution',
        },
        {
            'module_title': 'Django Admin Interfaces and Model Forms',
            'teaching_hours': 8,
            'topics': 'Activating Admin Interfaces, Using Admin Interfaces, Customizing Admin Interfaces, Reasons to use Admin Interfaces. Form Processing, Creating Feedback forms, Form submissions, custom validation, creating Model Forms, URLConf Ticks.',
            'hands_on': [
                'For student and course models created for Module2, register admin interfaces, perform migrations and illustrate data entry through admin forms.',
                'Develop a Model form for student that contains his topic chosen for project, languages used and duration with a model called project.',
            ],
            'textbook_ref': 'Chapters 6, 7 and 8',
            'self_learning': 'Other URLConfs.',
        },
        {
            'module_title': 'Generic Views and Django State Persistence',
            'teaching_hours': 8,
            'topics': 'Using Generic Views, Generic Views of Objects, Extending Generic Views of objects, Extending Generic Views.\n\nMIME Types, Generating Non-HTML contents like CSV and PDF, Syndication Feed Framework.',
            'hands_on': [
                'For students enrolment developed in Module 2, create a generic class view which displays list of students and detailview that displays student details for any selected student in the list.',
                'Develop example Django app that performs CSV and PDF generation for any models created in previous laboratory component.',
            ],
            'textbook_ref': 'Chapters 9, 11 and 12',
            'self_learning': 'Sitemap framework.',
        },
        {
            'module_title': 'jQuery and AJAX Integration in Django',
            'teaching_hours': 8,
            'topics': 'Ajax Solution, Java Script, XHTMLHttpRequest and Response, HTML, CSS, JSON, iFrames, Settings of Java Script in Django, jQuery and Basic AJAX,',
            'hands_on': [
                'Develop a registration page for student enrolment as done in Module 2 but without page refresh using AJAX.',
                'Develop a search application in Django using AJAX that displays courses enrolled by a student being searched.',
            ],
            'textbook_ref': 'Chapters 1, 2 and 7',
            'self_learning': 'JQuery AJAX Facilities',
        },
    ]


# ── Course Outcomes ────────────────────────────────────────────────────────────
def _build_course_outcomes(course, S):
    cos = course.course_outcomes if course.course_outcomes else [
        'Understand the working of MVT based full stack web development with Django.',
        'Designing of Models and Forms for rapid development of web pages.',
        'Analyze the role of Template Inheritance and Generic views for developing full stack web applications.',
        'Apply the Django framework libraries to render nonHTML contents like CSV and PDF.',
        'Perform jQuery based AJAX integration to Django Apps to build responsive full stack web applications.',
    ]

    # Header row
    rows = [[
        Paragraph('<b>IV. COURSE OUTCOMES</b>', S['section']),
        '',
    ]]
    span_cmds = [
        ('SPAN', (0, 0), (1, 0)),
        ('BACKGROUND', (0, 0), (1, 0), LGREY),
        ('ALIGN', (0, 0), (1, 0), 'CENTER'),
        ('LINEBELOW', (0, 0), (1, 0), 0.5, BLACK),
    ]
    row_idx = 1

    for i, co in enumerate(cos, 1):
        text = co.strip() if co.strip() else ''
        rows.append([
            Paragraph(f'<b>CO{i}</b>', S['co']),
            Paragraph(text, S['normal']),
        ])
        row_idx += 1

    col_widths = [1.5*cm, INNER_W - 1.5*cm]
    t = Table(rows, colWidths=col_widths, hAlign='LEFT')
    ts = TableStyle([
        box(0.6),
        grid(0.5),
        *pad(5, 5, 6, 6),
        valign_mid(),
        font_size(9.5),
    ])
    for cmd in span_cmds:
        ts.add(*cmd)
    t.setStyle(ts)
    return t


# ── CO-PO-PSO Mapping ─────────────────────────────────────────────────────────
def _build_copo_table(course, S):
    po_labels = ['PO/P\nSO', '1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '11', '12', 'S1', 'S2', 'S3']

    # Section header row
    header_row = [Paragraph('<b>V. CO-PO-PSO MAPPING</b> (mark H=3; M=2; L=1)', S['section'])]
    for _ in range(len(po_labels) - 1):
        header_row.append('')

    rows = [header_row]
    span_cmds = [
        ('SPAN', (0, 0), (len(po_labels) - 1, 0)),
        ('BACKGROUND', (0, 0), (len(po_labels) - 1, 0), LGREY),
        ('ALIGN', (0, 0), (len(po_labels) - 1, 0), 'CENTER'),
        ('LINEBELOW', (0, 0), (len(po_labels) - 1, 0), 0.5, BLACK),
    ]

    # PO header row
    po_header = [Paragraph(f'<b>{lbl}</b>', S['co']) for lbl in po_labels]
    rows.append(po_header)

    num_cos = course.num_cos if hasattr(course, 'num_cos') and course.num_cos > 0 else 5

    # Default mapping: CO1-CO5 all have M(2) in PO1,2,3,5 and PSO1
    default_mapping = {
        f'CO{i}': {'PO1': 2, 'PO2': 2, 'PO3': 2, 'PO5': 2, 'PSO1': 2}
        for i in range(1, 6)
    }
    copo = course.copo_mapping if hasattr(course, 'copo_mapping') and course.copo_mapping else default_mapping

    po_keys = ['PO1', 'PO2', 'PO3', 'PO4', 'PO5', 'PO6', 'PO7', 'PO8', 'PO9', 'PO10', 'PO11', 'PO12', 'PSO1', 'PSO2', 'PSO3']
    for i in range(1, num_cos + 1):
        co_key = f'CO{i}'
        mapping = copo.get(co_key, {})
        row = [Paragraph(f'<b>{co_key}</b>', S['co'])]
        for po in po_keys:
            val = mapping.get(po, 0)
            if val in (1, 2, 3):
                row.append(Paragraph(str(val), S['co']))
            else:
                row.append(Paragraph('', S['co']))
        rows.append(row)

    # Column widths
    first_col = 1.4 * cm
    rest_w = (INNER_W - first_col) / 15
    col_widths = [first_col] + [rest_w] * 15

    t = Table(rows, colWidths=col_widths, hAlign='LEFT')
    ts = TableStyle([
        box(0.6),
        grid(0.5),
        *pad(4, 4, 2, 2),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        valign_mid(),
        font_size(9),
    ])
    for cmd in span_cmds:
        ts.add(*cmd)
    t.setStyle(ts)
    return t


# ── Assessment Details ────────────────────────────────────────────────────────
def _build_assessment(course, S):
    rows = [
        [Paragraph('<b>VI.\u2003Assessment Details (CIE &amp; SEE)</b>', S['section'])],
        [Paragraph('<b>General Rules:</b> Refer CIE and SEE guidelines based on course type for autonomous scheme 2023 Dated on 10-02-2025.', S['normal'])],
        [Paragraph(f'<b>Continuous Internal Evaluation (CIE):</b> Refer Annexure section 1', S['normal'])],
        [Paragraph(f'<b>Semester End Examination (SEE):</b> Refer Annexure section 1', S['normal'])],
    ]
    t = Table(rows, colWidths=[INNER_W], hAlign='LEFT')
    ts = TableStyle([
        box(0.6),
        *pad(3, 3, 6, 6),
        valign_top(),
        font_size(9.5),
        ('BACKGROUND', (0, 0), (0, 0), LGREY),
        ('LINEBELOW', (0, 0), (0, 0), 0.5, BLACK),
        ('ALIGN', (0, 0), (0, 0), 'CENTER'),
    ])
    t.setStyle(ts)
    return t


# ── Learning Resources ─────────────────────────────────────────────────────────
def _build_learning_resources(course, S):
    story_parts = []

    # ── VII header ────────────────────────────────────────────────────────────
    hdr_row = [[Paragraph('<b>VII.\u2003Learning Resources</b>', S['section'])]]
    hdr_t = Table(hdr_row, colWidths=[INNER_W], hAlign='LEFT')
    hdr_t.setStyle(TableStyle([
        box(0.6),
        *pad(3, 3, 6, 6),
        ('BACKGROUND', (0, 0), (0, 0), LGREY),
        ('ALIGN', (0, 0), (0, 0), 'CENTER'),
    ]))
    story_parts.append(hdr_t)
    story_parts.append(Spacer(1, 2))

    # ── VII(a): Textbooks ─────────────────────────────────────────────────────
    story_parts.append(_build_books_table(
        label='<b>VII(a): Textbooks:</b> (Insert or delete rows as per requirement)',
        books=course.textbooks if course.textbooks else _default_textbooks(),
        S=S,
    ))
    story_parts.append(Spacer(1, 2))

    # ── VII(b): Reference Books ───────────────────────────────────────────────
    story_parts.append(_build_books_table(
        label='<b>VII(b): Reference Books:</b>',
        books=course.references if course.references else _default_references(),
        S=S,
    ))
    story_parts.append(Spacer(1, 2))

    # ── VII(c): Web links ────────────────────────────────────────────────────
    weblinks = [
        '1. MVT architecture with Django:\u2002https://freevideolectures.com/course/3700/djangotutorials',
        '2. Using Python in Django:\u2002https://www.youtube.com/watch?v=2BqoLiMT3Ao',
        '3. Model Forms with Django:\u2002https://www.youtube.com/watch?v=gMM1rtTwKxE',
        '4. Real time Interactions in Django:\u2002https://www.youtube.com/watch?v=3gHmfoeZ45k',
        '5. AJAX with Django for beginners:\u2002https://www.youtube.com/watch?v=3VaKNyjlxAU',
    ]
    wl_rows = [
        [Paragraph('<b>VII(c): Web links and Video Lectures (e-Resources):</b>', S['normal'])],
        [Paragraph('<b>WebLinks:</b>', S['normal'])],
    ] + [[Paragraph(lnk, S['normal'])] for lnk in weblinks]

    wl_t = Table(wl_rows, colWidths=[INNER_W], hAlign='LEFT')
    wl_t.setStyle(TableStyle([
        box(0.6),
        *pad(3, 3, 6, 6),
        valign_top(),
        font_size(9.5),
    ]))
    story_parts.append(wl_t)
    story_parts.append(Spacer(1, 2))

    # ── VIII: Activity Based Learning ─────────────────────────────────────────
    abl_rows = [
        [Paragraph('<b>VIII: Activity Based Learning / Practical Based Learning/Experiential learning:</b>', S['normal'])],
        [Paragraph(
            '1.\u2002Real world problem solving - applying the Django framework concepts and its integration '
            'with AJAX to develop any shopping website with admin and user dashboards.', S['normal'])],
    ]
    abl_t = Table(abl_rows, colWidths=[INNER_W], hAlign='LEFT')
    abl_t.setStyle(TableStyle([
        box(0.6),
        *pad(3, 3, 6, 6),
        valign_top(),
        font_size(9.5),
    ]))
    story_parts.append(abl_t)

    return story_parts


def _build_books_table(label, books, S):
    """Shared builder for Textbooks and Reference Books tables."""
    col_widths = [1.1*cm, 4.8*cm, 4.0*cm, 3.2*cm, INNER_W - 1.1*cm - 4.8*cm - 4.0*cm - 3.2*cm]

    rows = [
        # Label row spanning all columns
        [Paragraph(label, S['normal']), '', '', '', ''],
        # Header row
        [
            Paragraph('<b>Sl.\nNo.</b>', S['co']),
            Paragraph('<b>Title of the Book</b>', S['co']),
            Paragraph('<b>Name of the author</b>', S['co']),
            Paragraph('<b>Edition and Year</b>', S['co']),
            Paragraph('<b>Name of the\npublisher</b>', S['co']),
        ],
    ]
    span_cmds = [
        ('SPAN', (0, 0), (4, 0)),
        ('LINEBELOW', (0, 0), (4, 0), 0.5, BLACK),
        ('BACKGROUND', (0, 1), (4, 1), LGREY),
    ]

    for i, book in enumerate(books, 1):
        title     = book.get('title', '')
        author    = book.get('author', '')
        edition   = book.get('edition', 'First')
        year      = book.get('year', '2020')
        publisher = book.get('publisher', '')
        rows.append([
            Paragraph(str(i), S['co']),
            Paragraph(title, S['normal']),
            Paragraph(author, S['normal']),
            Paragraph(f'{edition} Edition, {year}' if edition else str(year), S['normal']),
            Paragraph(publisher, S['normal']),
        ])

    t = Table(rows, colWidths=col_widths, hAlign='LEFT')
    ts = TableStyle([
        box(0.6),
        grid(0.5),
        *pad(4, 4, 4, 4),
        valign_top(),
        font_size(9),
        ('ALIGN', (0, 0), (0, -1), 'CENTER'),
    ])
    for cmd in span_cmds:
        ts.add(*cmd)
    t.setStyle(ts)
    return t


def _default_textbooks():
    return [
        {
            'title': 'The Definitive Guide to Django: Web Development Done Right',
            'author': 'Adrian Holovaty, Jacob Kaplan Moss',
            'edition': 'Second',
            'year': '2009',
            'publisher': 'Springer-Verlag Berlin and Heidelberg GmbH & Co. KG Publishers',
        },
        {
            'title': 'Django Java Script Integration: AJAX and jQuery',
            'author': 'Jonathan Hayward',
            'edition': 'First',
            'year': '2011',
            'publisher': 'Pack Publishing',
        },
    ]


def _default_references():
    return [
        {'title': 'Django 3 Web Development Cookbook', 'author': 'Aidas Bendroraitis, Jake Kronika', 'edition': 'Fourth', 'year': '2020', 'publisher': 'Packt Publishing'},
        {'title': 'Django for Beginners: Build websites with Python and Django', 'author': 'William Vincent', 'edition': 'First', 'year': '2018', 'publisher': 'Amazon Digital Services'},
        {'title': 'Django3 by Example', 'author': 'Antonio Mele', 'edition': '3rd', 'year': '2020', 'publisher': 'Pack Publishers'},
        {'title': 'Django Design Patterns and Best Practices', 'author': 'Arun Ravindran', 'edition': '2nd', 'year': '2020', 'publisher': 'Pack Publishers'},
    ]