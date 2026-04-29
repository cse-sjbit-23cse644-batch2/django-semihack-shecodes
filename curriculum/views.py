from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.http import JsonResponse, FileResponse
from django.utils import timezone
from django.core.paginator import Paginator
from django.views.decorators.csrf import csrf_exempt
from .models import Course, ApprovalLog
from .forms import CourseBasicForm
from .utils import generate_syllabus_pdf
import json
import os

# ==================== DECORATORS ====================

def faculty_required(view_func):
    return login_required(user_passes_test(lambda u: u.role == 'faculty')(view_func))

def admin_bos_required(view_func):
    return login_required(user_passes_test(lambda u: u.role == 'admin_bos')(view_func))

def hod_required(view_func):
    return login_required(user_passes_test(lambda u: u.role == 'hod')(view_func))

# ==================== API VIEWS ====================

@login_required
def get_course_api(request, course_id):
    course = get_object_or_404(Course, id=course_id)
    return JsonResponse({
        'id': course.id,
        'course_code': course.course_code,
        'course_title': course.course_title,
        'semester': course.semester,
        'credits': course.credits,
        'department': course.department,
        'lecture_hours': course.lecture_hours,
        'tutorial_hours': course.tutorial_hours,
        'practical_hours': course.practical_hours,
        'total_hours': course.total_hours,
        'cie_marks': course.cie_marks,
        'see_marks': course.see_marks,
        'exam_duration': course.exam_duration,
        'prerequisites': course.prerequisites,
        'course_objectives': course.course_objectives,
        'modules': course.modules,
        'num_cos': course.num_cos,
        'course_outcomes': course.course_outcomes,
        'copo_mapping': course.copo_mapping,
        'status': course.status,
        'status_display': course.get_status_display(),
        'created_at': course.created_at.strftime('%Y-%m-%d %H:%M'),
    })

@login_required
def get_course_full_api(request, course_id):
    course = get_object_or_404(Course, id=course_id)
    return JsonResponse({
        'course_code': course.course_code,
        'course_title': course.course_title,
        'department': course.department,
        'semester': course.semester,
        'credits': course.credits,
        'course_objectives': course.course_objectives,
        'modules': course.modules,
        'copo_mapping': course.copo_mapping,
        'faculty_name': course.created_by.get_full_name(),
        'employee_id': course.created_by.employee_id,
        'created_at': course.created_at.strftime('%Y-%m-%d %H:%M'),
    })

@csrf_exempt
@login_required
def save_course_basic_api(request, course_id):
    if request.method == 'POST':
        course = get_object_or_404(Course, id=course_id)
        data = json.loads(request.body) if request.body else request.POST
        course.course_title = data.get('course_title', course.course_title)
        course.semester = int(data.get('semester', course.semester))
        course.credits = int(data.get('credits', course.credits))
        course.department = data.get('department', course.department)
        course.lecture_hours = int(data.get('lecture_hours', course.lecture_hours))
        course.tutorial_hours = int(data.get('tutorial_hours', course.tutorial_hours))
        course.practical_hours = int(data.get('practical_hours', course.practical_hours))
        course.total_hours = int(data.get('total_hours', course.total_hours))
        course.save()
        return JsonResponse({'status': 'success'})
    return JsonResponse({'status': 'error'}, status=400)

@csrf_exempt
@login_required
def save_course_objectives_api(request, course_id):
    if request.method == 'POST':
        course = get_object_or_404(Course, id=course_id)
        data = json.loads(request.body) if request.body else request.POST
        course.course_objectives = data.get('objectives', '')
        course.save()
        return JsonResponse({'status': 'success'})
    return JsonResponse({'status': 'error'}, status=400)

@csrf_exempt
@login_required
def save_course_modules_api(request, course_id):
    if request.method == 'POST':
        course = get_object_or_404(Course, id=course_id)
        data = json.loads(request.body) if request.body else request.POST
        modules = json.loads(data.get('modules', '[]'))
        course.modules = modules
        course.save()
        return JsonResponse({'status': 'success'})
    return JsonResponse({'status': 'error'}, status=400)

