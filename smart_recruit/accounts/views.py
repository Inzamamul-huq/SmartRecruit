from rest_framework.decorators import api_view, parser_classes, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.contrib.auth.hashers import make_password,check_password
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from rest_framework import status
from .models import *
from .serializers import *
import random

from django.core.mail import send_mail
from django.conf import settings
import os
from rest_framework.parsers import MultiPartParser
from django.conf import settings
from smart_recruit.supabase_storage import upload_file
from django.utils import timezone
from django.shortcuts import get_object_or_404


@api_view(['POST'])
@permission_classes([AllowAny])
def student_signup(request):
    if request.method == 'POST':

        if Student.objects.filter(email=request.data.get('email')).exists():
            return Response(
                {'error': 'Email already exists'},
                status=status.HTTP_400_BAD_REQUEST
            )
        data = request.data.copy()
        data['password'] = make_password(data.get('password'))

        serializer = StudentSerializer(data=data)
        if serializer.is_valid():
            user = serializer.save()

            return Response({'status': 'signup success', 'id': user.id, 'name': user.name})
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)

@api_view(['POST'])
def toggle_user_approval(request, user_id):
    try:
        student = Student.objects.get(id=user_id)
        student.allow = 'allow' if student.allow != 'allow' else None
        student.save()
        return Response({
            'status': 'success',
            'message': f'User approval status updated',
            'is_approved': student.allow == 'allow'
        })
    except Student.DoesNotExist:
        return Response({'status': 'error', 'message': 'User not found'}, status=404)
    except Exception as e:
        return Response({'status': 'error', 'message': str(e)}, status=500)


@api_view(['POST'])
def update_selection_status(request, student_id):
    try:
        student = get_object_or_404(Student, pk=student_id)
        is_selected = request.data.get('is_selected')
        
        if is_selected is None:
            return Response({'status': 'error', 'message': 'is_selected field is required'}, status=400)
            
        student.is_selected = is_selected
        student.save()
        
        return Response({
            'status': 'success',
            'message': f'Selection status updated successfully',
            'student_id': student.id,
            'is_selected': student.is_selected
        })
        
    except Exception as e:
        return Response({'status': 'error', 'message': str(e)}, status=500)


@api_view(['GET'])
def student_view(request):
    
    is_admin = request.query_params.get('admin', '').lower() == 'true'
    student_id = request.query_params.get('student_id')
    
    try:
        if student_id:
           
            student = Student.objects.get(id=student_id)
            serializer = StudentSerializer(student)
            return Response({
                'status': 'success',
                'user_type': 'student',
                'data': serializer.data
            })

        elif is_admin:
           
            users = Student.objects.all()
            serializer = StudentSerializer(users, many=True)
            return Response({
                'status': 'success',
                'user_type': 'admin',
                'data': serializer.data
            })

        else:
            
            return Response({
                'status': 'error',
                'message': 'Unauthorized access. Please provide student_id or admin=true'
            }, status=401)
            
    except Student.DoesNotExist:
        return Response({'status': 'error', 'message': 'Student not found'}, status=404)
    
    except Exception as e:
        return Response({'status': 'error', 'message': str(e)}, status=500)


from django.utils import timezone
from datetime import timedelta

@api_view(['POST'])
@permission_classes([AllowAny])
def send_otp(request):
    email = request.data['email']
    if not Student.objects.filter(email=email).exists():
        return Response({'status': 'Email not found'}, status=404)
    
    OTP.objects.filter(email=email).delete()
    otp = str(random.randint(100000, 999999))
    OTP.objects.create(email=email, otp=otp, created_at=timezone.now())
    send_mail(
        'Reset Password OTP', 
        f'Your OTP is: {otp}\nThis OTP is valid for 10 minutes.',
        'your_email@gmail.com',
        [email],
        fail_silently=False
    )
    return Response({'status': 'OTP sent to your email'})

