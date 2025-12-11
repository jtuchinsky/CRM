"""Tests for Appointment CRUD endpoints."""

from datetime import datetime, timedelta

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_create_appointment(client: AsyncClient):
    """Test creating a new appointment."""
    # Create contact first
    contact_response = await client.post(
        "/api/v1/contacts/",
        json={
            "first_name": "John",
            "last_name": "Patient",
            "email": "john.patient@example.com",
            "phone": "555-0001",
        },
    )
    contact_id = contact_response.json()["id"]

    # Create staff
    staff_response = await client.post(
        "/api/v1/staff/",
        json={
            "first_name": "Dr. Sarah",
            "last_name": "Doctor",
            "email": "sarah.doctor@clinic.com",
            "role": "Physician",
        },
    )
    staff_id = staff_response.json()["id"]

    # Create appointment
    start_time = (datetime.now() + timedelta(days=1)).replace(microsecond=0)
    appointment_data = {
        "contact_id": contact_id,
        "staff_id": staff_id,
        "start_time": start_time.isoformat(),
        "duration_minutes": 60,
        "title": "Annual Checkup",
        "description": "Routine physical exam",
        "location": "Room 101",
    }
    response = await client.post("/api/v1/appointments/", json=appointment_data)
    assert response.status_code == 201
    data = response.json()
    assert data["contact_id"] == contact_id
    assert data["staff_id"] == staff_id
    assert data["duration_minutes"] == 60
    assert data["title"] == "Annual Checkup"
    assert data["status"] == "scheduled"
    assert "end_time" in data  # Automatically calculated
    assert "id" in data


@pytest.mark.asyncio
async def test_create_appointment_invalid_duration(client: AsyncClient):
    """Test creating appointment with invalid duration fails."""
    appointment_data = {
        "contact_id": 1,
        "staff_id": 1,
        "start_time": datetime.now().isoformat(),
        "duration_minutes": 500,  # Exceeds 480 max
        "title": "Test",
    }
    response = await client.post("/api/v1/appointments/", json=appointment_data)
    assert response.status_code == 422  # Validation error


@pytest.mark.asyncio
async def test_create_appointment_zero_duration(client: AsyncClient):
    """Test creating appointment with zero duration fails."""
    appointment_data = {
        "contact_id": 1,
        "staff_id": 1,
        "start_time": datetime.now().isoformat(),
        "duration_minutes": 0,
        "title": "Test",
    }
    response = await client.post("/api/v1/appointments/", json=appointment_data)
    assert response.status_code == 422  # Validation error


