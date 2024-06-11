from core.tests.fixtures import *

import pytest
from datetime import datetime
from django.contrib.auth import get_user_model
from core.models import Address

User = get_user_model()

# Override or add additional fixtures specific to app1
@pytest.fixture
def user_model():
    return get_user_model()

@pytest.fixture
def user_data(address):
    return {
        "username": "testuser",
        "email": "testuser@example.com",
        "sex": "Male",
        "birth_date": datetime(2000, 1, 1),
        "first_name": "Test",
        "last_name": "User",
        "phone_number": "+21624123456",
        "is_active": True,
        "is_staff": False,
        "address": address,
    }

@pytest.fixture
def user(user_model, user_data):
    user = user_model.objects.create_user(
        **user_data
    )
    user.set_password("password123")
    user.save()
    return user

@pytest.fixture
def user_payload():
    return {
        "username": "testuser",
        "email": "testuser@example.com",
        "sex": "Male",
        "birth_date": "2000-01-01",
        "first_name": "Test",
        "last_name": "User",
        "phone_number": "+21624123456",
        "password": "password123",
        "confirm_password": "password123"
    }
