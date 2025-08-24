from django.core.validators import RegexValidator
from django.utils.translation import gettext_lazy as _

# Email validation using regex
email_validator = RegexValidator(
    r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$',
    _('Enter a valid email address.'),
    'invalid_email'
)

# Password validation using regex
password_validator = RegexValidator(
    r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[!@#$%^&*()_+\-=[\]{};\\|,.<>/?]).{8,}$',
    _('Password must be at least 8 characters long and include uppercase, lowercase, number and special character.'),
    'invalid_password'
)


# Phone number validation
phone_validator = RegexValidator(
    r'^\+?1?\d{9,15}$',
    _('Enter a valid phone number (e.g., +1234567890). Up to 15 digits allowed.'),
    'invalid_phone'
)
