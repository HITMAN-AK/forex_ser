from sqlalchemy import Column, Integer, String,ForeignKey
from sqlalchemy.orm import relationship
from database import Base

class User(Base):
    __tablename__ = "users"
    username = Column(String(100), primary_key=True, index=True)
    password = Column(String(100))

    history_false = relationship("Historyfalse", back_populates="userhf")
    history_true = relationship("Historytrue", back_populates="userht")


class Historyfalse(Base):
    __tablename__ = "historyfalse"
    id = Column(Integer, primary_key=True, index=True,autoincrement=True)
    user_id = Column(String(100), ForeignKey("users.username"))
    date = Column(String(20))
    open_at = Column(String(50))
    close_at = Column(String(50))
    open_time = Column(String(50))
    close_time = Column(String(50))
    predicted_trend = Column(String(50))
    actual_trend = Column(String(50),default="Yet to Predict")

    userhf = relationship("User", back_populates="history_false")


class Historytrue(Base):
    __tablename__ = "historytrue"
    id = Column(Integer, primary_key=True, index=True,autoincrement=True)
    user_id = Column(String(100), ForeignKey("users.username"))
    date = Column(String(20))
    open_at = Column(String(50))
    close_at = Column(String(50))
    open_time = Column(String(50))
    close_time = Column(String(50))
    predicted_trend = Column(String(50))
    actual_trend = Column(String(50))

    userht = relationship("User", back_populates="history_true")

