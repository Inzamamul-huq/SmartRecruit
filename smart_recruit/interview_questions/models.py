from django.db import models
from accounts.models import Student  

def interview_upload_path(instance, filename):
    return f'interview_experiences/{instance.student.email}/{filename}'

class InterviewExperience(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    student_email = models.EmailField(default='unknown@example.com')  
    job = models.ForeignKey('accounts.Job', on_delete=models.CASCADE, null=True, blank=True)
    company_name = models.CharField(max_length=200)
    division_name = models.CharField(max_length=200)
    
    
    aptitude_conducted = models.BooleanField(default=False)
    aptitude_questions = models.TextField(blank=True, null=True)
    aptitude_attachment = models.FileField(upload_to=interview_upload_path, blank=True, null=True)
    aptitude_attachment_url = models.URLField(blank=True, null=True)
    
    technical_conducted = models.BooleanField(default=False)
    technical_questions = models.TextField(blank=True, null=True)
    technical_attachment = models.FileField(upload_to=interview_upload_path, blank=True, null=True)
    technical_attachment_url = models.URLField(blank=True, null=True)
    
    gd_conducted = models.BooleanField(default=False, verbose_name='Group Discussion Conducted')
    gd_topics = models.TextField(blank=True, null=True, verbose_name='Group Discussion Topics')
    gd_attachment = models.FileField(upload_to=interview_upload_path, blank=True, null=True)
    gd_attachment_url = models.URLField(blank=True, null=True)
    
    hr_conducted = models.BooleanField(default=False)
    hr_questions = models.TextField(blank=True, null=True)
    hr_attachment = models.FileField(upload_to=interview_upload_path, blank=True, null=True)
    hr_attachment_url = models.URLField(blank=True, null=True)
    
    tips = models.TextField(blank=True, null=True, help_text='Any tips or advice for future candidates')
    overall_experience = models.TextField(blank=True, null=True)
    
    submitted_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.company_name} - {self.division_name} by {self.student.name}"
