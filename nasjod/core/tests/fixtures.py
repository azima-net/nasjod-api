import pytest
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model
from core.models import Address

User = get_user_model()

# Common address fixture (can be overridden)
@pytest.fixture
def address():
    return Address.objects.create(
        street="123 Main St",
        city="Hometown",
        state="CA",
        zip_code="12345",
        country="USA",
        coordinates="POINT(-118.243683 34.052235)"
    )

# Common user fixture (can be overridden)
@pytest.fixture
def user():
    return User.objects.create_user(
        email='user@example.com',
        password='password123'
    )

# API client fixture
@pytest.fixture
def api_client():
    return APIClient()
