from django.db import models
from django.contrib.auth.models import AbstractUser
from django.db.models.signals import post_save
from django.dispatch import receiver

class User(AbstractUser):
    ROLE_CHOICES = [
        ('faculty', '👨‍🏫 Faculty'),
        ('admin_bos', '🛡️ Admin/BOS'),
        ('hod', '👔 Head of Department'),
    ]
    
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='faculty')
    employee_id = models.CharField(max_length=20, unique=True)
    department = models.CharField(max_length=100)
    phone = models.CharField(max_length=15, blank=True)
    
    def __str__(self):
        return f"{self.get_full_name() or self.username} ({self.get_role_display()})"
    
    @property
    def is_faculty(self):
        return self.role == 'faculty'
    
    @property
    def is_admin_bos(self):
        return self.role == 'admin_bos'
    
    @property
    def is_hod(self):
        return self.role == 'hod'

class ApprovalHistory(models.Model):
    ACTION_CHOICES = [
        ('CREATE', 'Course Created'),
        ('EDIT', 'Course Edited'),
        ('SUBMIT_BOS', 'Submitted to BOS'),
        ('BOS_APPROVE', 'BOS Approved'),
        ('BOS_REJECT', 'BOS Rejected'),
        ('SUBMIT_HOD', 'Submitted to HOD'),
        ('HOD_APPROVE', 'HOD Approved'),
        ('HOD_REJECT', 'HOD Rejected'),
        ('PDF_GENERATE', 'PDF Generated'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    course_code = models.CharField(max_length=20)
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    comments = models.TextField(blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-timestamp']
    
    def __str__(self):
        return f"{self.course_code} - {self.action} by {self.user.username}"