from django.urls import path
from . import views
from . import conducttest
from . import cruds

urlpatterns = [
    
    path('student/signup/', views.student_signup),
    path('viewuser/', views.student_view),
    path('student/send-otp/', views.send_otp),
    path('student/verify-otp/', views.verify_otp),
    path('student/reset-password/', views.reset_password),
    path('student/upload-resume/<int:student_id>/', views.upload_resume),
    path('jobs/<int:job_id>/apply/', views.apply_for_job, name='apply-job'),
    
    path('viewuser/admin/', views.view_studentadmin, name='view-student-admin'),
    path('student/view/<int:student_id>/', views.view_single_student),
    path('student/by-email/', views.get_student_by_email, name='student-by-email'),
    path('student/applications/<str:email>/', views.get_student_applications, name='student-applications'),
    path('student/profile/', views.student_profile, name='student-profile'),
    path('student/change-password/', views.student_change_password, name='student-change-password'),


    #admin related URLs
    path('admin/signup/', views.admin_signup, name='admin_signup'),
    path('admin/toggle-approval/<int:user_id>/', views.toggle_user_approval, name='toggle-user-approval'),
    path('admin/post-job/', views.post_job),
    path('jobs/', views.job_list),
    path('admin/change-password/', views.admin_change_password, name='admin-change-password'),
    path('admin/viewjobapplicants/<int:job_id>/', views.job_applicants, name='view-job-applicants'),
    path('jobs/<int:job_id>/', views.job_detail, name='job-detail'),
    path('student/update-selection/<int:student_id>/', views.update_selection_status, name='update-selection'),
   
   #create question
    path('createquestion/',conducttest.create_mcq_question),

#get question
    path('getquestions/job/<int:job_id>/', conducttest.get_test_questions, name='get-questions-by-job'),
    path('getquestions/', conducttest.get_test_questions, name='get-all-questions'),
    path('getquestions/schedule/<int:test_schedule_id>/', conducttest.get_test_questions, name='get-questions-by-schedule'),
    path('submitanswers/<int:test_schedule_id>/', conducttest.submit_test_answers, name='submit-test-answers'),
   
    path('admin/schedule-test/', views.schedule_test),
    path('test-schedule/<int:schedule_id>/', views.get_test_schedule, name='test-schedule-detail'),
    path('student/result/<int:student_id>/', views.view_result),
    path('student/active-tests/<str:student_email>/', views.get_active_test_schedule, name='student-active-tests'),
    path('test/results/<int:test_schedule_id>/', views.get_test_results, name='test-results'),
   
   #send and get job opportunities
   
    path('job-opportunities/', conducttest.send_job_opportunities, name='send-job-opportunities'),
    path('job-opportunities/student/', conducttest.get_opportunities_by_student, name='get-opportunities-by-student'),
    
    # Job CRUD operations
    path('jobs/crud/<int:job_id>/', cruds.job_operations, name='job-operations'),
    path('jobs/<int:job_id>/details/', conducttest.get_job_details, name='get_job_details'),
    path('jobs/<int:job_id>/opportunities/', conducttest.get_job_opportunities, name='get_job_opportunities'),
    
    # Question CRUD Operations
    path('crud/questions/<int:question_id>/', cruds.question_operations, name='question-crud'),
]

