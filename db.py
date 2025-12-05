import streamlit as st
from sqlalchemy import create_engine, Column, Integer, String, Text, ForeignKey, PickleType
from sqlalchemy.orm import declarative_base, sessionmaker, relationship
from sqlalchemy.sql import text

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    username = Column(String(50), unique=True, nullable=False)
    password_hash = Column(String(128), nullable=False)
    name = Column(String(100))
    
    # Relationships
    availability = relationship("Availability", back_populates="user", uselist=False)
    potluck = relationship("Potluck", back_populates="user", uselist=False)
    wishes = relationship("Wish", foreign_keys="[Wish.user_id]", back_populates="user")
    claimed_wishes = relationship("Wish", foreign_keys="[Wish.claimed_by_id]", back_populates="claimed_by")

class Availability(Base):
    __tablename__ = 'availability'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    dates_json = Column(Text) # storing list of dates as JSON string or comma-separated
    
    user = relationship("User", back_populates="availability")

class Potluck(Base):
    __tablename__ = 'potluck'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    dish_1 = Column(String(200))
    dish_2 = Column(String(200))
    dish_3 = Column(String(200))
    assigned_dish = Column(String(200))
    
    user = relationship("User", back_populates="potluck")

class Wish(Base):
    __tablename__ = 'wishes'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    description = Column(String(255))
    claimed_by_id = Column(Integer, ForeignKey('users.id'), nullable=True)
    
    user = relationship("User", foreign_keys=[user_id], back_populates="wishes")
    claimed_by = relationship("User", foreign_keys=[claimed_by_id], back_populates="claimed_wishes")

# Database Connection
def get_engine():
    try:
        # Construct connection string from secrets
        # Expecting structure: [connections.sql]
        db_conf = st.secrets["connections"]["sql"]
        # Handle different dialects if necessary, assuming postgres/mysql compatible URL construction
        # url = f"{db_conf['dialect']}://{db_conf['username']}:{db_conf['password']}@{db_conf['host']}:{db_conf['port']}/{db_conf['database']}"
        # Or if the user puts the full url in secrets, simpler.
        # Let's construct it carefully considering the dialect.
        driver = db_conf.get("dialect", "postgresql")
        user = db_conf["username"]
        password = db_conf["password"]
        host = db_conf["host"]
        port = db_conf["port"]
        dbname = db_conf["database"]
        
        if "postgres" in driver:
            driver = "postgresql+psycopg2"
        elif "mysql" in driver:
            driver = "mysql+pymysql"
            
        url = f"{driver}://{user}:{password}@{host}:{port}/{dbname}"
        return create_engine(url)
    except Exception as e:
        # Fallback for dev/testing if secrets missing? No, we need to fail or warn.
        # But for the initial run, maybe we want to allow a local sqlite fallback if secrets fail?
        # User explicitly asked for remote DB.
        raise e

def init_db():
    engine = get_engine()
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine)()

def get_session():
    engine = get_engine()
    Session = sessionmaker(bind=engine)
    return Session()
