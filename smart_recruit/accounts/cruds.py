from rest_framework.decorators import api_view, parser_classes, permission_classes
from rest_framework.response import Response
from rest_framework import status
from rest_framework.parsers import JSONParser, MultiPartParser, FormParser
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from .models import Job, MCQQuestion, JobApplication
from django.shortcuts import get_object_or_404
from .serializers import *




@api_view(['PUT', 'DELETE'])
@parser_classes([JSONParser])
@permission_classes([IsAuthenticated, IsAdminUser])
def question_operations(request, question_id):
    """
    Update or delete a question
    """
    try:
        question = get_object_or_404(MCQQuestion, id=question_id)
        
        if request.method == 'PUT':
            job_id = request.data.get('job')
            if job_id:
                job = get_object_or_404(Job, id=job_id)
                request.data['job'] = job.id
                
            serializer = MCQQuestionSerializer(question, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response({
                    'status': 'success',
                    'message': 'Question updated successfully',
                    'data': serializer.data
                })
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            
        elif request.method == 'DELETE':
            question.delete()
            return Response({
                'status': 'success',
                'message': 'Question deleted successfully'
            }, status=status.HTTP_204_NO_CONTENT)
            
    except Exception as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@api_view(['PUT', 'DELETE'])
@parser_classes([MultiPartParser, FormParser, JSONParser])
@permission_classes([IsAuthenticated, IsAdminUser])
def job_operations(request, job_id):
    """
    Update or delete a job
    """
    try:
        job = get_object_or_404(Job, id=job_id)
        
        if request.method == 'PUT':
            serializer = JobSerializer(job, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response({
                    'status': 'success',
                    'message': 'Job updated successfully',
                    'data': serializer.data
                })
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            
        elif request.method == 'DELETE':
            # Delete related applications first
            JobApplication.objects.filter(job=job).delete()
            # Then delete the job
            job.delete()
            return Response({
                'status': 'success',
                'message': 'Job and related applications deleted successfully'
            }, status=status.HTTP_204_NO_CONTENT)
            
    except Exception as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
