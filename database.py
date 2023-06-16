
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base

#SQLALCHEMY_DATABASE_URL = 'sqlite:///./inventory.db' #sqlite
#SQLALCHEMY_DATABASE_URL = "postgresql://postgres:(wordpass)@localhost/new" #postgresadmin
SQLALCHEMY_DATABASE_URL = 'postgresql://qpnvrjcb:PMLCYD_yLJIKd4j7-xlIKB17JkXUJ6P7@chunee.db.elephantsql.com/qpnvrjcb' #online

#engine = create_engine(SQLALCHEMY_DATABASE_URL,connect_args={"check_same_thread": False} )  #sqlite
engine = create_engine(SQLALCHEMY_DATABASE_URL)  #postgresadmin



SessionLocal = sessionmaker(autocommit=False, autoflush=False , bind=engine)

Base = declarative_base()

#postgres://rgszespq:3DR8T6gIOVWmu7B1CrlwaeMQM3MEBYT7@rajje.db.elephantsql.com/rgszespq