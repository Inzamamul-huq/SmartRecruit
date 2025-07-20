from django.db import models
from django.contrib.auth.models import User

class Job(models.Model):
    title = models.CharField(max_length=100)
    description = models.TextField()
    skills_required = models.TextField()

    def __str__(self):
        return self.title

class JobApplication(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    job = models.ForeignKey(Job, on_delete=models.CASCADE)
    resume = models.FileField(upload_to='resumes/')
    status = models.CharField(max_length=20, choices=[('Pending', 'Pending'), ('Shortlisted', 'Shortlisted')], default='Pending')

    def __str__(self):
        return f"{self.user.username} - {self.job.title} - {self.status}"

class Question(models.Model):
    job = models.ForeignKey(Job, on_delete=models.CASCADE)
    question_text = models.CharField(max_length=300)
    option1 = models.CharField(max_length=100)
    option2 = models.CharField(max_length=100)
    option3 = models.CharField(max_length=100)
    option4 = models.CharField(max_length=100)
    correct_option = models.IntegerField()

    def __str__(self):
        return self.question_text

class TestSchedule(models.Model):
    job = models.ForeignKey(Job, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    scheduled_on = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.job.title}"
