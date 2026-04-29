from django import forms
from .models import Course

class CourseBasicForm(forms.ModelForm):
    class Meta:
        model = Course
        fields = ['course_code', 'course_title', 'department', 'semester', 'credits',
                  'lecture_hours', 'tutorial_hours', 'practical_hours', 'self_learning_hours',
                  'total_hours', 'cie_marks', 'see_marks', 'exam_duration', 'prerequisites']
        widgets = {
            'course_code': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., CS501'}),
            'course_title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., Advanced Databases'}),
            'department': forms.TextInput(attrs={'class': 'form-control'}),
            'semester': forms.NumberInput(attrs={'class': 'form-control', 'min': 1, 'max': 8}),
            'credits': forms.NumberInput(attrs={'class': 'form-control', 'min': 1, 'max': 6}),
            'lecture_hours': forms.NumberInput(attrs={'class': 'form-control'}),
            'tutorial_hours': forms.NumberInput(attrs={'class': 'form-control'}),
            'practical_hours': forms.NumberInput(attrs={'class': 'form-control'}),
            'self_learning_hours': forms.NumberInput(attrs={'class': 'form-control'}),
            'total_hours': forms.NumberInput(attrs={'class': 'form-control'}),
            'cie_marks': forms.NumberInput(attrs={'class': 'form-control'}),
            'see_marks': forms.NumberInput(attrs={'class': 'form-control'}),
            'exam_duration': forms.NumberInput(attrs={'class': 'form-control'}),
            'prerequisites': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }