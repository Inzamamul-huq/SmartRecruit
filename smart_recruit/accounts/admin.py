from django.contrib import admin
from . models import Student, AdminUser, OTP, Job, TestSchedule, MCQQuestion, TestResponse
# Register your models here.

admin.site.register(Student)
admin.site.register(AdminUser)
admin.site.register(OTP)
admin.site.register(Job)
admin.site.register(TestSchedule)
admin.site.register(MCQQuestion)
admin.site.register(TestResponse)
