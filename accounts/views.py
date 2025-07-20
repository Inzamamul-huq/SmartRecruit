from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login
from django.contrib.auth.hashers import make_password
from django.core.mail import send_mail
from django.views.decorators.csrf import csrf_exempt  # ✅ For CSRF disable


from .serializers import (
    RegisterSerializer,
    LoginSerializer,
    ForgotPasswordSerializer,
    OTPVerifySerializer,
    ResetPasswordSerializer,
)

import random


@csrf_exempt
@api_view(['POST'])
def register_user(request):
    serializer = RegisterSerializer(data=request.data)
    if serializer.is_valid():
        if User.objects.filter(username=serializer.validated_data['username']).exists():
            return Response({'error': 'Username already exists'}, status=status.HTTP_400_BAD_REQUEST)
        if User.objects.filter(email=serializer.validated_data['email']).exists():
            return Response({'error': 'Email already exists'}, status=status.HTTP_400_BAD_REQUEST)

        user = User.objects.create(
            username=serializer.validated_data['username'],
            email=serializer.validated_data['email'],
            password=make_password(serializer.validated_data['password'])
        )
        return Response({'message': 'User registered successfully'})
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@csrf_exempt
@api_view(['POST'])
def login_user(request):
    serializer = LoginSerializer(data=request.data)
    if serializer.is_valid():
        user = authenticate(
            username=serializer.validated_data['username'],
            password=serializer.validated_data['password']
        )
        if user:
            login(request, user)
            return Response({'message': 'Login successful'})
        return Response({'error': 'Invalid credentials'}, status=status.HTTP_401_UNAUTHORIZED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@csrf_exempt
@api_view(['POST'])
def login_admin(request):
    required_fields = ['email', 'password', 'secret_code']
    
    for field in required_fields:
        if field not in request.data:
            return Response({
                'error': f'Missing required field: {field}'
            }, status=status.HTTP_400_BAD_REQUEST)

    if (request.data['email'] == 'inzamulhuq1@gmail.com' and 
        request.data['password'] == 'password123' and 
        request.data['secret_code'] == 'secret123'):
        return Response({'message': 'Admin login successful'})
    
    return Response({'error': 'Invalid admin credentials'}, status=status.HTTP_401_UNAUTHORIZED)


from django.utils import timezone
from django.core.signing import Signer
from django.urls import reverse

from .models import PasswordResetToken

signer = Signer()

@csrf_exempt
@api_view(['POST'])
def forgot_password(request):
    serializer = ForgotPasswordSerializer(data=request.data)
    if serializer.is_valid():
        try:
            user = User.objects.get(email=serializer.validated_data['email'])
        except User.DoesNotExist:
            return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)

        # Generate a signed token
        token = signer.sign(str(user.id))
        
        # Create or update password reset token
        reset_token, created = PasswordResetToken.objects.update_or_create(
            user=user,
            defaults={'token': token, 'is_used': False}
        )
        
        reset_url = request.build_absolute_uri(reverse('reset_password', args=[token]))

        send_mail(
            'Smart Recruit Password Reset',
            f'Click the  link to reset your password:\n\n{reset_url}\n\nThis link will expire in 1 hour.',
            None,  
            [user.email],
        )
        return Response({'message': 'Reset link sent to email'})
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@csrf_exempt
@api_view(['GET'])
def reset_password(request, token):
    """
    Endpoint to handle password reset using a token from the reset link.
    The token is verified and if valid, returns a form to reset the password.
    """
    try:
        # Verify and unsign the token
        user_id = signer.unsign(token)
        user = User.objects.get(id=user_id)
        
        # Check if token exists and is valid
        reset_token = PasswordResetToken.objects.get(user=user, token=token)
        
        # Check if token is expired (1 hour)
        if timezone.now() - reset_token.created_at > timezone.timedelta(hours=1):
            reset_token.delete()
            return Response({'error': 'Reset link has expired'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Return success response with token
        return Response({
            'message': 'Token verified successfully',
            'token': token
        })
    except:
        return Response({'error': 'Invalid or expired reset link'}, status=status.HTTP_400_BAD_REQUEST)


@csrf_exempt
@api_view(['POST'])
def update_password(request):
    """
    Endpoint to update password after token verification
    """
    token = request.data.get('token')
    new_password = request.data.get('new_password')
    
    if not token or not new_password:
        return Response({'error': 'Token and new password are required'}, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        # Verify and unsign the token
        user_id = signer.unsign(token)
        user = User.objects.get(id=user_id)
        
        # Get and validate the reset token
        reset_token = PasswordResetToken.objects.get(user=user, token=token, is_used=False)
        
        # Update password
        user.password = make_password(new_password)
        user.save()
        
        # Mark token as used
        reset_token.is_used = True
        reset_token.save()
        
        return Response({'message': 'Password reset successful'})
    except:
        return Response({'error': 'Password reset failed'}, status=status.HTTP_400_BAD_REQUEST)
