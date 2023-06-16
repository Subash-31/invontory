from http.client import HTTPException
from idlelib.query import Query
from typing import Annotated, List
import os
import io
from openpyxl import Workbook
from fastapi_mail import FastMail, MessageType, MessageSchema, ConnectionConfig
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
from fastapi.security import OAuth2PasswordBearer
from fastapi_pagination import Page, add_pagination
from passlib.context import CryptContext
from sqlalchemy import select, func
from fastapi_pagination.ext.sqlalchemy import paginate
from datetime import date, time, timedelta, datetime
from fastapi import FastAPI, Depends, Response
from jupyter_client.session import Session
from pydantic import BaseModel, validator, EmailStr, Field, constr
from starlette import status
from models import Product, User, Orders, RagsInventory
import models
from database import engine, SessionLocal, Base
# email

from fastapi import FastAPI
from starlette.responses import JSONResponse
from fastapi_mail import FastMail, MessageSchema, ConnectionConfig, MessageType
from pydantic import EmailStr, BaseModel
from typing import List

from dotenv import dotenv_values

# credential
# creddentials = dotenv_values(".env")

# packages

app = FastAPI()

SECRET_KEY = '903rr5ui34t77gh3458wj423egyu6wee7t32yvr743t4ygtf7qw7we8324g3273r'
ALGORITHM = 'HS256'

SENDGRID_API_KEY = os.getenv("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")
SENDER_EMAIL = os.getenv("subash31jan@gmail.com")

models.Base.metadata.create_all(bind=engine)


class ProductEntry(BaseModel):
    product_name: str = Field(..., description="Name of the product")
    description: str = Field(..., description="product description")
    quantity: float = Field(..., description="Quantity of the product ")
    price: float = Field(..., description=" total Price of the product")
    Max_selling_price: float = Field(..., description="selling price of the total product")
    man_date: date = Field(..., description="Manufacture date in YYYY-MM-DD format")
    exp_date: date = Field(..., description="Expiration date in YYYY-MM-DD format")
    dealer_name: str = Field(..., description="Name of the dealer")
    dealer_mobile: int = Field(default=None, description="Dealer mobile number (optional)")
    product_code: str = Field(..., description="product code")

    @validator("man_date")
    def validate_man_date(cls, v):
        if v > date.today():
            raise ValueError("Manufacture date cannot be in the past")
        return v

    @validator("exp_date")
    def validate_exp_date(cls, v, values):
        if "man_date" in values and v <= values["man_date"]:
            raise ValueError("Expiration date must be after the manufacture date")
        return v


bcrypt_context = CryptContext(schemes='bcrypt', deprecated='auto')
oauth2_bearer = OAuth2PasswordBearer(tokenUrl='token')


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


db_dependency = Annotated[Session, Depends(get_db)]


################################################3


# @app.get("/get_all_products")
# async def read_all(db: db_dependency):
#     return db.query(Product).all()
@app.post("/enter_product", tags=["stock/product"], status_code=status.HTTP_201_CREATED)
async def product_entry(products_entry: ProductEntry, db: db_dependency):
    if db.query(Product).filter(Product.product_code == products_entry.product_code).first():
        return "product code exits"
        # raise HTTPException( status_code=400, detail="product code exits")

    if products_entry.quantity <= 0:
        return "quantity should be mininim "
        # raise HTTPException(status_code=400, detail="quantity should be mininim 1 ")

    if len(products_entry.description) <= 0:
        return "enter valid product description"
        # raise HTTPException(status_code=400, detail="enter valid product description ")

    if len(products_entry.dealer_name) <= 0:
        return "enter valid dealer name"
        # raise HTTPException(status_code=400, detail="enter valid dealer name ")

    individual_price = products_entry.price / products_entry.quantity

    stock = Product(
        product_name=products_entry.product_name,
        description=products_entry.description,
        quantity=products_entry.quantity,
        price=products_entry.price,
        sell_price=products_entry.Max_selling_price,
        man_date=products_entry.man_date,
        exp_date=products_entry.exp_date,
        dealer_mobile=products_entry.dealer_mobile,
        dealer_name=products_entry.dealer_name,
        product_code=products_entry.product_code,
        price_spec=individual_price
    )
    db.add(stock)
    db.commit()
    return " product added successfully "


class PaginationParams(BaseModel):
    offset: int = Field(0, description="Number of items to skip")
    limit: int = Field(10, description="Maximum number of items to retrieve")


@app.get("/get_all_productssss", tags=["stock/product"])
async def read_all(db: Session = Depends(get_db), pagination: PaginationParams = Depends()):
    products = db.query(Product).offset(pagination.offset).limit(pagination.limit).all()

    return products


