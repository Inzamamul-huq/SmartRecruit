from rest_framework import serializers
from .models import *
from .validators import  email_validator, phone_validator, password_validator

class StudentSerializer(serializers.ModelSerializer):
    name = serializers.CharField()
    email = serializers.EmailField(validators=[email_validator])
    phone = serializers.CharField(validators=[phone_validator])
    password = serializers.CharField(
        write_only=True,
        validators=[password_validator],
        style={'input_type': 'password'}
    )

    class Meta:
        model = Student
        fields = '__all__'



class AdminSerializer(serializers.ModelSerializer):
    class Meta:
        model = AdminUser
        fields = '__all__'

class JobSerializer(serializers.ModelSerializer):
    applicants_count = serializers.SerializerMethodField()

    class Meta:
        model = Job
        fields = ['id', 'title', 'description', 'created_at', 'applicants_count']

    def get_applicants_count(self, obj):
        return JobApplication.objects.filter(job=obj).count()

class JobApplicationSerializer(serializers.ModelSerializer):
    student = serializers.PrimaryKeyRelatedField(queryset=Student.objects.all())
    
    class Meta:
        model = JobApplication
        fields = ['id', 'student', 'job', 'resume', 'resume_url', 'status', 'applied_at', 'updated_at']
        read_only_fields = ['applied_at', 'updated_at']

    def create(self, validated_data):
        
        student = validated_data['student']
        job = validated_data['job']
        
        
        if JobApplication.objects.filter(student=student, job=job).exists():
            raise serializers.ValidationError("You have already applied to this job.")
            
        
        return JobApplication.objects.create(**validated_data)


class TestScheduleSerializer(serializers.ModelSerializer):
    application = serializers.PrimaryKeyRelatedField(queryset=JobApplication.objects.all())
    test_time = serializers.DateTimeField()
    duration_minutes = serializers.IntegerField(min_value=1, default=60)
    
    class Meta:
        model = TestSchedule
        fields = ['id', 'application', 'test_time', 'duration_minutes', 'message', 'is_completed', 'score', 'created_at', 'updated_at']
        read_only_fields = ['created_at', 'updated_at']
    
    def validate_application(self, value):
        # Check if a test schedule already exists for this application
        if TestSchedule.objects.filter(application=value).exists():
            raise serializers.ValidationError("A test schedule already exists for this application.")
        return value

class MCQQuestionSerializer(serializers.ModelSerializer):
    correct_option = serializers.IntegerField(min_value=1, max_value=4)
    
    class Meta:
        model = MCQQuestion
        fields = ['id', 'question_text', 'option1', 'option2', 'option3', 'option4', 'correct_option']
        
    def validate_correct_option(self, value):
        if value not in [1, 2, 3, 4]:
            raise serializers.ValidationError("correct_option must be between 1 and 4")
        return value

class TestResponseSerializer(serializers.ModelSerializer):
    class Meta:
        model = TestResponse
        fields = ['id', 'test_schedule', 'question', 'selected_option', 'is_correct', 'answered_at']
        read_only_fields = ['is_correct', 'answered_at']
    
    def validate(self, data):
        
        test_schedule = data['test_schedule']
        question = data['question']
        
        if question.job_id != test_schedule.application.job_id:
            raise serializers.ValidationError("This question doesn't belong to the job this test is for.")
            
        return data

class TestResultSerializer(serializers.Serializer):
    score = serializers.IntegerField()
    total_questions = serializers.IntegerField()
    correct_answers = serializers.IntegerField()
    wrong_answers = serializers.IntegerField()