@csrf_exempt
@login_required
def save_course_copo_api(request, course_id):
    if request.method == 'POST':
        course = get_object_or_404(Course, id=course_id)
        data = json.loads(request.body) if request.body else request.POST
        course.num_cos = int(data.get('num_cos', course.num_cos))
        course_outcomes = data.get('course_outcomes', '')
        course.course_outcomes = [co.strip() for co in course_outcomes.split('\n') if co.strip()]
        copo_mapping_str = data.get('copo_mapping', '{}')
        if isinstance(copo_mapping_str, str):
            course.copo_mapping = json.loads(copo_mapping_str)
        else:
            course.copo_mapping = copo_mapping_str
        course.save()
        return JsonResponse({'status': 'success'})
    return JsonResponse({'status': 'error'}, status=400)

@login_required
def get_course_status_api(request, course_id):
    course = get_object_or_404(Course, id=course_id)
    logs = ApprovalLog.objects.filter(course=course).values('action', 'details', 'timestamp', 'user__username')
    logs_list = [{'action': l['action'], 'details': l['details'], 'timestamp': l['timestamp'].strftime('%Y-%m-%d %H:%M:%S'), 'user': l['user__username']} for l in logs]
    return JsonResponse({'logs': logs_list, 'status': course.status})

# ==================== FACULTY VIEWS ====================

@faculty_required
def faculty_dashboard_combined(request):
    courses = Course.objects.filter(created_by=request.user).order_by('-created_at')
    stats = {
        'total': courses.count(),
        'draft': courses.filter(status='draft').count(),
        'pending_bos': courses.filter(status='pending_bos').count(),
        'pending_hod': courses.filter(status='pending_hod').count(),
        'approved': courses.filter(status='approved').count(),
        'revision': courses.filter(status='revision').count(),
    }
    return render(request, 'curriculum/faculty/dashboard_combined.html', {'courses': courses, 'stats': stats})

@faculty_required
def faculty_dashboard_separate(request):
    courses = Course.objects.filter(created_by=request.user).order_by('-created_at')
    stats = {
        'total': courses.count(),
        'draft': courses.filter(status='draft').count(),
        'pending_bos': courses.filter(status='pending_bos').count(),
        'pending_hod': courses.filter(status='pending_hod').count(),
        'approved': courses.filter(status='approved').count(),
    }
    return render(request, 'curriculum/faculty/dashboard.html', {'courses': courses, 'stats': stats})

@faculty_required
def create_course_separate(request):
    if request.method == 'POST':
        form = CourseBasicForm(request.POST)
        if form.is_valid():
            course = form.save(commit=False)
            course.created_by = request.user
            course.status = 'draft'
            course.save()
            ApprovalLog.objects.create(course=course, user=request.user, action='CREATE', details=f'Course {course.course_code} created')
            messages.success(request, f'Course {course.course_code} created!')
            return redirect('edit_course_separate', course_id=course.id)
    else:
        form = CourseBasicForm()
    return render(request, 'curriculum/faculty/create_course.html', {'form': form})

