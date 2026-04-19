import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'snookernepal.settings')
django.setup()

from django.contrib.auth import get_user_model
User = get_user_model()

username = 'admin'
password = 'Admin@1234'

if User.objects.filter(username=username).exists():
    user = User.objects.get(username=username)
    user.set_password(password)
    user.save()
    print("Password reset successfully")
else:
    User.objects.create_superuser(username=username, password=password)
    print("Superuser created successfully")