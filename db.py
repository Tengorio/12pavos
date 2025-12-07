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
    # Setup for local SQLite database
    # This removes dependency on st.secrets as requested for V2
    return create_engine("sqlite:///reunion.db")

def init_db():
    engine = get_engine()
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine)()

def get_session():
    engine = get_engine()
    Session = sessionmaker(bind=engine)
    return Session()
