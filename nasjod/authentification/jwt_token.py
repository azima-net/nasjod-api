
from rest_framework_simplejwt.tokens import AccessToken

def generate_frontend_token():
    token = AccessToken()
    token['app'] = 'frontend'
    return str(token)
