from database import Base
import datetime
from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, Float, String, Text, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from fastapi_utils.guid_type import GUID, GUID_DEFAULT_SQLITE
from sqlalchemy.types import TypeDecorator, String
import json

from uuid import UUID, uuid4  

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
	username = Column(String(30), unique=True, index=True) 
	email = Column(String(30), unique=True, nullable=False, index=True) 
	role = Column(JSONEncodeDict)
	disable = Column(Boolean, nullable=True, default=False)	
	hashed_password = Column(String(100), nullable=True, default=False)		
	
class Clientes(Base):
	__tablename__ = "clientes"
	
	id_cliente = Column(GUID, primary_key=True, default=GUID_DEFAULT_SQLITE) 
	cli_nombre = Column(String(50), unique=True, nullable=False, index=True) 
	cli_nacionalidad = Column(String(50), nullable=False, index=True) 
	cli_edad = Column(Integer, nullable=False, index=True) 
	cli_genero = Column(String(50), nullable=False, index=True)
	#Relacion M-M con tabla "Productos"
	clientes_ref = relationship("Productos", secondary="clientes_productos", back_populates="productos_ref", cascade="all, delete") 	
	
	
class Productos(Base):
	__tablename__ = "productos"
	
	id_producto = Column(GUID, primary_key=True, default=GUID_DEFAULT_SQLITE) 
	prod_nombre = Column(String(50), unique=True, nullable=False, index=True) 
	#Relacion M-M con tabla "Productos"
	productos_ref = relationship("Clientes", secondary="clientes_productos", back_populates="clientes_ref", cascade="all, delete") 	
	
	
class Clientes_Productos(Base):
	__tablename__ = "clientes_productos"
	
	id_cliente_producto = Column(GUID, primary_key=True, default=GUID_DEFAULT_SQLITE) 
	cli_pro_valoracion = Column(Float, nullable=False, index=True) 
	#Llaves primarias de asociacion para las tablas padres
	cliente_pro_id = Column(GUID, ForeignKey('clientes.id_cliente'), primary_key=True)   
	producto_cli_id = Column(GUID, ForeignKey('productos.id_producto'), primary_key=True) 
	
	__table_args__ = (UniqueConstraint("cliente_pro_id", "producto_cli_id"), )
	
	
