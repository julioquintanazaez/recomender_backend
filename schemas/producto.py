from typing import Union, Optional, List
from datetime import date
from pydantic import BaseModel, EmailStr 

class ProductoRecord(BaseModel):		
	nombre_producto : str 
	desc_producto : str
	tipo_producto : str

	class Config:
		from_attributes = True
		populate_by_name = True
		arbitrary_types_allowed = True	

class ProductoAdd(ProductoRecord):		
	servicio_id : str
	
class ProductoConsumo(BaseModel):
	consumo_producto : int
