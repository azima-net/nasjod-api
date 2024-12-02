import os
from django.http import JsonResponse
from django.conf import settings

def version(request):
    # Construct the full path to the version.txt file
    version_file_path = os.path.join(settings.BASE_DIR, 'version.txt')
    print(version_file_path)

    try:
        with open(version_file_path, 'r') as file:
            api_version = file.read().strip()
    except FileNotFoundError:
        api_version = 'Unknown'

    return JsonResponse({'version': api_version})
