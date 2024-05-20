import pytest
from datetime import datetime
from django.core.exceptions import ValidationError


@pytest.mark.django_db
def test_create_user(user_model, user_data):
    user = user_model.objects.create_user(**user_data, password="password123")
    assert user.email == user_data['email']
    assert user.check_password("password123")

@pytest.mark.django_db
def test_create_superuser(user_model):
    superuser = user_model.objects.create_superuser(
        email="superuser@example.com",
        password="password123"
    )
    assert superuser.is_superuser
    assert superuser.is_staff
    assert superuser.check_password("password123")

@pytest.mark.django_db
def test_user_str(user):
    assert str(user) == user.email

@pytest.mark.django_db
def test_user_phone_number_validation(user_model, address):
    with pytest.raises(ValidationError) as excinfo:
        user = user_model.objects.create_user(
            username="invalidphoneuser",
            email="invalidphoneuser@example.com",
            sex="Male",
            birth_date=datetime(2000, 1, 1),
            first_name="Invalid",
            last_name="Phone",
            phone_number="123",  # Invalid phone number
            is_active=True,
            is_staff=False,
            address=address,
            password="password123"
        )
        user.full_clean()  # This will trigger the validation
    assert "Invalid phone number format" in str(excinfo.value)

@pytest.mark.django_db
def test_valid_phone_number(user_model, address):
    user = user_model.objects.create_user(
        username="validphoneuser",
        email="validphoneuser@example.com",
        sex="Male",
        birth_date=datetime(2000, 1, 1),
        first_name="Valid",
        last_name="Phone",
        phone_number="+21624123456",
        is_active=True,
        is_staff=False,
        address=address,
        password="password123"
    )
    user.full_clean()  # This will trigger the validation
    assert user.phone_number == "+21624123456"
