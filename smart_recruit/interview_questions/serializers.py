from rest_framework import serializers
from .models import InterviewExperience

class InterviewExperienceSerializer(serializers.ModelSerializer):
    class Meta:
        model = InterviewExperience
        fields = '__all__'
