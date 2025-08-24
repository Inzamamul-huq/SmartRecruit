"""
WSGI config for smart_recruit project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.2/howto/deployment/wsgi/
"""

import os

from django.core.wsgi import get_wsgi_application

# Update this to use the correct module path
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'smart_recruit.settings')

application = get_wsgi_application()
