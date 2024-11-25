from rest_framework.authentication import BaseAuthentication
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.exceptions import AuthenticationFailed
from jwt import decode as jwt_decode, InvalidTokenError
from django.conf import settings


class AppTokenAuthentication(BaseAuthentication):
    """
    Custom authentication for app-level tokens that do not require user validation.
    """
    def authenticate(self, request):
        # Extract the token from the Authorization header
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            return None  # No token provided, let other authenticators handle it

        token = auth_header.split(" ")[1]
        print(token)

        try:
            # Decode the token using the signing key and algorithm from SIMPLE_JWT settings
            decoded_token = jwt_decode(
                token,
                settings.SIMPLE_JWT['SIGNING_KEY'],
                algorithms=[settings.SIMPLE_JWT['ALGORITHM']]
            )

            # Check if the token contains the `app` claim
            app_name = decoded_token.get("app")
            if not app_name:
                raise AuthenticationFailed("Token is not valid for app authentication.")
            # Return None as the user object and decoded_token as auth info
            return (None, decoded_token)

        except InvalidTokenError:
            raise AuthenticationFailed("Invalid token.")
