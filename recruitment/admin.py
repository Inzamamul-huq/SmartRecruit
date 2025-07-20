from django.contrib import admin
from .models import Job, JobApplication, Question, TestSchedule

admin.site.register(Job)
admin.site.register(JobApplication)
admin.site.register(Question)
admin.site.register(TestSchedule)
