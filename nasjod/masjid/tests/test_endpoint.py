import pytest
from django.urls import reverse
from rest_framework import status
from ..models import Masjid

@pytest.mark.django_db
def test_create_masjid(api_client, admin_user, masjid_payload):
    api_client.force_authenticate(user=admin_user)
    response = api_client.post(reverse('masjid-list'), masjid_payload, format='json')
    assert response.status_code == status.HTTP_201_CREATED
    assert 'uuid' in response.data
    assert 'name' in response.data
    assert response.data['name'] == masjid_payload['name']

@pytest.mark.django_db
def test_get_masjid(api_client, admin_user, masjid):
    api_client.force_authenticate(user=admin_user)
    url = reverse('masjid-detail', args=[masjid.uuid])
    response = api_client.get(url)
    assert response.status_code == status.HTTP_200_OK
    assert response.data['name'] == masjid.name

@pytest.mark.django_db
def test_partial_update_masjid(api_client, manager_user, masjid):
    api_client.force_authenticate(user=manager_user)
    masjid.managers.add(manager_user)
    update_data = {"name": "Updated Masjid"}
    url = reverse('masjid-detail', args=[masjid.uuid])
    response = api_client.patch(url, update_data)
    assert response.status_code == status.HTTP_200_OK
    masjid.refresh_from_db()
    assert masjid.name == "Updated Masjid"

@pytest.mark.django_db
def test_delete_masjid(api_client, admin_user, masjid):
    api_client.force_authenticate(user=admin_user)
    url = reverse('masjid-detail', args=[masjid.uuid])
    response = api_client.delete(url)
    assert response.status_code == status.HTTP_204_NO_CONTENT
    with pytest.raises(Masjid.DoesNotExist):
        Masjid.objects.get(uuid=masjid.uuid)