@app.get("/products/summary", tags=["stock/product"])
def get_inventry_summary(db: db_dependency):
    summary = db.query(Product).all()

    total_stocks = db.query(Product).count()
    total_quantity = sum(summary.quantity for summary in summary)
    total_price = sum(summary.sell_price for summary in summary)

    result = {
        "Total_stocks": total_stocks,
        "Total_quantity": total_quantity,
        "Total_value": round(total_price, 2)
    }

    return result


@app.get("/product_details/{product_code_search}", tags=["stock/product"])
async def get_product(db: db_dependency, product_code_search: str):
    specfic_product = db.query(Product).filter(Product.product_code == product_code_search).first()

    if not specfic_product:
        return "product not exists"

    pervalue = specfic_product.price / specfic_product.quantity

    summary = {
        "Total quantity": specfic_product.quantity,
        "Total price": round(specfic_product.price, 3),
        " 1 product price": round(pervalue, 3),
        "expiry date": specfic_product.exp_date
    }

    return summary


##############-->


@app.get("/products/{id}/profit-loss", tags=["stock/product"])
def calculate_profit_loss(db: db_dependency, code: str):
    ps = db.query(Product).filter(code == Product.product_code).first()

    if ps is None:
        return {"message": "Product not found"}

    profit_loss = ps.sell_price - ps.price

    return {"profit loss": profit_loss,
            "product name": ps.product_name
            }


@app.get("/product by dealer /{dealers_name}", tags=["stock/product"])
def search_by_dealer(db: db_dependency, dealers_name: str):
    dea = db.query(Product).filter(dealers_name == Product.dealer_name).all()

    if dea is None:
        return {"message": "Dealer not found"}

    return dea


##############################################################


@app.get("/products/export", tags=["stock/product"])
def export_products(response: Response, db: db_dependency):
    products = db.query(Product).all()
    workbook = Workbook()
    sheet = workbook.active

    sheet.append(["Product Name", "Product Code", "Quantity", "Expiration Date"])

    for product in products:
        sheet.append([
            product.product_name, product.product_code, product.quantity, product.exp_date
        ])

    file_location = os.path.join(os.path.expanduser("~"), "Desktop", "checklist.xlsx")

    workbook.save(file_location)

    response.headers["Content-Disposition"] = "attachment; filename=product.xlsx"
    response.headers["Content-Type"] = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"

    response.body = open(file_location, "rb").read()
    response.headers["File-Path"] = file_location
    return " product check list excel sheet was generated and saved in device"


#################################################3
class update(BaseModel):
    code: str
    quantity_sales: float


@app.put('/update_product_quantity', tags=["stock/product"])
async def update_quantity(product_update: update, db: db_dependency):
    productq = db.query(Product).filter((Product.product_code == product_update.code)).first()

    # if productq.quantity < Product.quantity:
    #   raise HTTPException(status_code=400, detail="quantity should only redusable")

    if not productq:
        # raise HTTPException(status_code=404, detail='product not available  ;-)')
        return " product not found"

    if product_update.quantity_sales > productq.quantity:
        return " product quantity should not be incresable"

    new_value = productq.price - (productq.price_spec * product_update.quantity_sales)
    upquantity = productq.quantity - product_update.quantity_sales

    productq.quantity = upquantity
    productq.price = new_value

    db.commit()
    return " product quantity updated"


#################################################################
@app.delete("/product/{product_id}", tags=["stock/product"])
def delete_product(profile_id: int, db: db_dependency):
    user = db.query(Product).filter(Product.id == profile_id).first()
    db.delete(user)
    db.commit()
    return "product deleted"


###############################################################


@app.delete("/delete_stock/{product_code}", tags=["stock/product"])
def delete_product(product_code: str, db: db_dependency):
    pro = db.query(Product).filter(Product.product_code == product_code).first()

    if not pro:
        return "product not exists"

    db.delete(pro)
    db.commit()
    return "product deleted successfully"


#############################################3


class CreateUserRequest(BaseModel):
    first_name: str
    last_name: str
    user_name: str
    email: EmailStr
    pancard_id: str
    address: str
    dob: date
    mobile_no: str
    business_description: str
    annual_income: int
    password: str
    confirm_password: str

    @validator('pancard_id')
    def validate_pan_number(cls, pancard_id):
        if len(pancard_id) != 10:
            raise ValueError("Invalid PAN number")
        return pancard_id

    @validator('mobile_no')
    def validate_mobile_number(cls, mobile_no):
        if len(mobile_no) != 10:
            raise ValueError("Invalid mobile number")
        return mobile_no


class PaginationParams(BaseModel):
    offset: int = Field(0, description="Number of items to skip")
    limit: int = Field(10, description="Maximum number of items to retrieve")