@faculty_required
def edit_course_separate(request, course_id):
    course = get_object_or_404(Course, id=course_id)
    
    if course.status not in ['draft', 'revision']:
        messages.error(request, f'Cannot edit. Current status: {course.get_status_display()}')
        return redirect('faculty_dashboard_separate')
    
    step = int(request.GET.get('step', 1))
    
    if request.method == 'POST':
        if step == 1:
            form = CourseBasicForm(request.POST, instance=course)
            if form.is_valid():
                form.save()
                messages.success(request, 'Basic information saved!')
                return redirect(f'/curriculum/faculty/separate/edit/{course_id}/?step=2')
        elif step == 2:
            course.course_objectives = request.POST.get('course_objectives', '')
            course.save()
            messages.success(request, 'Course objectives saved!')
            return redirect(f'/curriculum/faculty/separate/edit/{course_id}/?step=3')
        elif step == 3:
            modules = []
            module_count = int(request.POST.get('module_count', 0))
            for i in range(1, module_count + 1):
                if request.POST.get(f'module_{i}_title'):
                    modules.append({
                        'module_number': i,
                        'module_title': request.POST.get(f'module_{i}_title', ''),
                        'topics': request.POST.get(f'module_{i}_topics', ''),
                        'teaching_hours': int(request.POST.get(f'module_{i}_hours', 0)),
                    })
            course.modules = modules
            course.save()
            messages.success(request, 'Modules saved!')
            return redirect(f'/curriculum/faculty/separate/edit/{course_id}/?step=4')
        elif step == 4:
            course.num_cos = int(request.POST.get('num_cos', 5))
            co_text = request.POST.get('course_outcomes', '')
            course.course_outcomes = [co.strip() for co in co_text.split('\n') if co.strip()]
            course.save()
            messages.success(request, 'CO-PO Mapping saved! Course is ready for submission.')
            return redirect('faculty_dashboard_separate')
    else:
        form = CourseBasicForm(instance=course)
    
    po_list = [f'PO{i}' for i in range(1, 13)]
    return render(request, 'curriculum/faculty/edit_course.html', {'course': course, 'step': step, 'form': form, 'po_list': po_list})

