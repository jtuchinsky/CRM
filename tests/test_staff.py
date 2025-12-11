"""Tests for Staff CRUD endpoints."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_create_staff(client: AsyncClient):
    """Test creating a new staff member."""
    staff_data = {
        "first_name": "Dr. Emily",
        "last_name": "Williams",
        "email": "emily.williams@clinic.com",
        "phone": "555-7001",
        "role": "Physician",
        "is_active": True,
    }
    response = await client.post("/api/v1/staff/", json=staff_data)
    assert response.status_code == 201
    data = response.json()
    assert data["first_name"] == "Dr. Emily"
    assert data["last_name"] == "Williams"
    assert data["email"] == "emily.williams@clinic.com"
    assert data["role"] == "Physician"
    assert data["is_active"] is True
    assert "id" in data
    assert "created_at" in data
    assert "updated_at" in data


@pytest.mark.asyncio
async def test_create_staff_invalid_email(client: AsyncClient):
    """Test creating staff with invalid email fails."""
    staff_data = {
        "first_name": "John",
        "last_name": "Doe",
        "email": "not-an-email",
        "role": "Nurse",
    }
    response = await client.post("/api/v1/staff/", json=staff_data)
    assert response.status_code == 422  # Validation error


@pytest.mark.asyncio
async def test_get_staff(client: AsyncClient):
    """Test retrieving a staff member by ID."""
    # Create staff first
    staff_data = {
        "first_name": "Jane",
        "last_name": "Smith",
        "email": "jane.smith@clinic.com",
        "role": "Doctor",
    }
    create_response = await client.post("/api/v1/staff/", json=staff_data)
    staff_id = create_response.json()["id"]

    # Get staff
    response = await client.get(f"/api/v1/staff/{staff_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == staff_id
    assert data["email"] == "jane.smith@clinic.com"


@pytest.mark.asyncio
async def test_get_staff_not_found(client: AsyncClient):
    """Test getting non-existent staff returns 404."""
    response = await client.get("/api/v1/staff/999")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_list_staff(client: AsyncClient):
    """Test listing all staff members."""
    # Create multiple staff
    staff_list = [
        {
            "first_name": "Alice",
            "last_name": "Johnson",
            "email": "alice@clinic.com",
            "role": "Nurse",
        },
        {
            "first_name": "Bob",
            "last_name": "Williams",
            "email": "bob@clinic.com",
            "role": "Doctor",
        },
    ]
    for staff in staff_list:
        await client.post("/api/v1/staff/", json=staff)

    # List all
    response = await client.get("/api/v1/staff/")
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 2


@pytest.mark.asyncio
async def test_list_staff_filter_by_active(client: AsyncClient):
    """Test filtering staff by active status."""
    # Create active and inactive staff
    await client.post(
        "/api/v1/staff/",
        json={
            "first_name": "Active",
            "last_name": "Staff",
            "email": "active@clinic.com",
            "role": "Nurse",
            "is_active": True,
        },
    )
    await client.post(
        "/api/v1/staff/",
        json={
            "first_name": "Inactive",
            "last_name": "Staff",
            "email": "inactive@clinic.com",
            "role": "Nurse",
            "is_active": False,
        },
    )

    # Filter by active
    response = await client.get("/api/v1/staff/?is_active=true")
    assert response.status_code == 200
    data = response.json()
    assert all(staff["is_active"] for staff in data)


@pytest.mark.asyncio
async def test_list_staff_filter_by_role(client: AsyncClient):
    """Test filtering staff by role."""
    # Create staff with different roles
    await client.post(
        "/api/v1/staff/",
        json={
            "first_name": "Doctor",
            "last_name": "One",
            "email": "doctor1@clinic.com",
            "role": "Physician",
        },
    )
    await client.post(
        "/api/v1/staff/",
        json={
            "first_name": "Nurse",
            "last_name": "One",
            "email": "nurse1@clinic.com",
            "role": "Nurse",
        },
    )

    # Filter by role
    response = await client.get("/api/v1/staff/?role=Physician")
    assert response.status_code == 200
    data = response.json()
    assert all(staff["role"] == "Physician" for staff in data)


@pytest.mark.asyncio
async def test_update_staff(client: AsyncClient):
    """Test updating staff member details."""
    # Create staff
    create_response = await client.post(
        "/api/v1/staff/",
        json={
            "first_name": "Update",
            "last_name": "Test",
            "email": "update@clinic.com",
            "phone": "555-0001",
            "role": "Nurse",
        },
    )
    staff_id = create_response.json()["id"]

    # Update phone and role
    update_data = {"phone": "555-0002", "role": "Senior Nurse"}
    response = await client.patch(f"/api/v1/staff/{staff_id}", json=update_data)
    assert response.status_code == 200
    data = response.json()
    assert data["phone"] == "555-0002"
    assert data["role"] == "Senior Nurse"
    assert data["email"] == "update@clinic.com"  # Unchanged


@pytest.mark.asyncio
async def test_update_staff_not_found(client: AsyncClient):
    """Test updating non-existent staff returns 404."""
    response = await client.patch("/api/v1/staff/999", json={"phone": "555-0000"})
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_delete_staff(client: AsyncClient):
    """Test deleting a staff member."""
    # Create staff
    create_response = await client.post(
        "/api/v1/staff/",
        json={
            "first_name": "Delete",
            "last_name": "Test",
            "email": "delete@clinic.com",
            "role": "Nurse",
        },
    )
    staff_id = create_response.json()["id"]

    # Delete
    response = await client.delete(f"/api/v1/staff/{staff_id}")
    assert response.status_code == 204

    # Verify deleted
    get_response = await client.get(f"/api/v1/staff/{staff_id}")
    assert get_response.status_code == 404


@pytest.mark.asyncio
async def test_delete_staff_not_found(client: AsyncClient):
    """Test deleting non-existent staff returns 404."""
    response = await client.delete("/api/v1/staff/999")
    assert response.status_code == 404
