from django.urls import path
from . import views

urlpatterns = [
    # Faculty URLs
    path('faculty/', views.faculty_dashboard_combined, name='faculty_dashboard_combined'),
    path('faculty/separate/dashboard/', views.faculty_dashboard_separate, name='faculty_dashboard_separate'),
    path('faculty/separate/create/', views.create_course_separate, name='create_course_separate'),
    path('faculty/separate/edit/<int:course_id>/', views.edit_course_separate, name='edit_course_separate'),
    path('faculty/separate/list/', views.course_list_separate, name='course_list_separate'),
    path('faculty/separate/submit/<int:course_id>/', views.submit_approval_separate, name='submit_approval_separate'),
    
    # Admin/BOS URLs
    path('admin-bos/', views.admin_bos_dashboard_combined, name='admin_bos_dashboard_combined'),
    path('admin-bos/separate/dashboard/', views.admin_bos_dashboard_separate, name='admin_bos_dashboard_separate'),
    path('admin-bos/separate/review/<int:course_id>/', views.review_course_separate, name='review_course_separate'),
    path('admin-bos/separate/audit/', views.audit_log_separate, name='audit_log_separate'),
    
    # HOD URLs
    path('hod/', views.hod_dashboard_combined, name='hod_dashboard_combined'),
    path('hod/separate/dashboard/', views.hod_dashboard_separate, name='hod_dashboard_separate'),
    path('hod/separate/review/<int:course_id>/', views.final_review_separate, name='final_review_separate'),
    path('hod/separate/published/', views.published_syllabi_separate, name='published_syllabi_separate'),
    
    # Common
    path('download/<int:course_id>/', views.download_pdf, name='download_pdf'),
    
    # API URLs (for AJAX calls)
    path('api/course/<int:course_id>/', views.get_course_api, name='get_course_api'),
    path('api/course/<int:course_id>/full/', views.get_course_full_api, name='get_course_full_api'),
    path('api/course/<int:course_id>/basic/', views.save_course_basic_api, name='save_course_basic_api'),
    path('api/course/<int:course_id>/objectives/', views.save_course_objectives_api, name='save_course_objectives_api'),
    path('api/course/<int:course_id>/modules/', views.save_course_modules_api, name='save_course_modules_api'),
    path('api/course/<int:course_id>/copo/', views.save_course_copo_api, name='save_course_copo_api'),
    path('api/course/<int:course_id>/status/', views.get_course_status_api, name='get_course_status_api'),
]