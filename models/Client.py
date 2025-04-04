from sqlalchemy import (
    Column, 
    String, 
    Integer, 
    DateTime, 
    ForeignKey, 
    Boolean, 
    Float, 
    Date,
    Numeric,
)
from pytz import timezone
from sqlalchemy.orm import relationship
from models import Base
from models.ClientPayment import ClientPayment
from models.ClientOutlet import ClientOutlet
from models.Bpjs import Bpjs
from models.Allowances import Allowances
from models.ClientPayment import ClientPayment
from models.ContractClient import ContractClient
from models.TimeSheet import TimeSheet
from models.Performance import Performance
from models.Tax import Tax
from models.EmployeeAllowances import EmployeeAllowances
from models.BpjsEmployee import BpjsEmployee
from models.EmployeeTax import EmployeeTax

class Client(Base):
    __tablename__ = "client"

    id = Column(Integer, primary_key=True, nullable=False, index=True)
    name = Column(String, nullable=False, index=True)
    brand = Column(String, nullable=True)
    product_service = Column(String, nullable=True)
    npwp = Column(String, nullable=True)
    cs_person = Column(String, nullable=True)
    cs_number = Column(String, nullable=True)
    cs_email = Column(String, nullable=True)
    address = Column(String, nullable=True)
    website = Column(String, nullable=True)
    fee_agency = Column(Numeric(10, 6), nullable=True)
    basic_salary = Column(Numeric(10, 6), nullable=True)
    created_by = Column(String(36), nullable=True)
    updated_by = Column(String(36), nullable=True)
    created_at = Column(DateTime(timezone=True))
    updated_at = Column(DateTime(timezone=True))
    isact = Column(Boolean, default=True)
    payment_status = Column(Boolean, default=False)
    due_date_payment = Column(Date, nullable=True)
    id_client = Column(String, nullable=True, index=True)
    photo = Column(String, nullable=False)
    
    # Relation
    user_client = relationship("User", back_populates="client_user", primaryjoin="and_(User.client_id == Client.id, User.isact == True)")
    outlets = relationship("ClientOutlet", back_populates="client", primaryjoin="and_(ClientOutlet.client_id == Client.id, ClientOutlet.isact == True)")
    bpjs = relationship("Bpjs", back_populates="client", primaryjoin="and_(Bpjs.client_id == Client.id, Bpjs.isact == True)")
    allowances = relationship("Allowances", back_populates="client", primaryjoin="and_(Allowances.client_id == Client.id, Allowances.isact == True)")
    employee_allowances = relationship("EmployeeAllowances", back_populates="client", primaryjoin="and_(EmployeeAllowances.client_id == Client.id, EmployeeAllowances.isact == True)")
    employee_bpjs = relationship("BpjsEmployee", back_populates="client", primaryjoin="and_(BpjsEmployee.client_id == Client.id, BpjsEmployee.isact == True)")
    employee_tax = relationship("EmployeeTax", back_populates="client", primaryjoin="and_(EmployeeTax.client_id == Client.id, EmployeeTax.isact == True)")
    client_payments = relationship("ClientPayment", back_populates="clients")
    client_payroll = relationship("Payroll", back_populates="clients")
    contract_clients = relationship("ContractClient", back_populates="clients", 
                                    primaryjoin="and_(ContractClient.client_id == Client.id, ContractClient.isact == True)", 
                                    order_by="ContractClient.created_at")
    client_tax = relationship("Tax", back_populates="clients", primaryjoin="and_(Tax.client_id == Client.id, Tax.isact == True)")
    timesheet_client = relationship("TimeSheet", back_populates="clients")
    performance_client = relationship("Performance", back_populates="clients")

