from typing import Union, Optional, List
from datetime import date
from pydantic import BaseModel, EmailStr 

class UserUPD(BaseModel):
	username: str
	email: Union[EmailStr, None] = None
	role: List[str] = []
	
	class Config:
		orm_mode = True
		allow_population_by_field_name = True
		arbitrary_types_allowed = True	
		
class UserActivate(BaseModel):	
	disable: Union[bool, None] = None
	
	class Config:
		orm_mode = True
		allow_population_by_field_name = True
		arbitrary_types_allowed = True	
	
class User(BaseModel):	
	username: str
	email: EmailStr
	role: List[str] = []		
	
	class Config:
		orm_mode = True
		allow_population_by_field_name = True
		arbitrary_types_allowed = True	

class UserAdd(User):
	hashed_password: str
	
class UserInDB(UserAdd):
	id: str
	disable: Union[bool, None] = None
	
class UserPassword(BaseModel):
    hashed_password: str
	
class UserResetPassword(BaseModel):
	actualpassword: str
	newpassword: str

#-------------------------
#-------TOKEN-------------
#-------------------------
class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
	username: Union[str, None] = None
	scopes: List[str] = []	

#-------------------------
#-----  Cliente   ------
#-------------------------
class Clientes(BaseModel):	
	cli_nombre : str
	cli_nacionalidad : str
	cli_edad : int
	cli_genero : str
			
	class Config:
		orm_mode = True
		allow_population_by_field_name = True
		arbitrary_types_allowed = True	
		
class Clientes_InDB(Clientes):	
	id_cliente : str
	
	
#-------------------------
#-----  Productos   ------
#-------------------------
class Productos_UPD(BaseModel):	
	prod_nombre : str
	
	class Config:
		orm_mode = True
		allow_population_by_field_name = True
		arbitrary_types_allowed = True	
		
class Productos(BaseModel):	
	prod_nombre : str
	
	class Config:
		orm_mode = True
		allow_population_by_field_name = True
		arbitrary_types_allowed = True	
		
class Productos_InDB(Productos):	
	id_producto : str	
	
#-------------------------
#-----  Productos   ------
#-------------------------
class Clientes_Productos_UPD(BaseModel):	
	cli_pro_valoracion : float
	
	class Config:
		orm_mode = True
		allow_population_by_field_name = True
		arbitrary_types_allowed = True	
		
class Clientes_Productos(BaseModel):	
	cli_pro_valoracion : float
	cliente_pro_id : str
	producto_cli_id : str
	
	class Config:
		orm_mode = True
		allow_population_by_field_name = True
		arbitrary_types_allowed = True	
		
class Clientes_Productos_InDB(Clientes_Productos):	
	id_cliente_producto : str	