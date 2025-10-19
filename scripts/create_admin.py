import os
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.append(str(BASE_DIR))

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "erms_project.settings")

import django

django.setup()

from django.contrib.auth import get_user_model

User = get_user_model()
USERNAME = "admin"
EMAIL = "admin@example.com"
PASSWORD = "AdminPass123!"

user, created = User.objects.get_or_create(
    username=USERNAME,
    defaults={"email": EMAIL}
)
if created:
    user.set_password(PASSWORD)
    user.is_staff = True
    user.is_superuser = True
    user.save()
    print("Admin user created.")
else:
    if user.is_superuser:
        print("Admin user already exists.")
    else:
        user.email = EMAIL
        user.is_staff = True
        user.is_superuser = True
        user.set_password(PASSWORD)
        user.save()
        print("Existing user promoted to superuser.")