@pytest.mark.asyncio
async def test_get_appointment(client: AsyncClient):
    """Test retrieving an appointment by ID."""
    # Setup
    contact_response = await client.post(
        "/api/v1/contacts/",
        json={
            "first_name": "Get",
            "last_name": "Test",
            "email": "get.test@example.com",
        },
    )
    staff_response = await client.post(
        "/api/v1/staff/",
        json={
            "first_name": "Staff",
            "last_name": "Member",
            "email": "staff@clinic.com",
            "role": "Doctor",
        },
    )

    # Create appointment
    appointment_data = {
        "contact_id": contact_response.json()["id"],
        "staff_id": staff_response.json()["id"],
        "start_time": (datetime.now() + timedelta(days=2)).isoformat(),
        "duration_minutes": 30,
        "title": "Follow-up",
    }
    create_response = await client.post("/api/v1/appointments/", json=appointment_data)
    appointment_id = create_response.json()["id"]

    # Get appointment
    response = await client.get(f"/api/v1/appointments/{appointment_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == appointment_id
    assert data["title"] == "Follow-up"


@pytest.mark.asyncio
async def test_get_appointment_not_found(client: AsyncClient):
    """Test getting non-existent appointment returns 404."""
    response = await client.get("/api/v1/appointments/999")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_list_appointments(client: AsyncClient):
    """Test listing all appointments."""
    # Create test data
    contact = await client.post(
        "/api/v1/contacts/",
        json={"first_name": "List", "last_name": "Test", "email": "list@example.com"},
    )
    staff = await client.post(
        "/api/v1/staff/",
        json={
            "first_name": "List",
            "last_name": "Staff",
            "email": "list@clinic.com",
            "role": "Nurse",
        },
    )

    # Create multiple appointments
    for i in range(3):
        await client.post(
            "/api/v1/appointments/",
            json={
                "contact_id": contact.json()["id"],
                "staff_id": staff.json()["id"],
                "start_time": (datetime.now() + timedelta(days=i + 1)).isoformat(),
                "duration_minutes": 30,
                "title": f"Appointment {i+1}",
            },
        )

    # List all
    response = await client.get("/api/v1/appointments/")
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 3


@pytest.mark.asyncio
async def test_list_appointments_filter_by_contact(client: AsyncClient):
    """Test filtering appointments by contact."""
    # Create two contacts
    contact1 = await client.post(
        "/api/v1/contacts/",
        json={
            "first_name": "Contact",
            "last_name": "One",
            "email": "contact1@example.com",
        },
    )
    contact2 = await client.post(
        "/api/v1/contacts/",
        json={
            "first_name": "Contact",
            "last_name": "Two",
            "email": "contact2@example.com",
        },
    )
    staff = await client.post(
        "/api/v1/staff/",
        json={
            "first_name": "Filter",
            "last_name": "Staff",
            "email": "filter@clinic.com",
            "role": "Doctor",
        },
    )

    # Create appointments for both contacts
    await client.post(
        "/api/v1/appointments/",
        json={
            "contact_id": contact1.json()["id"],
            "staff_id": staff.json()["id"],
            "start_time": (datetime.now() + timedelta(days=1)).isoformat(),
            "duration_minutes": 30,
            "title": "Contact 1 Appointment",
        },
    )
    await client.post(
        "/api/v1/appointments/",
        json={
            "contact_id": contact2.json()["id"],
            "staff_id": staff.json()["id"],
            "start_time": (datetime.now() + timedelta(days=2)).isoformat(),
            "duration_minutes": 30,
            "title": "Contact 2 Appointment",
        },
    )

    # Filter by contact1
    response = await client.get(
        f"/api/v1/appointments/?contact_id={contact1.json()['id']}"
    )
    assert response.status_code == 200
    data = response.json()
    assert all(appt["contact_id"] == contact1.json()["id"] for appt in data)


@pytest.mark.asyncio
async def test_list_appointments_filter_by_staff(client: AsyncClient):
    """Test filtering appointments by staff."""
    contact = await client.post(
        "/api/v1/contacts/",
        json={
            "first_name": "Staff",
            "last_name": "Filter",
            "email": "stafffilter@example.com",
        },
    )
    staff1 = await client.post(
        "/api/v1/staff/",
        json={
            "first_name": "Staff",
            "last_name": "One",
            "email": "staff1@clinic.com",
            "role": "Doctor",
        },
    )
    staff2 = await client.post(
        "/api/v1/staff/",
        json={
            "first_name": "Staff",
            "last_name": "Two",
            "email": "staff2@clinic.com",
            "role": "Nurse",
        },
    )

    # Create appointments for both staff
    await client.post(
        "/api/v1/appointments/",
        json={
            "contact_id": contact.json()["id"],
            "staff_id": staff1.json()["id"],
            "start_time": (datetime.now() + timedelta(days=1)).isoformat(),
            "duration_minutes": 30,
            "title": "Staff 1 Appointment",
        },
    )
    await client.post(
        "/api/v1/appointments/",
        json={
            "contact_id": contact.json()["id"],
            "staff_id": staff2.json()["id"],
            "start_time": (datetime.now() + timedelta(days=2)).isoformat(),
            "duration_minutes": 30,
            "title": "Staff 2 Appointment",
        },
    )

    # Filter by staff1
    response = await client.get(
        f"/api/v1/appointments/?staff_id={staff1.json()['id']}"
    )
    assert response.status_code == 200
    data = response.json()
    assert all(appt["staff_id"] == staff1.json()["id"] for appt in data)


@pytest.mark.asyncio
async def test_list_appointments_filter_by_status(client: AsyncClient):
    """Test filtering appointments by status."""
    contact = await client.post(
        "/api/v1/contacts/",
        json={
            "first_name": "Status",
            "last_name": "Filter",
            "email": "statusfilter@example.com",
        },
    )
    staff = await client.post(
        "/api/v1/staff/",
        json={
            "first_name": "Status",
            "last_name": "Staff",
            "email": "status@clinic.com",
            "role": "Doctor",
        },
    )

    # Create appointment
    create_response = await client.post(
        "/api/v1/appointments/",
        json={
            "contact_id": contact.json()["id"],
            "staff_id": staff.json()["id"],
            "start_time": (datetime.now() + timedelta(days=1)).isoformat(),
            "duration_minutes": 30,
            "title": "Status Test",
        },
    )

    # Filter by scheduled status
    response = await client.get("/api/v1/appointments/?status=scheduled")
    assert response.status_code == 200
    data = response.json()
    assert all(appt["status"] == "scheduled" for appt in data)


@pytest.mark.asyncio
async def test_update_appointment_time(client: AsyncClient):
    """Test updating appointment time and duration."""
    # Setup
    contact = await client.post(
        "/api/v1/contacts/",
        json={
            "first_name": "Update",
            "last_name": "Time",
            "email": "updatetime@example.com",
        },
    )
    staff = await client.post(
        "/api/v1/staff/",
        json={
            "first_name": "Update",
            "last_name": "Staff",
            "email": "updatestaff@clinic.com",
            "role": "Doctor",
        },
    )

    # Create appointment
    original_start = datetime.now() + timedelta(days=1)
    create_response = await client.post(
        "/api/v1/appointments/",
        json={
            "contact_id": contact.json()["id"],
            "staff_id": staff.json()["id"],
            "start_time": original_start.isoformat(),
            "duration_minutes": 60,
            "title": "Original",
        },
    )
    appointment_id = create_response.json()["id"]

    # Update time and duration
    new_start = datetime.now() + timedelta(days=2)
    update_data = {"start_time": new_start.isoformat(), "duration_minutes": 90}
    response = await client.patch(
        f"/api/v1/appointments/{appointment_id}", json=update_data
    )
    assert response.status_code == 200
    data = response.json()
    assert data["duration_minutes"] == 90
    # end_time should be recalculated
    assert "end_time" in data


@pytest.mark.asyncio
async def test_update_appointment_status(client: AsyncClient):
    """Test updating appointment status."""
    # Setup
    contact = await client.post(
        "/api/v1/contacts/",
        json={
            "first_name": "Status",
            "last_name": "Update",
            "email": "statusupdate@example.com",
        },
    )
    staff = await client.post(
        "/api/v1/staff/",
        json={
            "first_name": "Status",
            "last_name": "Staff",
            "email": "statusstaff@clinic.com",
            "role": "Doctor",
        },
    )

    # Create appointment
    create_response = await client.post(
        "/api/v1/appointments/",
        json={
            "contact_id": contact.json()["id"],
            "staff_id": staff.json()["id"],
            "start_time": (datetime.now() + timedelta(days=1)).isoformat(),
            "duration_minutes": 30,
            "title": "Status Change",
        },
    )
    appointment_id = create_response.json()["id"]

    # Update status
    response = await client.patch(
        f"/api/v1/appointments/{appointment_id}", json={"status": "confirmed"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "confirmed"


@pytest.mark.asyncio
async def test_update_appointment_not_found(client: AsyncClient):
    """Test updating non-existent appointment returns 404."""
    response = await client.patch(
        "/api/v1/appointments/999", json={"title": "Updated"}
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_delete_appointment(client: AsyncClient):
    """Test deleting an appointment."""
    # Setup
    contact = await client.post(
        "/api/v1/contacts/",
        json={
            "first_name": "Delete",
            "last_name": "Test",
            "email": "delete@example.com",
        },
    )
    staff = await client.post(
        "/api/v1/staff/",
        json={
            "first_name": "Delete",
            "last_name": "Staff",
            "email": "deletestaff@clinic.com",
            "role": "Doctor",
        },
    )

    # Create appointment
    create_response = await client.post(
        "/api/v1/appointments/",
        json={
            "contact_id": contact.json()["id"],
            "staff_id": staff.json()["id"],
            "start_time": (datetime.now() + timedelta(days=1)).isoformat(),
            "duration_minutes": 30,
            "title": "To Delete",
        },
    )
    appointment_id = create_response.json()["id"]

    # Delete
    response = await client.delete(f"/api/v1/appointments/{appointment_id}")
    assert response.status_code == 204

    # Verify deleted
    get_response = await client.get(f"/api/v1/appointments/{appointment_id}")
    assert get_response.status_code == 404


@pytest.mark.asyncio
async def test_delete_appointment_not_found(client: AsyncClient):
    """Test deleting non-existent appointment returns 404."""
    response = await client.delete("/api/v1/appointments/999")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_appointment_end_time_calculation(client: AsyncClient):
    """Test that end_time is correctly calculated from start_time + duration."""
    # Setup
    contact = await client.post(
        "/api/v1/contacts/",
        json={
            "first_name": "EndTime",
            "last_name": "Test",
            "email": "endtime@example.com",
        },
    )
    staff = await client.post(
        "/api/v1/staff/",
        json={
            "first_name": "EndTime",
            "last_name": "Staff",
            "email": "endtimestaff@clinic.com",
            "role": "Doctor",
        },
    )

    # Create appointment with 90 minute duration
    start_time = datetime.now().replace(
        hour=10, minute=0, second=0, microsecond=0
    ) + timedelta(days=1)
    response = await client.post(
        "/api/v1/appointments/",
        json={
            "contact_id": contact.json()["id"],
            "staff_id": staff.json()["id"],
            "start_time": start_time.isoformat(),
            "duration_minutes": 90,
            "title": "End Time Test",
        },
    )
    assert response.status_code == 201
    data = response.json()

    # Parse times
    returned_start = datetime.fromisoformat(data["start_time"])
    returned_end = datetime.fromisoformat(data["end_time"])

    # Verify end_time = start_time + 90 minutes
    expected_end = start_time + timedelta(minutes=90)
    assert returned_end == expected_end
