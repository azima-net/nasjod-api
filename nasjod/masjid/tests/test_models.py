import pytest
from datetime import date, time
from django.core.exceptions import ValidationError
from ..models import EidPrayerTime, JumuahPrayerTime, PrayerTime

@pytest.mark.django_db
def test_create_masjid(masjid):
    assert masjid.name == "Sakiet Eddayer Mosque"
    assert masjid.address.street == "Mahdia"
    assert masjid.address.city == "Sakiet Eddaier"
    assert masjid.address.state == "Sfax Governorate"
    assert masjid.address.zip_code == "3011"
    assert masjid.address.country == "Tunisia"
    assert masjid.address.coordinates.x == 10.780081214495699
    assert masjid.address.coordinates.y == 34.79051319533724
    assert masjid.telephone == ""
    assert masjid.size == 'L'
    assert masjid.parking is True
    assert masjid.disabled_access is True
    assert masjid.ablution_room is True
    assert masjid.woman_space is True
    assert masjid.adult_courses is False
    assert masjid.children_courses is False
    assert masjid.salat_al_eid is True
    assert masjid.salat_al_janaza is True
    assert masjid.iftar_ramadhan is True
    assert masjid.itikef is False

@pytest.mark.django_db
def test_add_manager(masjid, manager_user):
    masjid.managers.add(manager_user)
    assert manager_user in masjid.managers.all()

@pytest.mark.django_db
def test_add_assistant(masjid, assistant_user):
    masjid.assistants.add(assistant_user)
    assert assistant_user in masjid.assistants.all()

@pytest.mark.django_db
def test_validate_unique_roles(masjid, manager_user, assistant_user):
    masjid.managers.add(manager_user)
    with pytest.raises(ValidationError) as excinfo:
        masjid.assistants.add(manager_user)
    assert "A user cannot be both a manager and an assistant in the same masjid." in str(excinfo.value)

@pytest.mark.django_db
def test_prayer_time_creation(prayer_time):
    assert PrayerTime.objects.count() == 1
    assert prayer_time.masjid.name == "Sakiet Eddayer Mosque"
    assert prayer_time.fajr == time(4, 30)
    assert prayer_time.sunrise == time(6, 0)
    assert prayer_time.dhuhr == time(12, 0)
    assert prayer_time.asr == time(15, 30)
    assert prayer_time.maghrib == time(18, 45)
    assert prayer_time.isha == time(20, 0)

@pytest.mark.django_db
def test_unique_constraint(masjid):
    PrayerTime.objects.create(
        masjid=masjid,
        date=date(2023, 5, 30),
        fajr=time(4, 30),
        sunrise=time(6, 0),
        dhuhr=time(12, 0),
        asr=time(15, 30),
        maghrib=time(18, 45),
        isha=time(20, 0)
    )
    with pytest.raises(Exception):
        PrayerTime.objects.create(
            masjid=masjid,
            date=date(2023, 5, 30),
            fajr=time(4, 30),
            sunrise=time(6, 0),
            dhuhr=time(12, 0),
            asr=time(15, 30),
            maghrib=time(18, 45),
            isha=time(20, 0)
        )

@pytest.mark.django_db
def test_prayer_time_ordering(masjid):
    prayer_time1 = PrayerTime.objects.create(
        masjid=masjid,
        date=date(2023, 5, 29),
        fajr=time(4, 30),
        sunrise=time(6, 0),
        dhuhr=time(12, 0),
        asr=time(15, 30),
        maghrib=time(18, 45),
        isha=time(20, 0)
    )
    prayer_time2 = PrayerTime.objects.create(
        masjid=masjid,
        date=date(2023, 5, 30),
        fajr=time(4, 31),
        sunrise=time(6, 1),
        dhuhr=time(12, 1),
        asr=time(15, 31),
        maghrib=time(18, 46),
        isha=time(20, 1)
    )
    prayer_times = PrayerTime.objects.all()
    assert prayer_times[0] == prayer_time1
    assert prayer_times[1] == prayer_time2

@pytest.mark.django_db
def test_jumuah_prayer_time_creation(jumuah_prayer_time):
    assert JumuahPrayerTime.objects.count() == 1
    assert jumuah_prayer_time.masjid.name == "Sakiet Eddayer Mosque"
    assert jumuah_prayer_time.date == date(2023, 5, 30)
    assert jumuah_prayer_time.jumuah_time == time(13, 30)

@pytest.mark.django_db
def test_jumuah_unique_constraint(masjid):
    JumuahPrayerTime.objects.create(
        masjid=masjid,
        date=date(2023, 5, 30),
        jumuah_time=time(13, 30)
    )
    with pytest.raises(Exception):
        JumuahPrayerTime.objects.create(
            masjid=masjid,
            date=date(2023, 5, 30),
            jumuah_time=time(13, 30)
        )

@pytest.mark.django_db
def test_jumuah_prayer_time_ordering(masjid):
    jumuah1 = JumuahPrayerTime.objects.create(
        masjid=masjid,
        date=date(2023, 5, 29),
        jumuah_time=time(13, 30)
    )
    jumuah2 = JumuahPrayerTime.objects.create(
        masjid=masjid,
        date=date(2023, 5, 30),
        jumuah_time=time(13, 30)
    )
    jumuah_times = JumuahPrayerTime.objects.all()
    assert jumuah_times[0] == jumuah1
    assert jumuah_times[1] == jumuah2

@pytest.mark.django_db
def test_eid_prayer_time_creation(eid_prayer_time):
    assert EidPrayerTime.objects.count() == 1
    assert eid_prayer_time.masjid.name == "Sakiet Eddayer Mosque"
    assert eid_prayer_time.date == date(2023, 6, 1)
    assert eid_prayer_time.eid_time == time(8, 0)

@pytest.mark.django_db
def test_eid_unique_constraint(masjid):
    EidPrayerTime.objects.create(
        masjid=masjid,
        date=date(2023, 6, 1),
        eid_time=time(8, 0)
    )
    with pytest.raises(Exception):
        EidPrayerTime.objects.create(
            masjid=masjid,
            date=date(2023, 6, 1),
            eid_time=time(8, 0)
        )

@pytest.mark.django_db
def test_eid_prayer_time_ordering(masjid):
    eid1 = EidPrayerTime.objects.create(
        masjid=masjid,
        date=date(2023, 6, 1),
        eid_time=time(8, 0)
    )
    eid2 = EidPrayerTime.objects.create(
        masjid=masjid,
        date=date(2023, 6, 2),
        eid_time=time(8, 0)
    )
    eid_times = EidPrayerTime.objects.all()
    assert eid_times[0] == eid1
    assert eid_times[1] == eid2