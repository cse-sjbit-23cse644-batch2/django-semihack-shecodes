from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.contrib.auth import get_user_model

User = get_user_model()

class Course(models.Model):
    STATUS_CHOICES = [
        ('draft', '📝 Draft'),
        ('pending_bos', '⏳ Pending BOS Approval'),
        ('pending_hod', '⏳ Pending HOD Approval'),
        ('approved', '✅ Approved'),
        ('rejected', '❌ Rejected'),
        ('revision', '🔄 Revision Required'),
    ]
    
    # Basic Information
    course_code = models.CharField(max_length=20, unique=True)
    course_title = models.CharField(max_length=200)
    department = models.CharField(max_length=100)
    semester = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(8)])
    credits = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(6)])
    
    # Teaching Hours
    lecture_hours = models.IntegerField(default=3)
    tutorial_hours = models.IntegerField(default=0)
    practical_hours = models.IntegerField(default=0)
    self_learning_hours = models.IntegerField(default=1)
    total_hours = models.IntegerField(default=40)
    
    # Assessment
    cie_marks = models.IntegerField(default=50)
    see_marks = models.IntegerField(default=50)
    exam_duration = models.IntegerField(default=3)
    
    # Course Content
    prerequisites = models.TextField(blank=True)
    course_objectives = models.TextField()
    course_outcomes = models.JSONField(default=list)
    modules = models.JSONField(default=list)
    hands_on_exercises = models.JSONField(default=list)
    self_learning_topics = models.JSONField(default=list)
    rbt_levels = models.JSONField(default=dict)
    textbooks = models.JSONField(default=list)
    references = models.JSONField(default=list)
    
    # CO-PO Mapping
    num_cos = models.IntegerField(default=5)
    copo_mapping = models.JSONField(default=dict)
    
    # Teaching Methods
    teaching_methods = models.JSONField(default=list)
    
    # Status & Approval
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_courses')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # BOS Approval
    bos_approved = models.BooleanField(default=False)
    bos_approved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='bos_approved_courses')
    bos_approved_at = models.DateTimeField(null=True, blank=True)
    bos_comments = models.TextField(blank=True)
    
    # HOD Approval
    hod_approved = models.BooleanField(default=False)
    hod_approved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='hod_approved_courses')
    hod_approved_at = models.DateTimeField(null=True, blank=True)
    hod_comments = models.TextField(blank=True)
    
    # PDF Export
    pdf_file = models.FileField(upload_to='syllabi_pdfs/', null=True, blank=True)
    pdf_generated_at = models.DateTimeField(null=True, blank=True)
    
    def __str__(self):
        return f"{self.course_code}: {self.course_title}"

class ApprovalLog(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='logs')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    action = models.CharField(max_length=50)
    details = models.TextField(blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-timestamp']
    def __str__(self):
        return f"{self.course.course_code} - {self.action}"  