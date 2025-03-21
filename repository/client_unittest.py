import unittest
from unittest.mock import MagicMock, AsyncMock, patch
from datetime import datetime
from repository.client import (
    add_client,
    delete_client,
    create_custom_id,
    add_outlet,
    add_validator,
    edit_validator,
    edit_client,
    list_client,
    detail_client,
    formatin_detail,
)
from schemas.client import AddClientRequest, EditClientRequest
from models.Client import Client
from models.ClientOutlet import ClientOutlet
from models.Bpjs import Bpjs
from models.Allowances import Allowances


class TestClientRepository(unittest.IsolatedAsyncioTestCase):
    async def test_add_client_success(self):
        mock_db = MagicMock()
        mock_user = MagicMock()
        mock_user.id = 1
        mock_payload = AddClientRequest(
            photo="photo_url",
            name="Test Client",
            address="Test Address",
            agency_fee=1000,
            payment_date="01-01-2023",
            cs_person="CS Person",
            cs_number="123456789",
            cs_email="cs@test.com",
            basic_salary=5000,
            outlet=[],
            bpjs=[],
            allowences=[]
        )
        mock_background_tasks = MagicMock()

        mock_client = Client(
            id=1,
            id_client=None,
            photo=mock_payload.photo,
            name=mock_payload.name,
            address=mock_payload.address,
            fee_agency=mock_payload.agency_fee,
            due_date_payment=datetime.strptime(mock_payload.payment_date, "%d-%m-%Y").date(),
            cs_person=mock_payload.cs_person,
            cs_number=mock_payload.cs_number,
            cs_email=mock_payload.cs_email,
            basic_salary=mock_payload.basic_salary,
            created_at=datetime.now()
        )
        mock_db.refresh.return_value = mock_client

        with patch("repository.client.create_custom_id", new_callable=AsyncMock) as mock_create_custom_id:
            mock_create_custom_id.return_value = "C0001"

            result = await add_client(mock_db, mock_user, mock_payload, mock_background_tasks)

            mock_db.add.assert_called_once()
            mock_db.commit.assert_called()
            mock_db.refresh.assert_called_once_with(mock_client)
            mock_create_custom_id.assert_called_once_with(mock_client.id)
            self.assertEqual(result, mock_client)

    async def test_add_client_failure(self):
        mock_db = MagicMock()
        mock_user = MagicMock()
        mock_user.id = 1
        mock_payload = AddClientRequest(
            photo="photo_url",
            name="Test Client",
            address="Test Address",
            agency_fee=1000,
            payment_date="01-01-2023",
            cs_person="CS Person",
            cs_number="123456789",
            cs_email="cs@test.com",
            basic_salary=5000,
            outlet=[],
            bpjs=[],
            allowences=[]
        )
        mock_background_tasks = MagicMock()

        mock_db.commit.side_effect = Exception("Database error")

        with patch("repository.client.create_custom_id", new_callable=AsyncMock) as mock_create_custom_id:
            mock_create_custom_id.return_value = "C0001"

            with self.assertRaises(ValueError) as context:
                await add_client(mock_db, mock_user, mock_payload, mock_background_tasks)

            self.assertEqual(str(context.exception), "Database error")
            mock_db.add.assert_called_once()
            mock_db.commit.assert_called()

    async def test_delete_client_success(self):
        mock_db = MagicMock()
        mock_user = MagicMock()
        mock_user.id = 1
        mock_client = MagicMock()
        mock_db.execute.return_value.scalar.return_value = mock_client

        result = await delete_client(1, mock_db, mock_user)

        self.assertEqual(result, "oke")
        mock_db.add.assert_called_once_with(mock_client)
        mock_db.commit.assert_called_once()

    async def test_delete_client_not_found(self):
        mock_db = MagicMock()
        mock_user = MagicMock()
        mock_db.execute.return_value.scalar.return_value = None

        with self.assertRaises(ValueError) as context:
            await delete_client(1, mock_db, mock_user)

        self.assertEqual(str(context.exception), "Client not found")

    async def test_create_custom_id(self):
        result = await create_custom_id(1, prefix="C")
        self.assertEqual(result, "C01")

    async def test_add_outlet_success(self):
        mock_db = MagicMock()
        mock_outlets = [MagicMock(name="Outlet 1"), MagicMock(name="Outlet 2")]
        mock_client_id = 1

        with patch("repository.client.SessionLocal", return_value=mock_db):
            await add_outlet(mock_outlets, mock_client_id)

            mock_db.add.assert_called()
            mock_db.commit.assert_called()

    async def test_add_validator_success(self):
        mock_db = MagicMock()
        mock_payload = AddClientRequest(
            name="Test Client",
            cs_email="cs@test.com",
            cs_number="123456789",
            photo="photo_url",
            address="Test Address",
            agency_fee=1000,
            payment_date="01-01-2023",
            cs_person="CS Person",
            basic_salary=5000,
            outlet=[],
            bpjs=[],
            allowences=[]
        )
        mock_db.execute.return_value.fetchall.return_value = [(False, False, False)]

        result = await add_validator(mock_db, mock_payload)

        self.assertEqual(result, {"success": True})

    async def test_edit_validator_success(self):
        mock_db = MagicMock()
        mock_payload = AddClientRequest(
            name="Test Client",
            cs_email="cs@test.com",
            cs_number="123456789",
            photo="photo_url",
            address="Test Address",
            agency_fee=1000,
            payment_date="01-01-2023",
            cs_person="CS Person",
            basic_salary=5000,
            outlet=[],
            bpjs=[],
            allowences=[]
        )
        mock_db.execute.return_value.fetchall.return_value = [(False, False, False)]

        result = await edit_validator(mock_db, mock_payload, id="C01")

        self.assertEqual(result, {"success": True})

    async def test_list_client_success(self):
        mock_db = MagicMock()
        mock_clients = [MagicMock(id=1, name="Client 1"), MagicMock(id=2, name="Client 2")]
        mock_db.execute.return_value.scalars.return_value.all.return_value = mock_clients
        mock_db.execute.return_value.scalar.return_value = 2

        result, num_data, num_page = await list_client(mock_db, page=1, page_size=1)

        self.assertEqual(len(result), 2)
        self.assertEqual(num_data, 2)
        self.assertEqual(num_page, 2)

    async def test_detail_client_success(self):
        mock_db = MagicMock()
        mock_client = MagicMock(id=1, name="Client 1")
        mock_db.execute.return_value.scalar.return_value = mock_client

        result = await detail_client(mock_db, id=1)

        self.assertEqual(result.id, mock_client.id)

    async def test_formatin_detail_success(self):
        mock_client = MagicMock(id=1, name="Client 1", outlets=[], bpjs=[], allowances=[])
        result = await formatin_detail(mock_client)

        self.assertEqual(result.id, mock_client.id)


if __name__ == "__main__":
    unittest.main()