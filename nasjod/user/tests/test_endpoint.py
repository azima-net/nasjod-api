# users/tests/test_views.py
import pytest
from django.urls import reverse
from rest_framework import status
from django.contrib.auth import get_user_model

User = get_user_model()

@pytest.mark.django_db
def test_create_user(api_client, admin_user, user_payload):
    api_client.force_authenticate(user=admin_user)
    response = api_client.post(reverse('user-list'), user_payload)
    assert response.status_code == status.HTTP_201_CREATED
    assert 'id' in response.data
    assert 'password' not in response.data

@pytest.mark.django_db
def test_create_user_password_mismatch(api_client, admin_user, user_payload):
    api_client.force_authenticate(user=admin_user)
    user_payload["confirm_password"] = "wrongpassword"
    response = api_client.post(reverse('user-list'), user_payload)
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.data == {"password": ["Passwords must match."]}

@pytest.mark.django_db
def test_get_user(api_client, admin_user, user):
    api_client.force_authenticate(user=admin_user)
    response = api_client.get(reverse('user-detail', args=[user.identifier]))
    assert response.status_code == status.HTTP_200_OK
    assert response.data["email"] == user.email

@pytest.mark.django_db
def test_partial_update_user(api_client, admin_user, user):
    api_client.force_authenticate(user=admin_user)
    update_data = {
        "first_name": "PartiallyUpdated",
        "last_name": "User",
        "password": "newpassword123",
        "confirm_password": "newpassword123"
    }
    response = api_client.patch(reverse('user-detail', args=[user.identifier]), update_data)
    assert response.status_code == status.HTTP_200_OK
    user.refresh_from_db()
    assert user.check_password("newpassword123")
    assert user.first_name == "PartiallyUpdated"
    assert user.last_name == "User"

@pytest.mark.django_db
def test_delete_user(api_client, admin_user, user):
    api_client.force_authenticate(user=admin_user)
    response = api_client.delete(reverse('user-detail', args=[user.identifier]))
    assert response.status_code == status.HTTP_204_NO_CONTENT
    with pytest.raises(User.DoesNotExist):
        User.objects.get(id=user.id)
