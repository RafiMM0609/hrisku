import unittest
from unittest.mock import AsyncMock, MagicMock, patch
from sqlalchemy.orm import Session
from datetime import datetime
from schemas.talent_monitor import TalentMapping, TalentInformation, Organization
from repository.talent_monitor import data_talent_mapping, data_talent_information, list_talent

class TestTalentMonitor(unittest.IsolatedAsyncioTestCase):

    async def test_data_talent_mapping(self):
        # Mock database session
        mock_db = MagicMock(spec=Session)
        mock_user = MagicMock()
        mock_client = MagicMock()
        mock_client_outlet = MagicMock()
        mock_shift_schedule = MagicMock()

        # Mock query results
        mock_user.id_user = "123"
        mock_user.name = "John Doe"
        mock_user.birth_date = datetime(1990, 1, 1)
        mock_user.nik = "123456789"
        mock_user.email = "john.doe@example.com"
        mock_user.phone = "1234567890"
        mock_user.address = "123 Main St"
        mock_client.id = 1
        mock_client.name = "Client A"
        mock_client_outlet.id = 1
        mock_client_outlet.name = "Outlet A"
        mock_shift_schedule.id_shift = 1
        mock_shift_schedule.day = "Monday"
        mock_shift_schedule.time_start = datetime.strptime("08:00", "%H:%M")
        mock_shift_schedule.time_end = datetime.strptime("15:00", "%H:%M")
        mock_shift_schedule.workdays = 5

        # Mock database execution
        mock_db.execute.return_value.first.return_value = (
            mock_user, mock_client, mock_client.name, mock_client_outlet, mock_client_outlet.name
        )
        mock_db.execute.return_value.scalars.return_value.all.return_value = [mock_shift_schedule]

        # Call the function
        result = await data_talent_mapping(mock_db, "123")

        # Assertions
        self.assertIsInstance(result, TalentMapping)
        self.assertEqual(result.talent_id, "123")
        self.assertEqual(result.name, "John Doe")
        self.assertEqual(result.client.name, "Client A")
        self.assertEqual(result.outlet.name, "Outlet A")
        self.assertEqual(len(result.shift), 1)
        self.assertEqual(result.shift[0]["day"], "Monday")

    async def test_data_talent_information(self):
        # Mock database session
        mock_db = MagicMock(spec=Session)
        mock_user = MagicMock()

        # Mock query results
        mock_user.id_user = "123"
        mock_user.name = "John Doe"
        mock_user.birth_date = datetime(1990, 1, 1)
        mock_user.nik = "123456789"
        mock_user.email = "john.doe@example.com"
        mock_user.phone = "1234567890"
        mock_user.address = "123 Main St"
        mock_user.photo = "photo.jpg"
        mock_user.roles = [MagicMock(id=1, name="Role A")]

        # Mock database execution
        mock_db.execute.return_value.scalar_one_or_none.return_value = mock_user

        # Call the function
        result = await data_talent_information(mock_db, "123")

        # Assertions
        self.assertIsInstance(result, TalentInformation)
        self.assertEqual(result.talent_id, "123")
        self.assertEqual(result.name, "John Doe")
        self.assertEqual(result.role.name, "Role A")
        self.assertEqual(result.photo, "photo.jpg")

    async def test_list_talent(self):
        # Mock database session
        mock_db = MagicMock(spec=Session)
        mock_user = MagicMock()

        # Mock query results
        mock_user.id_user = "123"
        mock_user.name = "John Doe"
        mock_user.birth_date = datetime(1990, 1, 1)
        mock_user.nik = "123456789"
        mock_user.email = "john.doe@example.com"
        mock_user.phone = "1234567890"
        mock_user.address = "123 Main St"

        # Mock database execution
        mock_db.execute.return_value.all.return_value = [mock_user]
        mock_db.execute.return_value.scalar.return_value = 1

        # Call the function
        result, num_data, num_page = await list_talent(mock_db, 1, 10)

        # Assertions
        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["talend_id"], "123")
        self.assertEqual(num_data, 1)
        self.assertEqual(num_page, 1)

if __name__ == "__main__":
    unittest.main()