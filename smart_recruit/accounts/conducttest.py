from rest_framework.decorators import api_view, parser_classes, permission_classes
from rest_framework.response import Response
from rest_framework.parsers import JSONParser
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.db import transaction
from django.shortcuts import get_object_or_404
from django.utils import timezone as django_timezone
from datetime import datetime, timedelta, timezone
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags
import logging

logger = logging.getLogger(__name__)

from .models import Job, JobOpportunity
from .serializers import *
from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.db.models import Q


@api_view(['POST'])
@parser_classes([JSONParser])
def create_mcq_question(request):
    try:
        
        data = request.data.copy()
        job_id = data.get('job_id')
        
        
        required_fields = ['question_text', 'option1', 'option2', 'option3', 'option4', 'correct_option']
        if not all(field in data for field in required_fields):
            return Response(
                {'status': 'error', 'message': 'All fields are required'},
                status=status.HTTP_400_BAD_REQUEST
            )
            
       
        correct_option = data.get('correct_option')
        if correct_option not in [1, 2, 3, 4]:
            return Response(
                {'status': 'error', 'message': 'correct_option must be between 1 and 4'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            job = Job.objects.get(id=job_id)
            
           
            question_count = MCQQuestion.objects.filter(job=job).count()
            if question_count >= 10:
                return Response(
                    {'status': 'error', 'message': 'Maximum limit of 10 questions reached for this job'},
                    status=status.HTTP_400_BAD_REQUEST
                )
                
        except Job.DoesNotExist:
            return Response(
                {'status': 'error', 'message': 'Invalid job_id'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
       
        question = MCQQuestion.objects.create(
            job=job,
            question_text=data['question_text'],
            option1=data['option1'],
            option2=data['option2'],
            option3=data['option3'],
            option4=data['option4'],
            correct_option=correct_option
        )
        
        serializer = MCQQuestionSerializer(question)
        return Response(
            {
                'status': 'success',
                'message': 'Question added successfully',
                'data': serializer.data
            },
            status=status.HTTP_201_CREATED
        )
    except Exception as e:
        return Response(
            {'status': 'error', 'message': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@parser_classes([JSONParser])
def get_test_questions(request, test_schedule_id=None, job_id=None):
    try:
       
        job_id = job_id or request.query_params.get('job_id')
        test_schedule_id = test_schedule_id or request.query_params.get('test_schedule_id')
        job_query = request.query_params.get('job_query', '').strip().lower()
        
        if test_schedule_id:
          
            test_schedule = TestSchedule.objects.select_related('application', 'application__job').get(
                id=test_schedule_id,
                is_completed=False
            )
            
            
            test_end_time = test_schedule.test_time + timedelta(minutes=test_schedule.duration_minutes)
            
            if datetime.now(tz=timezone.utc) > test_end_time:
                return Response(
                    {'status': 'error', 'message': 'The test window has ended.'},
                    status=status.HTTP_403_FORBIDDEN
                )
                
            job = test_schedule.application.job
            questions = MCQQuestion.objects.filter(job=job).order_by('id')[:10]
            job_title = job.title
        elif job_id:
            
            questions = MCQQuestion.objects.filter(job_id=job_id).order_by('?')[:10]
            try:
                job = Job.objects.get(id=job_id)
                job_title = job.title
            except Job.DoesNotExist:
                job_title = f'Job ID: {job_id}'
        elif job_query:
            questions = MCQQuestion.objects.filter(
                job__title__icontains=job_query
            ) | MCQQuestion.objects.filter(
                job__description__icontains=job_query
            )
            questions = questions.distinct().order_by('id')[:10]
            job_title = f'Questions for jobs matching: {job_query}'
        else:
            questions = MCQQuestion.objects.all().order_by('id')[:10]
            job_title = 'All Questions'
            
        if not questions.exists():
            return Response(
                {'status': 'error', 'message': 'No questions available'},
                status=status.HTTP_404_NOT_FOUND
            )
            
        
        questions_with_job_details = []
        for question in questions:
            question_data = MCQQuestionSerializer(question).data
            if question.job:
                question_data['job_details'] = {
                    'id': question.job.id,
                    'title': question.job.title,
                    'description': question.job.description
                }
            questions_with_job_details.append(question_data)
            
        return Response({
            'status': 'success',
            'questions': questions_with_job_details,
            'total_questions': questions.count(),
            'job_title': job_title
        })
        
    except TestSchedule.DoesNotExist:
        return Response(
            {'status': 'error', 'message': 'Test schedule not found or already completed'},
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        return Response(
            {'status': 'error', 'message': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@parser_classes([JSONParser])
@permission_classes([IsAuthenticated])
def get_job_opportunities(request, job_id):
    
    logger.info(f"Fetching job opportunities for job_id: {job_id}")
    
    try:
        
        try:
            job = Job.objects.get(id=job_id)
            logger.info(f"Found job: {job.id} - {job.title}")
        except Job.DoesNotExist as e:
            logger.error(f"Job not found with id: {job_id}")
            return Response(
                {'status': 'error', 'message': 'Job not found'},
                status=status.HTTP_404_NOT_FOUND
            )
            
        try:
            opportunities = JobOpportunity.objects.filter(job_id=job_id).order_by('-created_at')
            logger.info(f"Found {opportunities.count()} opportunities for job {job_id}")
            
            opportunities_data = []
            for opp in opportunities:
                try:
                    opportunity_data = {
                        'id': opp.id,
                        'job_id': job.id,
                        'job_title': job.title,
                        'description': job.description,
                        'student_email': opp.student_email,
                        'message_sent': opp.message_sent,
                        'sent_at': opp.sent_at.isoformat() if opp.sent_at else None,
                        'created_at': opp.created_at.isoformat(),
                        'message': opp.message
                    }
                    opportunities_data.append(opportunity_data)
                except Exception as e:
                    logger.error(f"Error serializing opportunity {opp.id}: {str(e)}", exc_info=True)
                    continue
            
            response_data = {
                'status': 'success',
                'job': {
                    'id': job.id,
                    'title': job.title,
                    'description': job.description,
                    'job_date': job.job_date.isoformat() if job.job_date else None
                },
                'opportunities': opportunities_data
            }
            
            logger.info(f"Successfully returning {len(opportunities_data)} opportunities")
            return Response(response_data)
            
        except Exception as e:
            logger.error(f"Error processing opportunities for job {job_id}: {str(e)}", exc_info=True)
            return Response(
                {'status': 'error', 'message': 'Failed to process job opportunities'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
    except Exception as e:
        logger.error(f"Unexpected error in get_job_opportunities: {str(e)}", exc_info=True)
        return Response(
            {'status': 'error', 'message': 'An unexpected error occurred'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@parser_classes([JSONParser])
@permission_classes([IsAuthenticated])
@transaction.atomic
def send_job_details(request):
    logger.info(f"Received job details request with data: {request.data}")
    try:
        student_email = request.data.get('student_email')
        job_id = request.data.get('job_id')
        message = request.data.get('message', '')
        
        if not student_email or not job_id:
            return Response(
                {'status': 'error', 'message': 'Student email and job ID are required'},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        if JobOpportunity.objects.filter(job_id=job_id, student_email=student_email).exists():
            return Response(
                {'status': 'error', 'message': 'Job opportunity already sent to this student'},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        
        try:
            job = Job.objects.get(id=job_id)
        except Job.DoesNotExist:
            return Response(
                {'status': 'error', 'message': 'Job not found'},
                status=status.HTTP_404_NOT_FOUND
            )
            
        
        opportunity = JobOpportunity.objects.create(
            title=job.title,
            description=message or job.description,
            job_date=job.job_date if hasattr(job, 'job_date') else timezone.now().date(),
            created_by=request.user,
            job=job,
            student_email=student_email,
            message_sent=False
        )
        
        try:
            
            subject = f"Job Opportunity: {job.title}"
            html_message = render_to_string('emails/job_opportunity.html', {
                'job': job,
                'message': message,
                'opportunity': opportunity
            })
            text_message = strip_tags(html_message)
            
            email = EmailMultiAlternatives(
                subject=subject,
                body=text_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[student_email],
                reply_to=[request.user.email]
            )
            email.attach_alternative(html_message, "text/html")
            email.send()
            
            
            opportunity.message_sent = True
            opportunity.save()
            
            return Response({
                'status': 'success', 
                'message': 'Job details sent successfully',
                'job_id': job.id,
                'student_email': student_email,
                'opportunity_id': opportunity.id
            })
            
        except Exception as e:
            
            opportunity.delete()
            logger.error(f"Error sending email: {str(e)}", exc_info=True)
            raise Exception("Failed to send email")
            
    except Exception as e:
        logger.error(f"Error in send_job_details: {str(e)}", exc_info=True)
        return Response(
            {'status': 'error', 'message': f'Failed to send job details: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@parser_classes([JSONParser])
@permission_classes([IsAuthenticated])
def get_opportunities_by_student(request):
    
    try:
        student_email = request.query_params.get('student_email')
        if not student_email:
            return Response(
                {'status': 'error', 'message': 'student_email parameter is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        opportunities = JobOpportunity.objects.filter(
            student_email=student_email
        ).select_related('job').order_by('-created_at')
        
        opportunities_data = []
        for opp in opportunities:
            opportunities_data.append({
                'id': opp.id,
                'job_id': opp.job.id,
                'job_title': opp.title,  
                'description': opp.description, 
                'student_email': opp.student_email,
                'message_sent': opp.message_sent,
                'sent_at': opp.sent_at.isoformat() if opp.sent_at else None,
                'created_at': opp.created_at.isoformat(),
                'message': getattr(opp, 'message', ''), 
                'job_date': opp.job_date.isoformat() if opp.job_date else None 
            })
            
        return Response({
            'status': 'success',
            'opportunities': opportunities_data
        })
        
    except Exception as e:
        logger.error(f"Error getting student opportunities: {str(e)}")
        return Response(
            {'status': 'error', 'message': 'Failed to get job opportunities'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@api_view(['POST'])
@parser_classes([JSONParser])
@permission_classes([IsAuthenticated])
def send_job_opportunities(request):
    logger.info(f"Received job opportunities request: {request.data}")
    try:
        data = request.data
        job_id = data.get('job_id')
        student_emails = data.get('student_emails', [])
        title = data.get('title', '')
        description = data.get('description', '')
        job_date = data.get('date')
        
        logger.info(f"Processing job opportunities - Job ID: {job_id}, Emails: {student_emails}")
        
        
        if not job_id:
            return Response(
                {'status': 'error', 'message': 'Job ID is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        if not student_emails:
            return Response(
                {'status': 'error', 'message': 'At least one student email is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        
        if job_date:
            try:
                job_date = datetime.strptime(job_date, '%Y-%m-%d').date()
            except (ValueError, TypeError):
                return Response(
                    {'status': 'error', 'message': 'Invalid date format. Use YYYY-MM-DD'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        if not job_id or not student_emails:
            return Response(
                {'status': 'error', 'message': 'Job ID and at least one student email are required'},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        if not isinstance(student_emails, list):
            student_emails = [student_emails]
            
        job = get_object_or_404(Job, id=job_id)
        created_opportunities = []
        
        for email in student_emails:
            
            if JobOpportunity.objects.filter(job_id=job_id, student_email=email).exists():
                continue
                
            
            opportunity = JobOpportunity.objects.create(
                job=job,
                title=title or job.title,
                description=description,
                job_date=job_date or timezone.now().date(),
                student_email=email,
                created_by=request.user,
                message_sent=False
            )
            created_opportunities.append(opportunity)
            
            try:
                
                context = {
                    'job': job,
                    'title': title or job.title,
                    'description': description,
                    'job_date': job_date,
                    'student_email': email
                }
                
                
                html_content = render_to_string('emails/job_opportunity.html', context)
                text_content = strip_tags(html_content)
                
                
                email_msg = EmailMultiAlternatives(
                    f'Job Opportunity: {title or job.title}',
                    text_content,
                    settings.DEFAULT_FROM_EMAIL,
                    [email]
                )
                email_msg.attach_alternative(html_content, "text/html")
                email_msg.send()
                
                
                opportunity.message_sent = True
                opportunity.sent_at = timezone.now()
                opportunity.save()
                
            except Exception as e:
                logger.error(f"Error sending job details to {email}: {str(e)}")
                
                continue
        
        if not created_opportunities:
            logger.info("No new opportunities created - likely all were duplicates")
            return Response({
                'status': 'info',
                'message': 'No new job opportunities were created (may have already been sent)'
            })
            
        success_message = f'Successfully created {len(created_opportunities)} job opportunity records'
        logger.info(success_message)
        return Response({
            'status': 'success',
            'message': success_message,
            'opportunity_count': len(created_opportunities),
            'job_id': job_id,
            'title': title
        })
            
    except Exception as e:
        logger.error(f"Error in send_job_opportunities: {str(e)}")
        return Response(
            {'status': 'error', 'message': 'An error occurred while processing your request'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
def get_job_details(request, job_id):
    try:
        job = JobOpportunity.objects.get(id=job_id)
        job_data = {
            'id': job.id,
            'title': job.title,
            'description': job.description,
            'created_at': job.created_at,
            'job_date': str(job.job_date) if hasattr(job, 'job_date') else None,
            'created_by': job.created_by.username if job.created_by else 'System'
        }
        return Response(job_data)
    except JobOpportunity.DoesNotExist:
        return Response(
            {'status': 'error', 'message': 'Job opportunity not found'},
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        logger.error(f"Error getting job details: {str(e)}")
        return Response(
            {'status': 'error', 'message': 'Failed to get job details'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@api_view(['POST'])
@parser_classes([JSONParser])
def submit_test_answers(request, test_schedule_id):
    try:
        
        
        if not isinstance(request.data, dict):
            return Response(
                {'status': 'error', 'message': 'Invalid request data format'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        
        try:
            
            
            test_schedule = TestSchedule.objects.select_related(
                'application', 
                'application__student', 
                'application__job'
            ).select_for_update().get(
                id=test_schedule_id,
                is_completed=False
            )
            
            
            
        except TestSchedule.DoesNotExist:
            error_msg = 'Test schedule not found or already completed'
            
            return Response(
                {'status': 'error', 'message': error_msg}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        
        student_email = request.data.get('student_email', '').strip().lower()
        expected_email = test_schedule.application.student.email.lower()
        
        if not student_email:
            error_msg = 'Student email is required'
            return Response(
                {'status': 'error', 'message': error_msg}, 
                status=status.HTTP_400_BAD_REQUEST
            )
            
        if student_email != expected_email:
            error_msg = 'Unauthorized for this test'
            return Response(
                {'status': 'error', 'message': error_msg}, 
                status=status.HTTP_403_FORBIDDEN
            )

        test_start_time = test_schedule.test_time
        if not test_schedule.duration_minutes:
            test_schedule.duration_minutes = 60  # Default to 60 minutes if not set
            test_schedule.save()
            
        test_end_time = test_start_time + timedelta(minutes=test_schedule.duration_minutes)
        current_time = django_timezone.now()
        
        if test_start_time.tzinfo is None:
            test_start_time = django_timezone.make_aware(test_start_time)
        if test_end_time.tzinfo is None:
            test_end_time = django_timezone.make_aware(test_end_time)
        
        
        
        if current_time > test_end_time:
            message = f'Test submission window has ended. The test ended on {test_end_time.strftime("%Y-%m-%d %H:%M %Z")}.'
            
            return Response(
                {'status': 'error', 'message': message}, 
                status=status.HTTP_403_FORBIDDEN
            )
            
        
        
        answers = request.data.get('answers', [])
        if not isinstance(answers, list):
            error_msg = 'Answers should be a list of question-answer pairs'
            return Response(
                {'status': 'error', 'message': error_msg},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        
        
        correct_answers = 0
        total_questions = 10  
       
        for answer in answers:
            try:
                question = MCQQuestion.objects.get(
                    id=answer.get('question_id'),
                    job=test_schedule.application.job
                )
                
                selected_option = answer.get('selected_option')
                is_correct = (selected_option == question.correct_option)
                
                if is_correct:
                    correct_answers += 1
                
                tr, _created = TestResponse.objects.update_or_create(
                    test_schedule=test_schedule,
                    question=question,
                    defaults={
                        'selected_option': selected_option,
                        'is_correct': is_correct
                    }
                )
                
            except (MCQQuestion.DoesNotExist, ValueError, KeyError):
                continue
        
        score = correct_answers
        
        
        test_schedule.is_completed = True
        test_schedule.score = score
        test_schedule.save()
        
        
        result = {
            'status': 'success',
            'message': 'Test submitted successfully',
            'result': {
                'score': score,
                'total_questions': total_questions,
                'correct_answers': correct_answers,
                'wrong_answers': total_questions - correct_answers
            }
        }
        
        return Response(result)
        
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        logger.error(f"Error in submit_test_answers: {str(e)}\n{error_trace}")
        
        
        
        return Response(
            {
                'status': 'error',
                'message': 'An unexpected error occurred. Please try again.'
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
