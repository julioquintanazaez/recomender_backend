from typing import Union, Optional, List
from datetime import date
from pydantic import BaseModel, EmailStr 

class ProductoBase(BaseModel):		
	nombre_producto : str 
	desc_producto : str

	class Config:
		from_attributes = True
		populate_by_name = True
		arbitrary_types_allowed = True	

class ProductoDB(ProductoBase):		
	id_producto : str
	
class ProductoConsumo(BaseModel):
	consumo_producto : int