@faculty_required
def course_list_separate(request):
    courses = Course.objects.filter(created_by=request.user).order_by('-created_at')
    paginator = Paginator(courses, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return render(request, 'curriculum/faculty/course_list.html', {'courses': page_obj})

@faculty_required
def submit_approval_separate(request, course_id):
    course = get_object_or_404(Course, id=course_id)
    
    if course.status != 'draft':
        messages.error(request, f'Cannot submit. Current status: {course.get_status_display()}')
        return redirect('faculty_dashboard_separate')
    
    if request.method == 'POST':
        course.status = 'pending_bos'
        course.save()
        ApprovalLog.objects.create(course=course, user=request.user, action='SUBMIT_BOS', details=request.POST.get('comments', ''))
        messages.success(request, f'Course {course.course_code} submitted to BOS for approval')
        return redirect('faculty_dashboard_separate')
    
    return render(request, 'curriculum/faculty/submit_approval.html', {'course': course})

# ==================== ADMIN/BOS VIEWS ====================

@admin_bos_required
def admin_bos_dashboard_combined(request):
    pending_courses = Course.objects.filter(status='pending_bos').order_by('-created_at')
    stats = {
        'pending': pending_courses.count(),
        'approved': Course.objects.filter(bos_approved=True).count(),
        'total_reviewed': Course.objects.exclude(status__in=['draft', 'pending_bos']).count(),
    }
    return render(request, 'curriculum/admin_bos/dashboard_combined.html', {'pending_courses': pending_courses, 'stats': stats})

@admin_bos_required
def admin_bos_dashboard_separate(request):
    pending_courses = Course.objects.filter(status='pending_bos').order_by('-created_at')
    return render(request, 'curriculum/admin_bos/dashboard.html', {'pending_courses': pending_courses})

@admin_bos_required
def review_course_separate(request, course_id):
    course = get_object_or_404(Course, id=course_id, status='pending_bos')
    
    if request.method == 'POST':
        action = request.POST.get('action')
        comments = request.POST.get('comments', '')
        
        if action == 'approve':
            course.status = 'pending_hod'
            course.bos_approved = True
            course.bos_approved_by = request.user
            course.bos_approved_at = timezone.now()
            course.bos_comments = comments
            course.save()
            ApprovalLog.objects.create(course=course, user=request.user, action='BOS_APPROVE', details=comments)
            messages.success(request, f'Course {course.course_code} approved and sent to HOD')
        else:
            course.status = 'revision'
            course.bos_comments = comments
            course.bos_approved_by = request.user
            course.bos_approved_at = timezone.now()
            course.save()
            ApprovalLog.objects.create(course=course, user=request.user, action='BOS_REJECT', details=comments)
            messages.warning(request, f'Course {course.course_code} sent back for revision')
        
        return redirect('admin_bos_dashboard_separate')
    
    return render(request, 'curriculum/admin_bos/review_course.html', {'course': course})

@admin_bos_required
def audit_log_separate(request):
    logs = ApprovalLog.objects.all().order_by('-timestamp')
    paginator = Paginator(logs, 50)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return render(request, 'curriculum/admin_bos/audit_log.html', {'logs': page_obj})

# ==================== HOD VIEWS ====================

@hod_required
def hod_dashboard_combined(request):
    pending_courses = Course.objects.filter(status='pending_hod').order_by('-created_at')
    approved_courses = Course.objects.filter(status='approved').order_by('-hod_approved_at')[:10]
    stats = {
        'pending': pending_courses.count(),
        'approved': Course.objects.filter(status='approved').count(),
        'total': Course.objects.exclude(status='draft').count(),
    }
    return render(request, 'curriculum/hod/dashboard_combined.html', {
        'pending_courses': pending_courses,
        'approved_courses': approved_courses,
        'stats': stats,
    })

@hod_required
def hod_dashboard_separate(request):
    pending_courses = Course.objects.filter(status='pending_hod').order_by('-created_at')
    return render(request, 'curriculum/hod/dashboard.html', {'pending_courses': pending_courses})

@hod_required
def final_review_separate(request, course_id):
    course = get_object_or_404(Course, id=course_id, status='pending_hod')
    
    if request.method == 'POST':
        action = request.POST.get('action')
        comments = request.POST.get('comments', '')
        
        if action == 'approve':
            course.status = 'approved'
            course.hod_approved = True
            course.hod_approved_by = request.user
            course.hod_approved_at = timezone.now()
            course.hod_comments = comments
            course.save()
            
            try:
                generate_syllabus_pdf(course, request.user)
                ApprovalLog.objects.create(course=course, user=request.user, action='HOD_APPROVE', details=f'Final approved. PDF generated.')
                messages.success(request, f'Course {course.course_code} approved and PDF generated!')
            except Exception as e:
                messages.error(request, f'Approved but PDF generation failed: {str(e)}')
        else:
            course.status = 'revision'
            course.hod_comments = comments
            course.save()
            ApprovalLog.objects.create(course=course, user=request.user, action='HOD_REJECT', details=comments)
            messages.warning(request, f'Course {course.course_code} sent back for revision')
        
        return redirect('hod_dashboard_separate')
    
    return render(request, 'curriculum/hod/final_review.html', {'course': course})

@hod_required
def published_syllabi_separate(request):
    courses = Course.objects.filter(status='approved').order_by('-hod_approved_at')
    paginator = Paginator(courses, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return render(request, 'curriculum/hod/published_syllabi.html', {'courses': page_obj})

# ==================== DOWNLOAD PDF - FACULTY CAN DOWNLOAD ====================

@login_required
def download_pdf(request, course_id):
    """Download PDF - Faculty can download their OWN approved courses"""
    course = get_object_or_404(Course, id=course_id)
    
    # Check permissions
    if request.user.role == 'faculty':
        # Faculty can only download their own approved courses
        if course.created_by.id != request.user.id:
            messages.error(request, 'You can only download your own syllabi')
            return redirect('faculty_dashboard_combined')
        if course.status != 'approved':
            messages.error(request, f'This syllabus is not yet approved. Current status: {course.get_status_display()}')
            return redirect('faculty_dashboard_combined')
    elif request.user.role not in ['admin_bos', 'hod']:
        messages.error(request, 'You do not have permission to download')
        return redirect('login')
    
    # Generate PDF if it doesn't exist
    try:
        if not course.pdf_file or not os.path.exists(course.pdf_file.path):
            generate_syllabus_pdf(course, request.user)
            course.refresh_from_db()
        
        if course.pdf_file and os.path.exists(course.pdf_file.path):
            return FileResponse(
                open(course.pdf_file.path, 'rb'),
                as_attachment=True,
                filename=f"{course.course_code}_Syllabus.pdf"
            )
        else:
            messages.error(request, 'PDF file could not be generated')
            return redirect(request.META.get('HTTP_REFERER', '/'))
    except Exception as e:
        messages.error(request, f'Error generating PDF: {str(e)}')
        return redirect(request.META.get('HTTP_REFERER', '/'))