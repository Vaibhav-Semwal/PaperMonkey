"""
Boots up just enough of Django so FastAPI can import and use Django's ORM
models (users.models.Profile) directly, without running a separate Django
server process. Django Admin still runs separately (manage.py runserver)
purely as an admin UI for managing roles.
"""
import os
import sys
import django

DJANGO_PROJECT_PATH = os.path.join(os.path.dirname(__file__), "..", "backend-django")
sys.path.insert(0, os.path.abspath(DJANGO_PROJECT_PATH))

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")
django.setup()