@api_view(['POST'])
@permission_classes([AllowAny])
def verify_otp(request):
    try:
        email = request.data.get('email')
        otp = request.data.get('otp')
        if not all([email, otp]):
            return Response(
                {'status': 'error', 'message': 'Email and OTP are required'}, 
                status=400
            )
        
        otp_obj = OTP.objects.filter(email=email).order_by('-created_at').first()
        if not otp_obj:
            return Response(
                {'status': 'error', 'message': 'No OTP found for this email'},
                status=400
            )
        
        if timezone.now() > otp_obj.created_at + timedelta(minutes=10):
            otp_obj.delete()
            return Response(
                {'status': 'error', 'message': 'OTP has expired. Please request a new one.'},
                status=400
            )
    
        if otp_obj.otp != otp:
            return Response(
                {'status': 'error', 'message': 'Invalid OTP'},
                status=400
            )
        
        return Response({'status': 'success', 'message': 'OTP verified successfully'})
        
    except Exception as e:
        return Response(
            {'status': 'error', 'message': str(e)},
            status=500
        )

@api_view(['POST'])
@permission_classes([AllowAny])
def reset_password(request):
    try:
        email = request.data.get('email')
        otp = request.data.get('otp')
        new_password = request.data.get('new_password')
        
        if not all([email, otp, new_password]):
            return Response(
                {'status': 'error', 'message': 'Email, OTP and new password are required'}, 
                status=400
            )
        
        otp_obj = OTP.objects.filter(email=email).order_by('-created_at').first()
        if not otp_obj:
            return Response(
                {'status': 'error', 'message': 'No OTP found for this email'},
                status=400
            )
        
        
        if timezone.now() > otp_obj.created_at + timedelta(minutes=10):
            otp_obj.delete()
            return Response(
                {'status': 'error', 'message': 'OTP has expired. Please request a new one.'},
                status=400
            )
        
        if otp_obj.otp != otp:
            return Response(
                {'status': 'error', 'message': 'Invalid OTP'},
                status=400
            )
        
        
        student = Student.objects.get(email=email)
        student.password = make_password(new_password)
        student.save()
        otp_obj.delete()
        
        return Response({'status': 'success', 'message': 'Password reset successful'})
        
    except Student.DoesNotExist:
        return Response(
            {'status': 'error', 'message': 'Student not found'},
            status=404
        )
    except Exception as e:
        return Response(
            {'status': 'error', 'message': str(e)},
            status=500
        )

from rest_framework.permissions import AllowAny

