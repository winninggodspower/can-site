import subprocess
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
import os

@csrf_exempt
def deploy(request):
    try:
        # Bash command: cd into project, activate venv, and run migration tasks
        commands = f"""
        cd {settings.PROJECT_PATH} &&
        source {settings.VENV_PATH} &&
        git pull &&
        pip install -r requirements.txt &&
        python manage.py makemigrations &&
        python manage.py migrate &&
        python manage.py collectstatic --noinput
        """
        
        output = subprocess.check_output(commands, shell=True, stderr=subprocess.STDOUT)
        return JsonResponse({'status': 'success', 'output': output.decode()})
    
    except subprocess.CalledProcessError as e:
        return JsonResponse({'status': 'error', 'output': e.output.decode()}, status=500)
