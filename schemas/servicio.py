from typing import Union, Optional, List
from datetime import date
from pydantic import BaseModel, EmailStr 

class Servico(BaseModel):
	nombre_servicio : str
	desc_servicio : str
	tipo_servicio : str

	class Config:
		from_attributes = True
		populate_by_name = True
		arbitrary_types_allowed = True	

class ServicioDB(Servico):	
	id_servicio : str	


	