@api_view(['POST'])
@permission_classes([AllowAny])
def admin_signup(request):
    
    try:
        data = request.data
        
        data['password'] = make_password(data.get('password'))
        
        serializer = AdminSerializer(data=data)
        if serializer.is_valid():
            serializer.save()
            return Response({
                "status": "success",
                "message": "Admin created successfully",
                "data": serializer.data
            }, status=status.HTTP_201_CREATED)
        return Response({
            "status": "error",
            "message": "Invalid data",
            "errors": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)
        
    except Exception as e:
        return Response({
            "status": "error",
            "message": str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# ---------- JOBS ----------
@api_view(['POST'])
def post_job(request):
    serializer = JobSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response({'status': 'Job posted'})
    return Response(serializer.errors)

@api_view(['GET'])
def job_list(request):
    jobs = Job.objects.all().order_by('-id')
    serializer = JobSerializer(jobs, many=True)
    return Response(serializer.data)

@api_view(['POST'])
@parser_classes([MultiPartParser])
def apply_for_job(request, job_id):
   
    try:
        student_id = request.data.get('student_id')
        resume_file = request.FILES.get('resume')
        
        if not student_id:
            return Response(
                {"error": "student_id is required"},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        if not resume_file:
            return Response(
                {"error": "Resume file is required"},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        student = get_object_or_404(Student, id=student_id)
        job = get_object_or_404(Job, id=job_id)
        
        
        from datetime import datetime, timedelta
        from django.utils import timezone
        from interview_questions.models import InterviewExperience
        
        
        recent_opportunity = JobOpportunity.objects.filter(
            student_email=student.email,
            job_date__lte=timezone.now().date()
        ).order_by('-job_date').first()
        
        if recent_opportunity:
            job_datetime = timezone.make_aware(
                datetime.combine(recent_opportunity.job_date, datetime.min.time())
            )
            
            
            has_experience = InterviewExperience.objects.filter(
                student_email=student.email,
                job=recent_opportunity.job,
                submitted_at__gt=job_datetime
            ).exists()
            
            time_since_opportunity = (timezone.now() - job_datetime).total_seconds()
            two_days_in_seconds = 2 * 24 * 60 * 60  # 2 days in seconds
            
            if time_since_opportunity > two_days_in_seconds and not has_experience:
                return Response(
                    {
                        "error": "Please submit your interview experience for the previous job to apply for new opportunities.",
                        "code": "interview_experience_required",
                        "job_opportunity_id": recent_opportunity.id,
                        "job_title": recent_opportunity.title,
                        "job_date": recent_opportunity.job_date.isoformat(),
                        "time_elapsed_seconds": time_since_opportunity
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        application_data = {
            'student': student.id,  
            'job': job.id,
            'resume': resume_file,
            'status': 'applied'
        }
        
        serializer = JobApplicationSerializer(data=application_data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            
        application = serializer.save()

        # Upload resume to Supabase and store URL
        try:
            upload = upload_file(resume_file, f"applications/{application.id}")
            application.resume_url = upload.get('public_url') or upload.get('signed_url')
            application.save(update_fields=['resume_url'])
        except Exception as e:
            print(f"Supabase upload failed for application {application.id}: {e}")
        
       
        try:
            send_mail(
                'Application Submitted',
                f'Your application for {job.title} has been received and is under review.',
                settings.DEFAULT_FROM_EMAIL,
                [student.email],
                fail_silently=False,
            )
        except Exception as e:
            print(f"Error sending confirmation email: {e}")
        
        return Response({
            "success": True,
            "status": "success",
            "message": "Successfully applied for the job",
            "application_id": application.id,
            "job_id": job.id,
            "job_title": job.title,
            "status": application.status,
            "applied_at": application.applied_at.isoformat(),
            "resume_uploaded": True,
            "resume_url": application.resume_url
        }, status=status.HTTP_201_CREATED)
        
    except Exception as e:
        import traceback
        print(f"Error in apply_for_job: {str(e)}\n{traceback.format_exc()}")
        return Response(
            {"error": str(e), "detail": "An error occurred while processing your application"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@api_view(['GET'])
def job_detail(request, job_id):
    
    try:
        job = get_object_or_404(Job, id=job_id)
        student_id = request.query_params.get('student_id')
        
        response_data = JobSerializer(job).data
        
       
        if student_id:
            has_applied = TestSchedule.objects.filter(job=job, student_id=student_id).exists()
            response_data['has_applied'] = has_applied
            
            if has_applied:
                application = TestSchedule.objects.get(job=job, student_id=student_id)
                response_data['application_status'] = {
                    'applied_at': application.applied_at,
                    'is_completed': application.is_completed,
                    'score': application.score
                }
        
        return Response(response_data)
        
    except Job.DoesNotExist:
        return Response(
            {"error": "Job not found"},
            status=status.HTTP_404_NOT_FOUND
        )

@api_view(['GET'])
def get_active_test_schedule(request, student_email):
    
    try:
        print(f"Looking up student with email: {student_email}")
        student = Student.objects.get(email=student_email)
        print(f"Found student: {student.id} - {student.email}")
        
        applications = JobApplication.objects.filter(student=student).select_related('job')
        print(f"Found {applications.count()} applications")
        
        schedules = []
        for app in applications:
            if hasattr(app, 'test_schedule') and app.test_schedule and not app.test_schedule.is_completed:
                ts = app.test_schedule
                schedules.append({
                    'id': ts.id,
                    'test_time': ts.test_time.isoformat() if ts.test_time else None,
                    'is_completed': ts.is_completed,
                    'score': ts.score,
                    'job': {
                        'id': app.job.id,
                        'title': app.job.title,
                        'description': app.job.description,
                    }
                })
        
        print(f"Found {len(schedules)} active test schedules")
        schedules.sort(key=lambda x: (x['test_time'] is None, x['test_time']))
        
        return Response({
            'status': 'success',
            'count': len(schedules),
            'schedules': schedules
        })
        
    except Student.DoesNotExist:
        print(f"Student with email {student_email} not found")
        return Response(
            {'status': 'error', 'message': 'Student not found'},
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        print(f"Error in get_active_test_schedule: {str(e)}")
        return Response(
            {'status': 'error', 'message': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@api_view(['GET'])
def get_test_results(request, test_schedule_id):
    
    try:
        test_schedule = get_object_or_404(TestSchedule, id=test_schedule_id)
        
        
        responses = TestResponse.objects.filter(
            test_schedule=test_schedule
        ).select_related('question')
        
        response_data = []
        for resp in responses:
            response_data.append({
                'question_text': resp.question.question_text,
                'selected_option': resp.selected_option,
                'correct_option': resp.question.correct_option,
                'is_correct': resp.is_correct
            })
        
        return Response({
            'status': 'success',
            'test': {
                'id': test_schedule.id,
                'test_time': test_schedule.test_time,
                'is_completed': test_schedule.is_completed,
                'score': test_schedule.score,
                'responses': response_data
            },
            'student': {
                'id': test_schedule.application.student.id,
                'name': test_schedule.application.student.name,
                'email': test_schedule.application.student.email
            },
            'job': {
                'id': test_schedule.application.job.id,
                'title': test_schedule.application.job.title
            }
        })
        
    except Exception as e:
        return Response(
            {'status': 'error', 'message': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

# ---------- JOB APPLICANTS ----------
@api_view(['GET'])
def job_applicants(request, job_id):
    """
    Get all students who have applied for a specific job with their application status, test schedule, and scores
    """
    try:
        job = get_object_or_404(Job, id=job_id)
        
        applications = JobApplication.objects.filter(job=job).select_related(
            'student', 'test_schedule'
        )
        
        applicants = []
        for app in applications:
            student = app.student
            
           
            test_score = None
            if hasattr(app, 'test_schedule') and app.test_schedule and app.test_schedule.is_completed:
                test_score = app.test_schedule.score
            
            # First check if we have a resume URL from the student
            resume_url = getattr(student, 'resume_url', None)
            
            # If no resume URL from student, check the application
            if not resume_url:
                resume_url = getattr(app, 'resume_url', None)
            
            # If still no resume URL, check the old resume field
            if not resume_url and app.resume:
                if hasattr(app.resume, 'url') and app.resume.url:
                    resume_url = request.build_absolute_uri(app.resume.url)
                elif isinstance(app.resume, str):
                    if os.path.exists(app.resume):
                        media_root = settings.MEDIA_ROOT
                        if app.resume.startswith(media_root):
                            relative_path = app.resume[len(media_root):].lstrip('/')
                            resume_url = request.build_absolute_uri(settings.MEDIA_URL + relative_path)
                    # If it's already a URL (like from Supabase), use it as is
                    elif app.resume.startswith(('http://', 'https://')):
                        resume_url = app.resume
            
            test_schedule = None
            if hasattr(app, 'test_schedule'):
                test_schedule = {
                    'test_schedule_id': app.test_schedule.id,
                    'test_time': app.test_schedule.test_time.isoformat() if app.test_schedule.test_time else None,
                    'test_completed': app.test_schedule.is_completed,
                    'test_score': app.test_schedule.score,
                    'message': app.test_schedule.message
                }
            
            applicants.append({
                'application_id': app.id,
                'student_id': student.id,
                'name': student.name,
                'email': student.email,
                'phone': student.phone,
                'status': app.status,
                'status_display': app.get_status_display(),
                'is_selected': student.is_selected,
                'resume_url': resume_url,
                'applied_at': app.applied_at.isoformat() if app.applied_at else None,
                'test_schedule': test_schedule
            })
        
        return Response({
            'status': 'success',
            'job_id': job.id,
            'job_title': job.title,
            'total_applicants': len(applicants),
            'applicants': applicants
        })
        
    except Exception as e:
        import traceback
        print(f"Error in job_applicants: {str(e)}\n{traceback.format_exc()}")
        return Response({
            'status': 'error',
            'message': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ---------- RESUME ----------
@api_view(['POST'])
@parser_classes([MultiPartParser])
def upload_resume(request, student_id):
    try:
        file = request.FILES.get('resume')
        if not file:
            return Response(
                {'error': 'No file provided. Please upload a file under the field name "resume".'},
                status=status.HTTP_400_BAD_REQUEST
            )

        allowed_ext = ('.pdf', '.doc', '.docx')
        if not file.name.lower().endswith(allowed_ext):
            return Response(
                {'error': 'Only PDF/DOC/DOCX files are allowed.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            student = Student.objects.get(id=student_id)
        except Student.DoesNotExist:
            return Response({'error': 'Student not found'}, status=status.HTTP_404_NOT_FOUND)

        # Upload to Supabase
        try:
            # Upload file to Supabase with student-specific path
            up = upload_file(file, f"students/{student.id}")
            
            # Get the public URL (should be accessible without authentication)
            resume_url = up.get('public_url')
            
            # If public URL is not available, try signed URL as fallback
            if not resume_url:
                resume_url = up.get('signed_url')
                
            if not resume_url:
                return Response(
                    {'error': 'Failed to get file URL from storage'},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
                
            # Ensure the URL is a string and clean it up
            resume_url = str(resume_url).split('?')[0]  # Remove any query parameters
            
            # Save the URL to the student record
            student.resume_url = resume_url
            student.save(update_fields=['resume_url'])
            
            print(f"Resume uploaded successfully to: {resume_url}")
            
        except Exception as e:
            import traceback
            error_detail = f"{str(e)}\n{traceback.format_exc()}"
            print(f"Error uploading resume: {error_detail}")
            return Response(
                {'error': 'Failed to upload resume to storage', 'detail': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        return Response({'status': 'Resume uploaded', 'resume_url': student.resume_url})
    except Exception as e:
        import traceback
        print(f"Error in upload_resume: {str(e)}\n{traceback.format_exc()}")
        return Response(
            {'error': 'Internal server error', 'detail': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@api_view(['GET'])
def view_studentadmin(request):
    student = Student.objects.all()
    serializer = StudentSerializer(student, many=True)
    return Response(serializer.data)
    
@api_view(['GET'])
def view_single_student(request, student_id):
    try:
        student = Student.objects.get(id=student_id)
    except Student.DoesNotExist:
        return Response({'error': 'Student not found'}, status=status.HTTP_404_NOT_FOUND)

# ---------- STUDENT PROFILE ----------
@api_view(['GET', 'PUT', 'PATCH'])
@permission_classes([IsAuthenticated])
def student_profile(request):
    
    try:
        email = getattr(request.user, 'email', None) or request.query_params.get('email')
        if not email:
            return Response({'error': 'Unable to resolve current user email'}, status=status.HTTP_400_BAD_REQUEST)
        student = Student.objects.filter(email=email).first()
        if not student:
            return Response({'error': 'Student not found'}, status=status.HTTP_404_NOT_FOUND)

        if request.method in ['PUT', 'PATCH']:
            data = {}
            name = request.data.get('name')
            phone = request.data.get('phone')
            if name is not None:
                student.name = name
            if phone is not None:
                student.phone = phone
            student.save()
        
        
        return Response({
            'id': student.id,
            'name': student.name,
            'email': student.email,
            'phone': student.phone,
            'resume': student.resume.url if getattr(student, 'resume', None) else None,
            'resume_url': getattr(student, 'resume_url', None),
        })
    except Exception as e:
        return Response({'error': str(e)}, status=500)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def student_change_password(request):
    
    try:
        email = getattr(request.user, 'email', None) or request.data.get('email')
        if not email:
            return Response({'error': 'Unable to resolve current user email'}, status=status.HTTP_400_BAD_REQUEST)
        student = Student.objects.filter(email=email).first()
        if not student:
            return Response({'error': 'Student not found'}, status=status.HTTP_404_NOT_FOUND)

        current_password = request.data.get('current_password')
        new_password = request.data.get('new_password')
        confirm_new_password = request.data.get('confirm_new_password')

        if not all([current_password, new_password, confirm_new_password]):
            return Response({'error': 'All password fields are required'}, status=400)
        if not check_password(current_password, student.password):
            return Response({'error': 'Current password is incorrect'}, status=400)
        if new_password != confirm_new_password:
            return Response({'error': 'New passwords do not match'}, status=400)

        student.password = make_password(new_password)
        student.save()
        return Response({'status': 'Password updated successfully'})
    except Exception as e:
        return Response({'error': str(e)}, status=500)

# ---------- ADMIN PROFILE (PASSWORD CHANGE ONLY) ----------
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def admin_change_password(request):
    
    user = request.user
    if not getattr(user, 'is_staff', False):
        return Response({'error': 'Only admin users can change password here'}, status=status.HTTP_403_FORBIDDEN)

    data = request.data or {}
    current_password = data.get('current_password')
    new_password = data.get('new_password')
    confirm_new_password = data.get('confirm_new_password')

    if not current_password or not new_password or not confirm_new_password:
        return Response({'error': 'current_password, new_password, confirm_new_password are required'}, status=status.HTTP_400_BAD_REQUEST)

    if new_password != confirm_new_password:
        return Response({'error': 'New passwords do not match'}, status=status.HTTP_400_BAD_REQUEST)

    
    if len(new_password) < 6:
        return Response({'error': 'New password must be at least 6 characters'}, status=status.HTTP_400_BAD_REQUEST)

    admin_email = getattr(user, 'email', None) or getattr(user, 'username', None)
    if not admin_email:
        return Response({'error': 'Admin email not found on user'}, status=status.HTTP_400_BAD_REQUEST)

    from .models import AdminUser
    admin = AdminUser.objects.filter(email=admin_email).first()
    if not admin:
        return Response({'error': 'Admin record not found'}, status=status.HTTP_404_NOT_FOUND)

    
    if not check_password(current_password, admin.password):
        return Response({'error': 'Current password is incorrect'}, status=status.HTTP_400_BAD_REQUEST)

   
    admin.password = make_password(new_password)
    admin.save(update_fields=['password'])

    return Response({'status': 'Password updated successfully'})
    
    serializer = StudentSerializer(student)
    return Response(serializer.data)

@api_view(['GET'])
def get_student_by_email(request):
    email = request.GET.get('email')
    if not email:
        return Response(
            {'status': 'error', 'message': 'Email parameter is required'},
            status=status.HTTP_400_BAD_REQUEST
        )
    try:
        student = Student.objects.get(email=email)
        return Response({'id': student.id, 'name': student.name, 'email': student.email})
    except Student.DoesNotExist:
        return Response(
            {'status': 'error', 'message': 'Student not found'},
            status=status.HTTP_404_NOT_FOUND
        )

@api_view(['GET'])
def get_student_applications(request, email):
    
    try:
        
        student = Student.objects.get(email=email)
        
        
        applications = JobApplication.objects.filter(
            student=student
        ).select_related('job', 'test_schedule').order_by('-applied_at')
        
       
        data = []
        for app in applications:
            app_data = {
                'id': app.id,
                'job': {
                    'id': app.job.id,
                    'title': app.job.title,
                    'description': app.job.description,
                    'created_at': app.job.created_at
                },
                'status': app.status,
                'applied_at': app.applied_at,
                'test_scheduled': False,
                'test_info': None
            }
            
            
            if hasattr(app, 'test_schedule'):
                test = app.test_schedule
                app_data.update({
                    'test_scheduled': True,
                    'test_info': {
                        'id': test.id,
                        'test_time': test.test_time,
                        'duration_minutes': test.duration_minutes,
                        'is_completed': test.is_completed,
                        'score': test.score,
                        'can_start': test.test_time and test.test_time <= timezone.now()
                    }
                })
            
            data.append(app_data)
        
        return Response({
            'status': 'success',
            'count': len(data),
            'applications': data
        })
        
    except Student.DoesNotExist:
        return Response(
            {'status': 'error', 'message': 'Student not found'},
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        return Response(
            {'status': 'error', 'message': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

# ---------- SHORTLIST ----------
@api_view(['GET'])
def view_result(request, student_id):
    student = Student.objects.get(id=student_id)
    return Response({
        'is_selected': student.is_selected,
        'admin_tips': student.admin_tips 
    })

# ---------- TEST SCHEDULE ----------
@api_view(['GET'])
def get_test_schedule(request, schedule_id):
    """
    Get a single test schedule by ID
    """
    try:
        test_schedule = TestSchedule.objects.get(id=schedule_id)
        serializer = TestScheduleSerializer(test_schedule)
        return Response(serializer.data)
    except TestSchedule.DoesNotExist:
        return Response(
            {'error': 'Test schedule not found'},
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@api_view(['POST'])
def schedule_test(request):
    """
    Schedule a test for a job application
    Required in request data: application_id, test_time, message (optional)
    """
    print("Received test schedule data:", request.data)
    
    try:
        application_id = request.data.get('application_id')
        test_time = request.data.get('test_time')
        duration_minutes = request.data.get('duration_minutes', 60)  # Default to 60 minutes if not provided
        message = request.data.get('message', '')
        
        if not application_id or not test_time:
            return Response(
                {'error': 'application_id and test_time are required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        
        try:
            duration_minutes = int(duration_minutes)
            if duration_minutes <= 0:
                raise ValueError("Duration must be positive")
        except (ValueError, TypeError):
            return Response(
                {'error': 'duration_minutes must be a positive number'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        application = get_object_or_404(JobApplication, id=application_id)
        
        if hasattr(application, 'test_schedule'):
            return Response(
                {'error': 'A test is already scheduled for this application'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        test_schedule_data = {
            'application': application.id,
            'test_time': test_time,
            'duration_minutes': duration_minutes,
            'message': message
        }
        
        serializer = TestScheduleSerializer(data=test_schedule_data)
        if not serializer.is_valid():
            print("Validation errors:", serializer.errors)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        test_schedule = serializer.save()
        
        application.status = 'test_scheduled'
        application.save()
        
        try:
            student = application.student
            job = application.job
            send_mail(
                'Test Scheduled',
                f"Your test for {job.title} is scheduled for {test_schedule.test_time}.\n\n"
                f"Message: {message or 'No additional message provided.'}",
                settings.DEFAULT_FROM_EMAIL,
                [student.email],
                fail_silently=False,
            )
        except Exception as e:
            print(f"Error sending email: {e}")
        
        return Response({
            'status': 'success',
            'message': 'Test scheduled successfully',
            'test_schedule_id': test_schedule.id,
            'test_time': test_schedule.test_time.isoformat(),
            'duration_minutes': test_schedule.duration_minutes,
            'application_id': application.id,
            'student_id': application.student.id,
            'job_id': application.job.id
        }, status=status.HTTP_201_CREATED)
        
    except Exception as e:
        print(f"Error in schedule_test: {str(e)}")
        return Response(
            {'error': 'An error occurred while scheduling the test', 'details': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )