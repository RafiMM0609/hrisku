import pytest
from unittest.mock import AsyncMock, MagicMock
from datetime import datetime
from sqlalchemy.orm import Session
from repository.talent_mapping import (
    map_shift_to_calendar,
    ViewTalentData,
    add_user_validator,
    add_talent,
    create_custom_id,
)

@pytest.mark.asyncio
async def test_map_shift_to_calendar():
    db = MagicMock(spec=Session)
    emp_id = "123"
    start_time = "09:00"
    end_time = "17:00"
    day = "Monday"

    shifts = await map_shift_to_calendar(emp_id, start_time, end_time, day, db)

    assert len(shifts) == 10
    assert shifts[0]["id"] == emp_id
    assert shifts[0]["day"] == day
    assert "start" in shifts[0]
    assert "end" in shifts[0]

@pytest.mark.asyncio
async def test_view_talent_data(mocker):
    db = mocker.MagicMock(spec=Session)
    db.execute.return_value.one_or_none.return_value = None

    with pytest.raises(ValueError, match="Talent not found"):
        await ViewTalentData(db, "nonexistent_id")

    db.execute.assert_called_once()

@pytest.mark.asyncio
@pytest.mark.parametrize(
    "outlet_exists, email_exists, client_exists, expected_success, expected_error",
    [
        (True, False, True, True, None),  # Valid case
        (False, False, True, False, "Outlet not valid"),  # Invalid outlet
        (True, True, True, False, "Email already exists"),  # Duplicate email
        (True, False, False, False, "Client not found"),  # Invalid client
    ],
)
async def test_add_user_validator(mocker, outlet_exists, email_exists, client_exists, expected_success, expected_error):
    db = mocker.MagicMock(spec=Session)
    payload = MagicMock(outlet_id=1, client_id=1, email="test@example.com")
    db.execute.return_value.fetchall.return_value = [[outlet_exists, email_exists, client_exists]]

    result = await add_user_validator(db, payload)

    assert result["success"] == expected_success
    assert result.get("errors") == expected_error

@pytest.mark.asyncio
async def test_add_talent(mocker):
    db = mocker.MagicMock(spec=Session)
    user = MagicMock()
    background_tasks = mocker.MagicMock()
    payload = MagicMock(
        photo="photo.jpg",
        name="John Doe",
        dob="01-01-1990",
        nik="123456789",
        outlet_id=1,
        email="test@example.com",
        phone="1234567890",
        address="123 Street",
        client_id=1,
        shift=[],
        contract=None,
    )

    await add_talent(db, user, background_tasks, payload)

    db.add.assert_called_once()
    db.commit.assert_called()
    background_tasks.add_task.assert_any_call(mocker.ANY, mocker.ANY, payload.contract)

@pytest.mark.asyncio
@pytest.mark.parametrize(
    "id, prefix, expected_id",
    [
        (123, "T", "T0123"),  # Default prefix
        (45, "EMP", "EMP045"),  # Custom prefix
        (7, None, "T07"),  # Default prefix with single-digit ID
    ],
)
async def test_create_custom_id(id, prefix, expected_id):
    result = await create_custom_id(id, prefix)
    assert result == expected_id
