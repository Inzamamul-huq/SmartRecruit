from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from .views import LogoutView, jwt_login

urlpatterns = [
    path('login/', jwt_login, name='jwt_login'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('logout/', LogoutView.as_view(), name='auth_logout'),
]
