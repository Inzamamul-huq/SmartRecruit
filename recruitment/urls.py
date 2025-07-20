from django.urls import path
from . import views

urlpatterns = [
    path('job/create/', views.create_job),
    path('job/list/', views.list_jobs),
    path('job/apply/', views.apply_job),
    path('job/shortlist/', views.shortlist_candidate),
    path('job/question/add/', views.add_question),
    path('job/schedule/', views.schedule_test),
]
