from datetime import date
from database import Base
from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, Date, Float, func,DateTime


class Product(Base):
    __tablename__ ='product'

    id = Column(Integer, primary_key=True, index=True)
    #user_id = Column(Integer, ForeignKey('User.id'))
    product_name = Column(String)
    description = Column(String)
    quantity = Column(Float)
    price = Column(Float)
    sell_price = Column(Float)
    man_date = Column(Date)
    exp_date = Column(Date)
    stock_entry_date = Column(Date, default=date.today)
    dealer_name = Column(String)
    dealer_mobile = Column(Integer)
    product_code = Column(String, unique=True)
    price_spec = Column(Float)

class User(Base):
    __tablename__ ='users'

    id = Column(Integer, primary_key=True, index=True)
    user_name = Column(String,unique=True)
    first_name = Column(String)
    last_name = Column(String)
    pancard_id = Column(String)
    address = Column(String)
    mobile_no = Column(String,unique=True)
    email = Column(String,unique=True)
    business_description = Column(String)
    annual_income = Column(Integer)
    dob = Column(Date)
    password =Column(String)

class Orders(Base):
    __tablename__ = 'orders'

    id = Column(Integer, primary_key=True,index=True)
    user_id = Column(Integer)
    dealer_mail = Column(String)
    dealer_name= Column(String)
    stock_requesting_name = Column(String)
    stock_count = Column(String)
    address = Column(String)
    date = Column(DateTime)


class RagsInventory(Base):
    __tablename__ = 'ragsinventory'

    id = Column(Integer, primary_key=True)
    rag_specific_name = Column(String)
    product_name = Column(String)
    quantity = Column(Integer or Float)