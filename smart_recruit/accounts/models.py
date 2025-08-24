from datetime import timezone
from django.db import models
from .validators import email_validator, phone_validator


class Student(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField(unique=True, validators=[email_validator])
    phone = models.CharField(max_length=15, validators=[phone_validator])
    password = models.CharField(max_length=100)
    resume = models.FileField(upload_to='resumes/', null=True, blank=True)
    is_selected = models.BooleanField(null=True)
    allow = models.TextField(null=True)

class AdminUser(models.Model):
    email = models.EmailField(unique=True, validators=[email_validator])
    password = models.CharField(max_length=100)

class OTP(models.Model):
    email = models.EmailField(validators=[email_validator])
    otp = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)

class Job(models.Model):
    title = models.CharField(max_length=100)
    description = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

class JobOpportunity(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField()
    job_date = models.DateField()
    created_by = models.ForeignKey('auth.User', on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    job = models.ForeignKey('Job', on_delete=models.CASCADE, related_name='opportunities')
    student_email = models.EmailField()
    message_sent = models.BooleanField(default=False)
    sent_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ('job', 'student_email')
        verbose_name_plural = 'Job Opportunities'

    def __str__(self):
        return f"{self.title} - {self.student_email} - {self.job_date}"
        
    def save(self, *args, **kwargs):
        
        if self.message_sent and not self.sent_at:
            self.sent_at = timezone.now()
        super().save(*args, **kwargs)


class JobApplication(models.Model):
    STATUS_CHOICES = [
        ('applied', 'Applied'),
        ('under_review', 'Under Review'),
        ('test_scheduled', 'Test Scheduled'),
        ('test_completed', 'Test Completed'),
        ('selected', 'Selected'),
        ('rejected', 'Rejected'),
    ]
    
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    job = models.ForeignKey(Job, on_delete=models.CASCADE)
    resume = models.FileField(upload_to='job_applications/resumes/')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='applied')
    applied_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ('student', 'job')
        ordering = ['-applied_at']
        
    def __str__(self):
        return f"{self.student.name} - {self.job.title}"


class TestSchedule(models.Model):
    application = models.OneToOneField(
        JobApplication, 
        on_delete=models.CASCADE,
        related_name='test_schedule'
    )
    test_time = models.DateTimeField()
    duration_minutes = models.PositiveIntegerField(default=60, help_text='Duration of the test in minutes')
    message = models.TextField(blank=True, null=True)
    is_completed = models.BooleanField(default=False)
    score = models.IntegerField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['test_time']
        
    def __str__(self):
        return f"Test for {self.application} at {self.test_time}"


class MCQQuestion(models.Model):
    question_text = models.TextField()
    option1 = models.CharField(max_length=200)
    option2 = models.CharField(max_length=200)
    option3 = models.CharField(max_length=200)
    option4 = models.CharField(max_length=200)
    correct_option = models.IntegerField(choices=[(1, 'Option 1'), (2, 'Option 2'), (3, 'Option 3'), (4, 'Option 4')])
    job = models.ForeignKey(Job, on_delete=models.CASCADE, related_name='questions')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.question_text[:50] + '...'

class TestResponse(models.Model):
    test_schedule = models.ForeignKey(TestSchedule, on_delete=models.CASCADE, related_name='responses')
    question = models.ForeignKey(MCQQuestion, on_delete=models.CASCADE)
    selected_option = models.IntegerField(choices=[(1, 'Option 1'), (2, 'Option 2'), (3, 'Option 3'), (4, 'Option 4')])
    is_correct = models.BooleanField()
    answered_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('test_schedule', 'question')
        
    def __str__(self):
        return f"Response for {self.question} in {self.test_schedule}"