@app.get("/get_all_users", tags=["User"])
async def read_all(db: Session = Depends(get_db), pagination: PaginationParams = Depends()):
    users = db.query(User).offset(pagination.offset).limit(pagination.limit).all()

    return users


@app.post("/create", status_code=status.HTTP_201_CREATED, tags=["User"])
async def create_user(db: db_dependency,
                      create_user_request: CreateUserRequest):
    if db.query(User).filter(User.user_name == create_user_request.user_name).first():
        # raise HTTPException(status_code=400, detail="Username already exists try different")
        return "username exists"
    if db.query(User).filter(User.email == create_user_request.email).first():
        # raise HTTPException(status_code=400, detail="Email already exists")
        return "email exists"
    if db.query(User).filter(User.mobile_no == create_user_request.mobile_no).first():
        return "mobile number exists"
    if db.query(User).filter(User.pancard_id == create_user_request.pancard_id).first():
        return " pancard number exists"
    if create_user_request.password != create_user_request.confirm_password:
        return " password and confirm password should be same "

    create_user_model = User(
        first_name=create_user_request.first_name,
        last_name=create_user_request.last_name,
        user_name=create_user_request.user_name,
        dob=create_user_request.dob,
        email=create_user_request.email,
        pancard_id=create_user_request.pancard_id,
        address=create_user_request.address,
        business_description=create_user_request.business_description,
        mobile_no=create_user_request.mobile_no,
        password=bcrypt_context.hash(create_user_request.password),
        annual_income=create_user_request.annual_income
    )
    db.add(create_user_model)
    db.commit()
    return " profile created "


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class EmailRequest(BaseModel):
    email_to: str
    subject: str
    content: str


@app.post("/send_email", tags=["User"])
def send_email(email: EmailRequest):
    message = Mail(
        from_email="subash31jan@gmail.com",
        to_emails=email.email_to,
        subject=email.subject,
        plain_text_content=email.content)

    try:
        sg = SendGridAPIClient(SENDGRID_API_KEY)
        response = sg.send(message)
        return {"message": "Email sent successfully"}
    except Exception as e:
        return {"message": "Failed to send email"}


class ChangePassword(BaseModel):
    username_or_email_or_regno: str
    current_password: str
    new_password: str


@app.put('/change_user_password', tags=["User"])
async def change_user_password(change_password: ChangePassword, db: db_dependency):
    user = db.query(User).filter(User.email == change_password.username_or_email_or_regno).first()

    is_password_valid = pwd_context.verify(change_password.current_password, bcrypt_context.hash(user.password))

    if not user or is_password_valid:
        return " user not found or invalid user"
    # raise HTTPException(status_code=404, detail='User not found or password invaild ;-)')

    new_password_hashed = bcrypt_context.hash(change_password.new_password)
    user.password = new_password_hashed
    db.commit()
    return {'message': 'Password changed successfully'}


class Delete(BaseModel):
    user_name: str
    password: str


@app.delete("/delete_user", tags=["User"])
def delete_profile(username: Delete, db: db_dependency):
    user = db.query(User).filter(User.user_name == username.user_name).first()

    if not user:
        return "user not exists"

    if not bcrypt_context.verify(username.password, user.password):
        return "incorrect password try again"

    db.delete(user)
    db.commit()
    return "profile deleted"



conf = ConnectionConfig(
    MAIL_USERNAME="subash31jan",
    MAIL_PASSWORD="(wordpass)",
    MAIL_FROM="subash31jan@yahoo.com",
    MAIL_PORT=587,
    MAIL_SERVER="smtp.mail.yahoo.com",
    MAIL_FROM_NAME="subash m",
    MAIL_STARTTLS=True,
    MAIL_SSL_TLS=False,
    USE_CREDENTIALS=True,
    VALIDATE_CERTS=True
)



class EmailInput(BaseModel):
    email_to: str
    subject: str
    message: str


@app.post("/send_email", tags=["Orders"])
async def send_email(email_input: EmailInput):
    message = MessageSchema(
        subject=email_input.subject,
        recipients=[email_input.to_address],
        body=email_input.message,
        subtype=MessageType.html
    )

    fm = FastMail(conf)
    await fm.send_message(message)
    return {"message": "Email has been sent successfully!"}


