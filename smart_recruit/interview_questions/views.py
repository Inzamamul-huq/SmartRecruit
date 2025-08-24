from django.shortcuts import  get_object_or_404
from rest_framework.decorators import api_view, parser_classes, permission_classes
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from .models import InterviewExperience
from .serializers import InterviewExperienceSerializer
from accounts.models import Student, Job

@api_view(['POST'])
@parser_classes([MultiPartParser, FormParser])
@permission_classes([IsAuthenticated])
def post_interview_experience(request):
    try:
        
        student_email = request.data.get('student_email') or getattr(request.user, 'email', None)
        student = get_object_or_404(Student, email=student_email)
        job_id = request.data.get('job_id')
        job = get_object_or_404(Job, id=job_id) if job_id else None
        
        
        experience_data = {
            'student': student.id,
            'student_email': student.email,
            'job': job.id if job else None,
            'company_name': request.data.get('company_name'),
            'division_name': request.data.get('division_name'),
            'aptitude_conducted': request.data.get('aptitude_conducted', 'false').lower() == 'true',
            'aptitude_questions': request.data.get('aptitude_questions'),
            'technical_conducted': request.data.get('technical_conducted', 'false').lower() == 'true',
            'technical_questions': request.data.get('technical_questions'),
            'gd_conducted': request.data.get('gd_conducted', 'false').lower() == 'true',
            'gd_topics': request.data.get('gd_topics'),
            'hr_conducted': request.data.get('hr_conducted', 'false').lower() == 'true',
            'hr_questions': request.data.get('hr_questions'),
            'tips': request.data.get('tips'),
            'overall_experience': request.data.get('overall_experience'),
        }
        
        
        for field in ['aptitude_attachment', 'technical_attachment', 'gd_attachment', 'hr_attachment']:
            if field in request.FILES:
                experience_data[field] = request.FILES[field]
        
        serializer = InterviewExperienceSerializer(data=experience_data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_all_experiences(request):
    experiences = InterviewExperience.objects.all().order_by('-submitted_at')
    serializer = InterviewExperienceSerializer(experiences, many=True)
    return Response(serializer.data)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_job_experiences(request, job_id):
    experiences = InterviewExperience.objects.filter(job_id=job_id).order_by('-submitted_at')
    serializer = InterviewExperienceSerializer(experiences, many=True)
    return Response(serializer.data)

@api_view(['GET'])
@permission_classes([IsAuthenticatedOrReadOnly])
def get_experience_detail(request, pk):
    experience = get_object_or_404(InterviewExperience, pk=pk)
    serializer = InterviewExperienceSerializer(experience)
    return Response(serializer.data)

@api_view(['PUT', 'PATCH'])
@permission_classes([IsAuthenticated])
def update_experience(request, pk):
    experience = get_object_or_404(InterviewExperience, pk=pk)
    
    if request.user != experience.student.user:
        return Response(
            {"error": "You do not have permission to perform this action."},
            status=status.HTTP_403_FORBIDDEN
        )
    
    serializer = InterviewExperienceSerializer(
        experience, 
        data=request.data, 
        partial=request.method == 'PATCH'
    )
    
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_experience(request, pk):
    experience = get_object_or_404(InterviewExperience, pk=pk)
    
    if request.user != experience.student.user:
        return Response(
            {"error": "You do not have permission to perform this action."},
            status=status.HTTP_403_FORBIDDEN
        )
    
    experience.delete()
    return Response(status=status.HTTP_204_NO_CONTENT)
