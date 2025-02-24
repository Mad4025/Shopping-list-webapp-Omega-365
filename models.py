from sqlalchemy import Column, Integer, String, DateTime, DECIMAL, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import create_engine
from dotenv import load_dotenv
from datetime import datetime
import os
from flask_login import UserMixin

load_dotenv()

Base = declarative_base()
db_path = os.getenv('db_path')
engine = create_engine(f"mysql+pymysql://{db_path}")


class ShoppingList(Base):
    __tablename__ = 'shopping_list'

    id = Column(Integer, primary_key=True, autoincrement=True)
    item_name = Column(String(100), nullable=False)
    quantity = Column(Integer, default=1)
    price = Column(DECIMAL(10, 2), default=0.00)
    created_at = Column(DateTime, default=datetime.now)

    # For logging and debugging purposes only
    def __repr__(self):
        return f"<ShoppingList(item_name='{self.item_name}', quantity={self.quantity}, price={self.price})>"


class ShoppingCart(Base):
    __tablename__ = 'shopping_cart'

    id = Column(Integer, primary_key=True, autoincrement=True)
    item_name = Column(String(100), nullable=False)
    quantity = Column(Integer, default=1)
    added_at = Column(DateTime, default=datetime.now)


class PurchaseHistory(Base):
    __tablename__ = 'purchase_history'

    id = Column(Integer, primary_key=True, autoincrement=True)
    transaction_id = Column(String(100), nullable=False) # Store stripe session_id
    item_name = Column(String(100), nullable=False)
    quantity = Column(Integer, nullable=False)
    price = Column(Float, nullable=False)
    purchased_at = Column(DateTime, default=datetime.now)


class User(UserMixin, Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)
    username = Column(String(150), unique=True, nullable=False)
    role = Column(String(50), default='user')


Base.metadata.create_all(engine)