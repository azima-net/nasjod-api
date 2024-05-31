from datetime import date, time
from core.tests.fixtures import *

import pytest
from django.contrib.auth import get_user_model

from core.models import Address
from ..models import EidPrayerTime, JumuahPrayerTime, Masjid, PrayerTime

User = get_user_model()

# Override or add additional fixtures specific to app2
@pytest.fixture
def address():
    return Address.objects.create(
        street="Mahdia",
        city="Sakiet Eddaier",
        state="Sfax Governorate",
        zip_code="3011",
        country="Tunisia",
        coordinates="POINT (10.780081214495699 34.79051319533724)"
    )

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
        is_staff=True
    )
    return user

@pytest.fixture
def assistant_user():
    return User.objects.create_user(
        email='assistant@example.com',
        password='password123'
    )

@pytest.fixture
def masjid_payload():
    return {
        "name": "Sakiet Eddayer Mosque",
        "address": {
            "street": "Mahdia",
            "city": "Sakiet Eddaier",
            "state": "Sfax Governorate",
            "zip_code": "3011",
            "country": "Tunisia",
            "coordinates": "POINT(10.780081214495699 34.79051319533724)"
        },
        "telephone": "",
        "photo": None,
        "cover": None,
        "size": "L",
        "parking": True,
        "disabled_access": True,
        "ablution_room": True,
        "woman_space": True,
        "adult_courses": False,
        "children_courses": False,
        "salat_al_eid": True,
        "salat_al_janaza": True,
        "iftar_ramadhan": True,
        "itikef": False
    }

@pytest.fixture
def masjid(address):
    return Masjid.objects.create(
        name="Sakiet Eddayer Mosque",
        address=address,
        telephone="",
        photo=None,
        cover=None,
        size='L',
        parking=True,
        disabled_access=True,
        ablution_room=True,
        woman_space=True,
        adult_courses=False,
        children_courses=False,
        salat_al_eid=True,
        salat_al_janaza=True,
        iftar_ramadhan=True,
        itikef=False
    )

@pytest.fixture
def prayer_time(masjid):
    return PrayerTime.objects.create(
        masjid=masjid,
        date=date(2023, 5, 30),
        fajr=time(4, 30),
        sunrise=time(6, 0),
        dhuhr=time(12, 0),
        asr=time(15, 30),
        maghrib=time(18, 45),
        isha=time(20, 0)
    )

@pytest.fixture
def jumuah_prayer_time(masjid):
    return JumuahPrayerTime.objects.create(
        masjid=masjid,
        date=date(2023, 5, 30),
        jumuah_time=time(13, 30)
    )

@pytest.fixture
def eid_prayer_time(masjid):
    return EidPrayerTime.objects.create(
        masjid=masjid,
        date=date(2023, 6, 1),
        eid_time=time(8, 0)
    )
