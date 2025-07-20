from rest_framework import serializers
from .models import Job, JobApplication, Question, TestSchedule

class JobSerializer(serializers.ModelSerializer):
    class Meta:
        model = Job
        fields = '__all__'

class JobApplicationSerializer(serializers.ModelSerializer):
    class Meta:
        model = JobApplication
        fields = '__all__'

class QuestionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Question
        fields = '__all__'

class TestScheduleSerializer(serializers.ModelSerializer):
    class Meta:
        model = TestSchedule
        fields = '__all__'
