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
	
	profesor = relationship("Profesor", uselist=False, back_populates="user_profesor", cascade="all, delete")
	cliente = relationship("Cliente", uselist=False, back_populates="user_cliente", cascade="all, delete")
	estudiante = relationship("Estudiante", uselist=False, back_populates="user_estudiante", cascade="all, delete")


class Servicio(Base):
	__tablename__ = "servicio"
	
	id_servicio = Column(GUID, primary_key=True, default=GUID_DEFAULT_SQLITE) 
	nombre_servicio = Column(String(50), unique=True, nullable=False, index=True) 
	desc_servicio = Column(String(250), nullable=False, index=True)
	tipo_servicio = Column(String(50), nullable=True, index=True) 

	productos = relationship("Producto", back_populates="servicios_productos", cascade="all, delete")

class Producto(Base):
	__tablename__ = "producto"
	
	id_producto = Column(GUID, primary_key=True, default=GUID_DEFAULT_SQLITE) 
	nombre_producto = Column(String(50), unique=True, nullable=False, index=True) 
	desc_producto = Column(String(250), nullable=False, index=True)
	consumo_producto = Column(Integer, nullable=True, index=True, default=0)
	tipo_producto = Column(String(50), nullable=True, index=True) 

	servicio_id = Column(GUID, ForeignKey("servicio.id_servicio"))
	servicios_productos = relationship("Servicio", back_populates="productos")
	