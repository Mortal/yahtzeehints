"""
WSGI config for yahtzeehints project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/2.2/howto/deployment/wsgi/
"""

import os
import yahtzeevalue

from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'yahtzeehints.settings')

application = get_wsgi_application()

from django.conf import settings

inner_get_response = application.get_response

db_wrapper = yahtzeevalue.Database(settings.YAHTZEE_PATH)
db = db_wrapper.__enter__()

def get_response(request):
    request.yahtzeevalue = db
    return inner_get_response(request)

application.get_response = get_response
