from typing import Union, Optional, List
from datetime import date
from pydantic import BaseModel, EmailStr 

class User_Base(BaseModel):	
	usuario : Union[str, None] = None	
	role: List[str] = ["admin", "cliente"]
	class Config:
		from_attributes = True
		populate_by_name = True
		arbitrary_types_allowed = True	
	
class User_Add(User_Base):
	hashed_password: str
	
class User_InDB(User_Add):
	id: str

class User_ResetPassword(BaseModel):
	newpassword: str

class DeleteRequest(BaseModel):
    indices: List[str]
