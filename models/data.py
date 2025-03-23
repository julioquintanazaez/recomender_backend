#from db.database import Base
import datetime
from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, Float, String, Text, UniqueConstraint
from sqlalchemy.orm import relationship
from fastapi_utils.guid_type import GUID, GUID_DEFAULT_SQLITE
from sqlalchemy.types import TypeDecorator, String
import json
from uuid import UUID, uuid4 
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class JSONEncodeDict(TypeDecorator):
	impl = String	
	def process_bind_param(self, value, dialect):
		if value is not None:
			value = json.dumps(value)
		return value
	
	def process_result_value(self, value, dialect):
		if value is not None:
			value = json.loads(value)
		return value
		
class User(Base):
	__tablename__ = "user"
	
	id = Column(GUID, primary_key=True, default=GUID_DEFAULT_SQLITE)
	usuario = Column(String(30), unique=True, index=True) 
	role = Column(JSONEncodeDict)
	hashed_password = Column(String(100), nullable=True, default=False)	
	
class Producto(Base):
	__tablename__ = "producto"
	
	id_producto = Column(GUID, primary_key=True, default=GUID_DEFAULT_SQLITE) 
	nombre_producto = Column(String(50), unique=True, nullable=False, index=True) 
	desc_producto = Column(String(250), nullable=False, index=True)
	consumo_producto = Column(Integer, nullable=True, index=True, default=0)

	