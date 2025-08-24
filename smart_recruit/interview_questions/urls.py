from django.urls import path
from .views import (
    post_interview_experience,
    get_all_experiences,
    get_job_experiences,
    get_experience_detail,
    update_experience,
    delete_experience
)

urlpatterns = [
    path('experience/', post_interview_experience, name='post_experience'),
    path('experience/all/', get_all_experiences, name='all_experiences'),
    path('experience/job/<int:job_id>/', get_job_experiences, name='job_experiences'),
    
    
    path('experience/<int:pk>/', get_experience_detail, name='experience-detail'),
    path('experience/<int:pk>/update/', update_experience, name='experience-update'),
    path('experience/<int:pk>/delete/', delete_experience, name='experience-delete'),
]
