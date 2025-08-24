from rest_framework.decorators import api_view, permission_classes
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import get_user_model
from django.contrib.auth.models import User as DjangoUser  
from django.contrib.auth.hashers import check_password
from django.db import transaction
from accounts.models import AdminUser, Student
from .serializers import CustomTokenObtainPairSerializer, UserSerializer

User = get_user_model()

class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer

class LogoutView(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        try:
            refresh_token = request.data["refresh"]
            token = RefreshToken(refresh_token)
            token.blacklist()
            return Response(status=status.HTTP_205_RESET_CONTENT)
        except Exception as e:
            return Response(status=status.HTTP_400_BAD_REQUEST)

class UserProfileView(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        serializer = UserSerializer(request.user)
        return Response(serializer.data)


def _get_or_create_auth_user(email: str, is_staff: bool) -> DjangoUser:
    
    from django.utils import timezone
    user, created = DjangoUser.objects.get_or_create(
        username=email,
        defaults={
            'email': email,
            'is_staff': is_staff,
            'is_active': True,
            'last_login': timezone.now()
        }
    )
    
    if user.is_staff != is_staff:
        user.is_staff = is_staff
        user.save(update_fields=['is_staff'])
    return user

def _issue_tokens_response(user):
    
    refresh = RefreshToken.for_user(user)
    access = refresh.access_token
    return {
        'access': str(access),
        'refresh': str(refresh),
        'user': UserSerializer(user).data,
    }

@api_view(['POST'])
@permission_classes([AllowAny])
@transaction.atomic
def jwt_login(request):
    
    try:
        email = request.data.get('email') or request.data.get('username')
        password = request.data.get('password')

        if not email or not password:
            return Response(
                {'detail': 'Email and password are required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )

        
        admin = AdminUser.objects.filter(email=email).first()
        if admin and check_password(password, admin.password):
            user = _get_or_create_auth_user(email, is_staff=True)
            return Response(_issue_tokens_response(user))

       
        student = Student.objects.filter(email=email).first()
        if student:
            if not check_password(password, student.password):
                return Response(
                    {'detail': 'Invalid credentials'}, 
                    status=status.HTTP_401_UNAUTHORIZED
                )
            if student.allow != 'allow':
                return Response(
                    {'detail': 'Account not approved. Please wait for admin approval.'}, 
                    status=status.HTTP_403_FORBIDDEN
                )
            user = _get_or_create_auth_user(email, is_staff=False)
            return Response(_issue_tokens_response(user))

        return Response(
            {'detail': 'User not found'}, 
            status=status.HTTP_404_NOT_FOUND
        )

    except Exception as e:
        return Response(
            {'detail': 'An error occurred during login', 'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