#
# class EmailSchema(BaseModel):
#     sender_email: EmailStr
#     subject: str
#     body: str
#     recipients: List[EmailStr]
#
#
# conf = ConnectionConfig(
#     MAIL_USERNAME="subash",
#     MAIL_PASSWORD="(wordpass)",
#     MAIL_FROM="subash31jan@gmail.com",
#     MAIL_PORT=587,
#     MAIL_SERVER="gmail server",
#     MAIL_FROM_NAME="Desired Name",
#     MAIL_STARTTLS=True,
#     MAIL_SSL_TLS=False,
#     USE_CREDENTIALS=True,
#     VALIDATE_CERTS=True
# )
#
#
#
# @app.post("/email")
# async def simple_send(email: EmailSchema) :
#
#     message = MessageSchema(
#         subject=email.subject,
#         recipients=email.recipients,
#         body=email.body,
#         subtype=MessageType.html,
#         sender=email.sender_email
#     )
#
#     fm = FastMail(conf)
#     await fm.send_message(message)
#     return "Email has been sent"


class OrderCreateRequest(BaseModel):
    user_email: EmailStr
    dealer_mail: EmailStr
    dealer_name: str
    stock_requesting_name: str
    stock_count: str
    address: str


@app.post("/orders", tags=["Orders"])
def create_order(order: OrderCreateRequest, db: db_dependency):
    user = db.query(User).filter(User.email == order.user_email).first()

    if not user:
        return "enter your user name correctly"

    new_order = Orders(
        dealer_mail=order.dealer_mail,
        user_id=user.id,
        dealer_name=order.dealer_name,
        stock_requesting_name=order.stock_requesting_name,
        stock_count=order.stock_count,
        address=order.address,
        date=datetime.today()

    )
    db.add(new_order)
    db.commit()
    db.refresh(new_order)
    return {"message": "Order created successfully", "order_id": new_order.id}


file_location = os.path.join(os.path.expanduser("~"), "Desktop", "orders1.xlsx")


@app.get("/ all_orders/", tags=["Orders"])
async def read_all(db: Session = Depends(get_db), pagination: PaginationParams = Depends()):
    order_list = db.query(Orders).offset(pagination.offset).limit(pagination.limit).all()

    return order_list


@app.get("/orders/export", tags=["Orders"])
def export_orders(response: Response, db: db_dependency):
    orders = db.query(Orders).all()
    workbook = Workbook()
    sheet = workbook.active
    sheet.append([
        "Order ID", "User ID", "Dealer Email", "Dealer Name", "Stock Name",
        "Stock Count", "Address", "Date Time"
    ])

    for order in orders:
        sheet.append([
            order.id, order.user_id, order.dealer_mail, order.dealer_name,
            order.stock_requesting_name, order.stock_count, order.address, order.date
        ])

    workbook.save(file_location)
    response.headers["Content-Disposition"] = f"attachment; filename=orders3.xlsx"
    response.headers["Content-Type"] = (
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
    response.body = open(file_location, "rb").read()
    response.headers["File-Path"] = file_location
    return " product check list excel sheet was generated and saved in device"


############################################################################################################################



class RagsInventoryCreate(BaseModel):
    rack_specific_name: str
    product_name: str
    quantity: float

@app.post('/rack_inventory', tags=['Rack_Inventory'])
def create_rag_entry(rack_data: RagsInventoryCreate):

    db = SessionLocal()
    new_rack_entry = RagsInventory(
        rag_specific_name=rack_data.rack_specific_name,
        product_name=rack_data.product_name,
        quantity=rack_data.quantity
    )

    db.add(new_rack_entry)
    db.commit()
    return "Rack created successfully"


@app.get("/rack/{specific_name}", tags=["Rack_Inventory"])
def get_product_by_rack_name(specific_name: str, db:db_dependency):
    rack = db.query(RagsInventory).filter(RagsInventory.rag_specific_name == specific_name).first()

    if not rack:
        return "Rack not found"

    return {
        "Product Name": rack.product_name,
        "Quantity": rack.quantity
    }



@app.get("/ all_rack_list/", tags=["Rack_Inventory"])
def read_all(db: Session = Depends(get_db), pagination: PaginationParams = Depends()):
    rack_list = db.query(RagsInventory).offset(pagination.offset).limit(pagination.limit).all()

    return rack_list

class request_update(BaseModel):
    rack_name:str
    prouct_name: str
    quantity_to_update:int



@app.put("/update_rack/",tags=["Rack_Inventory"])
def update(db:db_dependency,up:request_update):

    check = db.query(RagsInventory).filter(up.rack_name == RagsInventory.rag_specific_name).first()

    if not check:
        return "rack not found"


    check.quantity= up.quantity_to_update

    db.commit()
    return "updated successfully"

@app.delete("/rack_delete/{specific_name}", tags=["Rack_Inventory"])
def delete_rack(specific_name: str, db: db_dependency):
    rack = db.query(RagsInventory).filter(RagsInventory.rag_specific_name == specific_name).first()

    if not rack:
        return "Rack not found"

    db.delete(rack)
    db.commit()

    return "Rack deleted successfully"











