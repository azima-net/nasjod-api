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

@pytest.fixture
def admin_user():
    user = User.objects.create_superuser(
        email='admin@example.com',
        password='adminpassword123'
    )
    return user

@pytest.fixture
def manager_user():
    user = User.objects.create_user(
        email='manager@example.com',
        username='manageruser',
        password='password123',
        first_name='Manager',
        last_name='User',
        sex='Male',
        birth_date='1980-01-01',
        phone_number='+21624000000',
        is_active=True,
        is_staff=False
    )
    return user

@pytest.fixture
def assistant_user():
    user = User.objects.create_user(
        email='assistant@example.com',
        username='assistantuser',
        password='password123',
        first_name='Assistant',
        last_name='User',
        sex='Male',
        birth_date='1990-01-01',
        phone_number='+21625000000',
        is_active=True,
        is_staff=False
    )
    return user

@pytest.fixture
def mousalli_user():
    user = User.objects.create_user(
        email='mousalli@example.com',
        username='mousalliuser',
        password='password123',
        first_name='Mousalli',
        last_name='User',
        sex='Male',
        birth_date='2000-01-01',
        phone_number='+21626000000',
        is_active=True,
        is_staff=False
    )
    return user

@pytest.fixture
def imam_user():
    user = User.objects.create_user(
        email='imam@example.com',
        username='imamuser',
        password='password123',
        first_name='Imam',
        last_name='User',
        sex='Male',
        birth_date='1970-01-01',
        phone_number='+21627000000',
        is_active=True,
        is_staff=False
    )
    return user
