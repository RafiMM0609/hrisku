import calendar
from models import SessionLocal
from sqlalchemy import select, func, or_
from sqlalchemy.orm import Session, joinedload
from datetime import datetime, timedelta, date
from models.Client import Client
def get_days_in_month(year, month):
    return calendar.monthrange(year, month)[1]

# Contoh penggunaan
year = 2025
month = 4

days_in_month = get_days_in_month(year, month)
print(f"Bulan {month}/{year} memiliki {days_in_month} hari.")

# async def add_monthly_salary_emp(emp_id, client_id):
#     db = SessionLocal()
#     try:
#         # Fetch the end date of the contract from ContractClient
#         # contract = (
#         #     db.query(ContractClient)
#         #     .filter(ContractClient.client_id == client_id)
#         #     .order_by(ContractClient.end.desc())
#         #     .first()
#         # )
#         # if not contract or not contract.end:
#         #     raise ValueError("Contract end date not found for the given client.")

#         # date = contract.end_date  # Use the end date of the contract
#         date = datetime.now().date() + timedelta(days=30)  # Generate dummy date 30 days from today
        
#         # Query ClientPayment dengan eager loading untuk menghindari query tambahan
#         client = db.query(Client)\
#             .options(
#             joinedload(Client.client_tax),
#             joinedload(Client.allowances),
#             joinedload(Client.bpjs),
#             joinedload(Client.user_client)
#             )\
#             .filter(Client.isact == True, Client.id == client_id)\
#             .first()
#         # client = db.execute(query).scalar_one_or_none()
#         taxes = client.client_tax
#         allowances = client.allowances
#         bpjs_data = client.bpjs
#         # Initialize total nominal with basic salary
#         total_nominal = 0.00
#         basic_salary = client.basic_salary or 0.00
#         total_nominal += basic_salary

#         # Perhitungan pergaji karyawan

#         # Add BPJS
#         total_bpjs = 0.00
#         ls_bpjs = []
#         ls_allowances = []
#         for item in bpjs_data:
#             bpjs_amount = ((item.amount or 0) / 100) * basic_salary
#             ls_bpjs.append(
#                 {
#                     "name": item.name,
#                     "amount": bpjs_amount,
#                 }
#             )
#             total_bpjs += bpjs_amount
#             total_nominal += bpjs_amount

#         # Add Allowances
#         for item in allowances:
#             allowance_amount = item.amount or 0
#             ls_allowances.append(
#                 {
#                     "name": item.name,
#                     "amount": allowance_amount,
#                 }
#             )
#             total_nominal += allowance_amount

#         # Add tax
#         """
#         - Check dulu laporan gaji di tabel payroll sudah berapa
#         - Jika udah 11, maka yang ke 12 di tambahi tax buat laporan pajak
#         - Jika belum 11 maka biasa tanpa tax
#         - Tax nantinya tidak ikut dihitung, hanya ditambahkan di detail tax
#         - Untuk total payroll harusnya bulanan sama semua
#         """
#         total_taxes = 0.00
#         for tax in taxes:
#             tax_amount = ((tax.percent or 0) / 100) * basic_salary_in_period
#             total_taxes += tax_amount
#             total_nominal += tax_amount

#         # Grand Total
#         grand_total = total_nominal

#         # Check if data already exists
#         existing_payment = (
#             db.query(ClientPayment)
#             .filter(ClientPayment.client_id == client_id, ClientPayment.date == date)
#             .first()
#         )

#         if existing_payment:
#             # Update existing record
#             existing_payment.amount = grand_total
#         else:
#             # Add new record
#             new_payment = ClientPayment(
#                 client_id=client_id,
#                 date=date,
#                 amount=grand_total,
#                 status=1,
#             )
#             db.add(new_payment)

#         db.commit()
#         return "oke"
#     except Exception as e:
#         print("Error add client payment: \n", e)
#         raise ValueError("Failed to add client payment", e)
#     finally:
#         db.close()

