from django.contrib import admin

# Register your models here.
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, ApprovalHistory

class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'first_name', 'last_name', 'role', 'employee_id', 'department')
    list_filter = ('role', 'department')
    fieldsets = UserAdmin.fieldsets + (
        ('Additional Info', {'fields': ('role', 'employee_id', 'department', 'phone')}),
    )

admin.site.register(User, CustomUserAdmin)
admin.site.register(ApprovalHistory)