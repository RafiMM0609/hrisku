import calendar
from models import SessionLocal
from sqlalchemy import select, func, or_
from sqlalchemy.orm import Session, joinedload
from datetime import datetime, timedelta, date
from models.Client import Client
from models.Payroll import Payroll
from models.EmployeeAllowances import EmployeeAllowances
from models.EmployeeTax import EmployeeTax
from models.BpjsEmployee import BpjsEmployee

def get_days_in_month(year, month):
    return calendar.monthrange(year, month)[1]

# # Contoh penggunaan
# year = 2025
# month = 4

# days_in_month = get_days_in_month(year, month)
# print(f"Bulan {month}/{year} memiliki {days_in_month} hari.")

async def add_monthly_salary_emp(emp_id, client_id):
    db = SessionLocal()
    try:
        # Fetch the end date of the contract from ContractClient
        # contract = (
        #     db.query(ContractClient)
        #     .filter(ContractClient.client_id == client_id)
        #     .order_by(ContractClient.end.desc())
        #     .first()
        # )
        # if not contract or not contract.end:
        #     raise ValueError("Contract end date not found for the given client.")
        
        # Data preparation
        start_of_year = date(date.today().year, 1, 1)
        end_of_year = date(date.today().year, 12, 31)

        # Calculate the start and end of the current month
        start_of_month = datetime(datetime.now().year, datetime.now().month, 1)
        end_of_month = datetime(datetime.now().year, datetime.now().month, calendar.monthrange(datetime.now().year, datetime.now().month)[1])
        # Payment_date
        payment_date = end_of_month - timedelta(days=1)  # Generate dummy date 30 days from today
        
        # Query ClientPayment dengan eager loading untuk menghindari query tambahan
        client = db.query(Client)\
            .options(
            joinedload(Client.client_tax),
            joinedload(Client.allowances),
            joinedload(Client.bpjs),
            joinedload(Client.user_client)
            )\
            .filter(Client.isact == True, Client.id == client_id)\
            .first()
        # client = db.execute(query).scalar_one_or_none()
        taxes = client.client_tax
        allowances = client.allowances
        bpjs_data = client.bpjs
        # Initialize total nominal with basic salary
        total_nominal = 0.00
        basic_salary = client.basic_salary or 0.00
        total_nominal += basic_salary

        # Perhitungan pergaji karyawan

        # Add BPJS
        ls_bpjs = []
        ls_allowances = []
        ls_tax = []
        total_bpjs = 0.00
        total_allowances = 0.00
        total_tax = 0.00

        # Add BPJS
        for item in bpjs_data:
            bpjs_amount = ((item.amount or 0) / 100) * basic_salary
            ls_bpjs.append(
                {
                    "name": item.name,
                    "amount": bpjs_amount,
                }
            )
            total_bpjs += bpjs_amount

        # Add Allowances
        for item in allowances:
            allowance_amount = item.amount or 0
            ls_allowances.append(
                {
                    "name": item.name,
                    "amount": allowance_amount,
                }
            )
            total_allowances += allowance_amount
            total_nominal += allowance_amount

        # Hitung total gaji dalam seperiode
        count_payroll = db.execute(
            select(func.count(Payroll.id))
            .filter(
                Payroll.client_id == client_id,
                Payroll.emp_id == emp_id,
                Payroll.isact == True,
                Payroll.payment_date.between(start_of_year, end_of_year),  # Updated filter
            )
        ).scalar()
        if count_payroll >= 11:
            # Add tax
            for item in taxes:
                tax_amount = ((item.percent or 0) / 100) * (basic_salary * 12)
                ls_tax.append(
                    {
                        "name": item.name,
                        "amount": tax_amount,
                    }
                )

        # Check payroll bulan ini sudah ada belum
        exist_payroll = db.query(Payroll)\
            .filter(
                Payroll.emp_id==emp_id, 
                Payroll.isact==True,
                Payroll.payment_date.between(start_of_month, end_of_month)  # Updated filter
                )\
            .first()

        # Count net sallary
        net_salary = total_nominal - total_bpjs

        # Add or update allowances record
        for item in ls_allowances:
            existing_allowance = db.query(EmployeeAllowances)\
                .filter(
                    EmployeeAllowances.client_id == client_id,
                    EmployeeAllowances.emp_id == emp_id,
                    EmployeeAllowances.name == item["name"],
                    func.date(EmployeeAllowances.created_at) >= start_of_month.date(),
                    func.date(EmployeeAllowances.created_at) <= end_of_month.date()
                ).first()
            if existing_allowance:
                existing_allowance.amount = item["amount"]
                existing_allowance.created_at = datetime.now()
                db.add(existing_allowance)
            else:
                new_allowance = EmployeeAllowances(
                    client_id=client_id,
                    emp_id=emp_id,
                    name=item["name"],
                    amount=item["amount"],
                    created_at=datetime.now(),
                )
                db.add(new_allowance)

        # Add or update BPJS record
        for item in ls_bpjs:
            existing_bpjs = db.query(BpjsEmployee)\
                .filter(
                    BpjsEmployee.client_id == client_id,
                    BpjsEmployee.emp_id == emp_id,
                    BpjsEmployee.name == item["name"],
                    func.date(BpjsEmployee.created_at) >= start_of_month.date(),
                    func.date(BpjsEmployee.created_at) <= end_of_month.date()
                ).first()
            if existing_bpjs:
                existing_bpjs.amount = item["amount"]
                existing_bpjs.created_at = datetime.now()
                db.add(existing_bpjs)
            else:
                new_bpjs = BpjsEmployee(
                    client_id=client_id,
                    emp_id=emp_id,
                    name=item["name"],
                    amount=item["amount"],
                    created_at=datetime.now(),
                )
                db.add(new_bpjs)

        # Add or update tax record
        for item in ls_tax:
            existing_tax = db.query(EmployeeTax)\
                .filter(
                    EmployeeTax.client_id == client_id,
                    EmployeeTax.emp_id == emp_id,
                    EmployeeTax.name == item["name"],
                    func.date(EmployeeTax.created_at) >= start_of_month.date(),
                    func.date(EmployeeTax.created_at) <= end_of_month.date()
                ).first()
            if existing_tax:
                existing_tax.amount = item["amount"]
                existing_tax.created_at = datetime.now()
                db.add(existing_tax)
            else:
                new_tax = EmployeeTax(
                    client_id=client_id,
                    emp_id=emp_id,
                    name=item["name"],
                    amount=item["amount"],
                    created_at=datetime.now(),
                )
                db.add(new_tax)

        if exist_payroll:
            exist_payroll.monthly_paid = basic_salary
            exist_payroll.payment_date = payment_date
            exist_payroll.total_allowances = total_allowances
            exist_payroll.total_bpjs = total_bpjs
            exist_payroll.total_tax = total_tax
            exist_payroll.net_salary = net_salary
            db.add(exist_payroll)
        else:
            # Add new payroll record
            new_payment = Payroll(
                client_id=client_id,
                emp_id=emp_id,
                monthly_paid=basic_salary,
                payment_date=payment_date,
                total_allowances=total_allowances,
                total_bpjs=total_bpjs,
                total_tax=total_tax,
                net_salary=net_salary,
            )
            db.add(new_payment)
        db.commit()
        return "oke"
    except Exception as e:
        print("Error add user payroll: \n", e)
        raise ValueError("Failed to add user payroll: \n", e)
    finally:
        db.close()

