from rest_framework.decorators import api_view, parser_classes
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.response import Response
from rest_framework import status
from .models import Job, JobApplication, Question, TestSchedule
from .serializers import JobSerializer, JobApplicationSerializer, QuestionSerializer, TestScheduleSerializer
from django.views.decorators.csrf import csrf_exempt

@csrf_exempt
@api_view(['POST'])
def create_job(request):
    serializer = JobSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response({'message': 'Job created'}, status=201)
    return Response(serializer.errors, status=400)

@csrf_exempt
@api_view(['GET'])
def list_jobs(request):
    jobs = Job.objects.all()
    serializer = JobSerializer(jobs, many=True)
    return Response(serializer.data)

@csrf_exempt
@api_view(['POST'])
@parser_classes([MultiPartParser, FormParser])
def apply_job(request):
    serializer = JobApplicationSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response({'message': 'Applied successfully'}, status=201)
    return Response(serializer.errors, status=400)

@csrf_exempt
@api_view(['POST'])
def shortlist_candidate(request):
    try:
        app_id = request.data.get('application_id')
        application = JobApplication.objects.get(id=app_id)
        application.status = 'Shortlisted'
        application.save()
        return Response({'message': 'Candidate shortlisted'})
    except JobApplication.DoesNotExist:
        return Response({'error': 'Application not found'}, status=404)

@csrf_exempt
@api_view(['POST'])
def add_question(request):
    serializer = QuestionSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response({'message': 'Question added'}, status=201)
    return Response(serializer.errors, status=400)

@csrf_exempt
@api_view(['POST'])
def schedule_test(request):
    serializer = TestScheduleSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response({'message': 'Test scheduled'}, status=201)
    return Response(serializer.errors, status=400)
