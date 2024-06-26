from fastapi import Depends, FastAPI, HTTPException, status, Response, Security, Request
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm, SecurityScopes
from functools import lru_cache
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from sqlalchemy.sql import func
from sqlalchemy import and_
from sqlalchemy.sql.expression import case
from sqlalchemy import desc, asc
from sqlalchemy import text
from uuid import uuid4
from pathlib import Path
from typing import Union
from datetime import datetime, timedelta
#---Imported for JWT example-----------
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel, ValidationError
from typing_extensions import Annotated
import models
import schemas
from database import SessionLocal, engine 
import init_db
import config
import asyncio
import concurrent.futures
import csv
from io import BytesIO, StringIO
from fastapi.responses import StreamingResponse
from fastapi import File, UploadFile
import codecs
import json
#FOR MACHONE LEARNING
import numpy as np
import pandas as pd
from sklearn.metrics.pairwise import cosine_similarity

models.Base.metadata.create_all(bind=engine)

#Create resources for JWT flow
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(
	tokenUrl="token",
	scopes={"admin": "Add, create, edit and delete all information.", "cliente": "Read relevant information.", "usuario": "Only read about us information"}
)
#----------------------
#Create our main app
app = FastAPI()

#----SETUP MIDDLEWARES--------------------

# Allow these origins to access the API
origins = [	
	"http://proj-precipitaciones.onrender.com",
	"https://proj-precipitaciones.onrender.com",		
	"http://localhost",
	"http://localhost:8080",
	"https://localhost:8080",
	"http://localhost:5000",
	"https://localhost:5000",
	"http://localhost:3000",
	"https://localhost:3000",
	"http://localhost:8000",
	"https://localhost:8000",
]

# Allow these methods to be used
methods = ["GET", "POST", "PUT", "DELETE"]

# Only these headers are allowed
headers = ["Content-Type", "Authorization"]

app.add_middleware(
	CORSMiddleware,
	allow_origins=origins,
	allow_credentials=True,
	allow_methods=methods,
	allow_headers=headers,
	expose_headers=["*"]
)

ALGORITHM = config.ALGORITHM	
SECRET_KEY = config.SECRET_KEY
APP_NAME = config.APP_NAME
ACCESS_TOKEN_EXPIRE_MINUTES = config.ACCESS_TOKEN_EXPIRE_MINUTES
ADMIN_USER = config.ADMIN_USER
ADMIN_NOMBRE = config.ADMIN_NOMBRE
ADMIN_PAPELLIDO = config.ADMIN_PAPELLIDO
ADMIN_SAPELLIDO = config.ADMIN_SAPELLIDO
ADMIN_CI = config.ADMIN_CI
ADMIN_CORREO = config.ADMIN_CORREO
ADMIN_PASS = config.ADMIN_PASS

# Dependency
def get_db():
	db = SessionLocal()
	try:
		yield db
	finally:
		db.close()


#------CODE FOR THE JWT EXAMPLE----------
def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def get_user(db: Session, username: str):
	db_user = db.query(models.User).filter(models.User.username == username).first()	
	if db_user is not None:
		return db_user 

#This function is used by "login_for_access_token"
def authenticate_user(username: str, password: str,  db: Session = Depends(get_db)):
    user = get_user(db, username)
    if not user:
        return False
    if not verify_password(password, user.hashed_password): #secret
        return False
    return user
	
#This function is used by "login_for_access_token"
def create_access_token(data: dict, expires_delta: Union[timedelta, None] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=30) #Si no se pasa un valor por usuario
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt
	
#This function is used by "get currecnt active user" dependency security authentication
async def get_current_user(
			security_scopes: SecurityScopes, 
			token: Annotated[str, Depends(oauth2_scheme)],
			db: Session = Depends(get_db)):
	if security_scopes.scopes:
		authenticate_value = f'Bearer scope="{security_scopes.scope_str}"'
	else:
		authenticate_value = "Bearer"
		
	credentials_exception = HTTPException(
		status_code=status.HTTP_401_UNAUTHORIZED,
		detail="Could not validate credentials",
		headers={"WWW-Authenticate": "Bearer"},
	)
	try:
		payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
		username: str = payload.get("sub")
		if username is None:
			raise credentials_exception			
		token_scopes = payload.get("scopes", [])
		token_data = schemas.TokenData(scopes=token_scopes, username=username)
		
	except (JWTError, ValidationError):
		raise credentials_exception
			
		token_data = schemas.TokenData(username=username)
	except JWTError:
		raise credentials_exception
		
	user = get_user(db, username=token_data.username)
	if user is None:
		raise credentials_exception
		
	for user_scope in security_scopes.scopes:
		if user_scope not in token_data.scopes:
			raise HTTPException(
				status_code=status.HTTP_401_UNAUTHORIZED,
				detail="Not enough permissions",
				headers={"WWW-Authenticate": authenticate_value},
			)
			
	return user
	
async def get_current_active_user(current_user: Annotated[schemas.User, Security(get_current_user, scopes=["admin"])]):  #, "manager", "user"
	if current_user.disable:
		print({"USER AUTENTICATED" : current_user.disable})
		print({"USER ROLES" : current_user.role})
		raise HTTPException(status_code=400, detail="Disable user")
	return current_user

#------------------------------------
@app.post("/token", response_model=schemas.Token)
async def login_for_access_token(form_data: Annotated[OAuth2PasswordRequestForm, Depends()], db: Session = Depends(get_db)):
	user = authenticate_user(form_data.username, form_data.password, db)
	if not user:
		raise HTTPException(
			status_code=status.HTTP_401_UNAUTHORIZED,
			detail="Incorrect username or password",
			headers={"WWW-Authenticate": "Bearer"},
		)
	access_token_expires = timedelta(minutes=int(ACCESS_TOKEN_EXPIRE_MINUTES))
	print(form_data.scopes)
	
	print(user.role) #Prin my roles to confirm them
	
	access_token = create_access_token(
		data={"sub": user.username, "scopes": user.role},   #form_data.scopes
		expires_delta=access_token_expires
	)
	return {"detail": "Ok", "access_token": access_token, "token_type": "Bearer"}
	
@app.get("/")
def index():
	return {"Aplicación": "Sistema recomendador"}
	
@app.get("/users/me", response_model=schemas.User)
async def read_users_me(current_user: Annotated[schemas.User, Depends(get_current_user)]):
	return current_user

@app.get("/get_restricted_user")
async def get_restricted_user(current_user: Annotated[schemas.User, Depends(get_current_active_user)]):
    return current_user
	
@app.get("/get_authenticated_edition_resources", response_model=schemas.User)
async def get_authenticated_edition_resources(current_user: Annotated[schemas.User, Security(get_current_active_user, scopes=["cliente"])]):
    return current_user
	
@app.get("/get_authenticated_read_resources", response_model=schemas.User)
async def get_authenticated_read_resources(current_user: Annotated[schemas.User, Security(get_current_user, scopes=["cliente"])]):
    return current_user
	
#########################
###   USERS ADMIN  ######
#########################
@app.post("/create_owner", status_code=status.HTTP_201_CREATED)  
async def create_owner(db: Session = Depends(get_db)): #Por el momento no tiene restricciones
	if db.query(models.User).filter(models.User.username == config.ADMIN_USER).first():
		db_user = db.query(models.User).filter(models.User.username == config.ADMIN_USER).first()
		if db_user is None:
			raise HTTPException(status_code=404, detail="El usuario no existe en la base de datos")	
		db.delete(db_user)	
		db.commit()
		
	db_user = models.User(
		username=config.ADMIN_USER, 
		email=config.ADMIN_CORREO,
		role=["admin","investigador","cliente","usuario"],
		disable=False,
		hashed_password=pwd_context.hash(config.ADMIN_PASS)		
	)
	db.add(db_user)
	db.commit()
	db.refresh(db_user)	
	return {f"Resultado:": config.ADMIN_PASS}
	
@app.post("/crear_usuario/", status_code=status.HTTP_201_CREATED)  
async def crear_usuario(current_user: Annotated[schemas.User, Depends(get_current_active_user)],
				user: schemas.UserAdd, db: Session = Depends(get_db)): 
	if db.query(models.User).filter(models.User.username == user.username).first() :
		raise HTTPException( 
			status_code=400,
			detail="El usuario existe en la base de datos",
		)	
	db_user = models.User(
		username=user.username, 
		email=user.email,
		role=user.role,
		disable=True,
		hashed_password=pwd_context.hash(user.hashed_password)
	)
	db.add(db_user)
	db.commit()
	db.refresh(db_user)	
	return {f"Usuario: {db_user.username}": "creado satisfactoriamente"}
	
@app.get("/leer_usuarios/", status_code=status.HTTP_201_CREATED) 
async def leer_usuarios(current_user: Annotated[schemas.User, Depends(get_current_active_user)],
		skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):    	
	db_users = db.query(models.User).offset(skip).limit(limit).all()    
	return db_users

@app.put("/actualizar_usuario/{username}", status_code=status.HTTP_201_CREATED) 
async def actualizar_usuario(current_user: Annotated[schemas.User, Depends(get_current_active_user)], 
				username: str, new_user: schemas.UserUPD, db: Session = Depends(get_db)):
	db_user = db.query(models.User).filter(models.User.username == username).first()
	if db_user is None:
		raise HTTPException(status_code=404, detail="Usuario no encontrado")
	db_user.username=new_user.username	
	db_user.email=new_user.email	
	db_user.role=new_user.role
	db.commit()
	db.refresh(db_user)	
	return db_user	
	
@app.put("/activar_usuario/{username}", status_code=status.HTTP_201_CREATED) 
async def activar_usuario(current_user: Annotated[schemas.User, Depends(get_current_active_user)],
				username: str, new_user: schemas.UserActivate, db: Session = Depends(get_db)):
	db_user = db.query(models.User).filter(models.User.username == username).first()
	if db_user is None:
		raise HTTPException(status_code=404, detail="Usuario no encontrado")
	if username != "_admin" and username != current_user.username:
		db_user.disable=new_user.disable		
		db.commit()
		db.refresh(db_user)	
	return db_user	
	
@app.delete("/eliminar_usuario/{username}", status_code=status.HTTP_201_CREATED) 
async def eliminar_usuario(current_user: Annotated[schemas.User, Depends(get_current_active_user)],
				username: str, db: Session = Depends(get_db)):
	db_user = db.query(models.User).filter(models.User.username == username).first()
	if db_user is None:
		raise HTTPException(status_code=404, detail="Usuario no encontrado")	
	if username != "_admin" and username != current_user.username:
		db.delete(db_user)	
		db.commit()
	return {"Deleted": "Usuario eliminado satisfactoriamente"}
	
@app.put("/actualizar_contrasenna/{username}", status_code=status.HTTP_201_CREATED) 
async def actualizar_contrasenna(current_user: Annotated[schemas.User, Security(get_current_user, scopes=["cliente"])],
				username: str, password: schemas.UserPassword, db: Session = Depends(get_db)):
	db_user = db.query(models.User).filter(models.User.username == username).first()
	if db_user is None:
		raise HTTPException(status_code=404, detail="Usuario no encontrado")	
	db_user.hashed_password=pwd_context.hash(password.hashed_password)
	db.commit()
	db.refresh(db_user)	
	return {"Result": "Contrasenna actualizada satisfactoriamente"}
	
@app.put("/actualizar_contrasenna_por_usuario/{username}", status_code=status.HTTP_201_CREATED) 
async def actualizar_contrasenna_por_usuario(current_user: Annotated[schemas.User, Security(get_current_user, scopes=["cliente"])],
				username: str, password: schemas.UserResetPassword, db: Session = Depends(get_db)):
				
	if not verify_password(password.actualpassword, current_user.hashed_password): 
		return HTTPException(status_code=700, detail="La cotrasenna actual no coincide")
		
	db_user = db.query(models.User).filter(models.User.username == username).first()	
	if db_user is None:
		raise HTTPException(status_code=404, detail="Usuario no encontrado")	
	db_user.hashed_password=pwd_context.hash(password.newpassword)
	db.commit()
	db.refresh(db_user)	
	return {"Response": "Contrasenna actualizada satisfactoriamente"}
		
######################
####  CLIENTE  #######
######################
@app.post("/crear_cliente/", status_code=status.HTTP_201_CREATED)
async def crear_cliente(current_user: Annotated[schemas.User, Depends(get_current_active_user)],
					cliente: schemas.Clientes, db: Session = Depends(get_db)):
	try:
		db_cliente = models.Clientes(
			cli_nombre = cliente.cli_nombre,
			cli_nacionalidad = cliente.cli_nacionalidad,
			cli_edad = cliente.cli_edad,
			cli_genero = cliente.cli_genero
		)			
		db.add(db_cliente)   	
		db.commit()
		db.refresh(db_cliente)			
		
		return {"Result":"Cliente creado satisfactoriamente"}
		
	except IntegrityError as e:
		raise HTTPException(status_code=500, detail="Error de integridad creando objeto Cliente")
	except SQLAlchemyError as e: 
		raise HTTPException(status_code=405, detail="Error inesperado creando el objeto Cliente")		

@app.get("/leer_clientes/", status_code=status.HTTP_201_CREATED)  
async def leer_clientes(current_user: Annotated[schemas.User, Security(get_current_user, scopes=["cliente"])],
					skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):    
	
	db_cliente = db.query(models.Clientes).all()	
	
	return db_cliente
	
@app.delete("/eliminar_cliente/{id}", status_code=status.HTTP_201_CREATED) 
async def eliminar_cliente(current_user: Annotated[schemas.User, Depends(get_current_active_user)],
					id: str, db: Session = Depends(get_db)):
	
	db_cliente = db.query(models.Clientes
						).filter(models.Clientes.id_cliente == id
						).first()
	
	if db_cliente is None:
		raise HTTPException(status_code=404, detail="El Cliente no existe en la base de datos")	
	
	db.delete(db_cliente)	
	db.commit()
	
	return {"Result": "Cliente eliminado satisfactoriamente"}
	
@app.put("/actualizar_cliente/{id}", status_code=status.HTTP_201_CREATED) 
async def actualizar_cliente(current_user: Annotated[schemas.User, Security(get_current_user, scopes=["cliente"])], 
				id: str, cliente: schemas.Clientes, db: Session = Depends(get_db)):
	
	db_cliente = db.query(models.Clientes).filter(models.Clientes.id_cliente == id).first()
	
	if db_cliente is None:
		raise HTTPException(status_code=404, detail="El cliente no existen en la base de datos")
	
	db_cliente.cli_nombre = cliente.cli_nombre	
	db_cliente.cli_nacionalidad = cliente.cli_nacionalidad
	db_cliente.cli_edad = cliente.cli_edad
	db_cliente.cli_genero = cliente.cli_genero
	
	db.commit()
	db.refresh(db_cliente)	
	
	return {"Result": "Cliente actualizado satisfactoriamente"}	
	
######################
####  PRODUCTOS  #####
######################
@app.post("/crear_producto/", status_code=status.HTTP_201_CREATED)
async def crear_producto(current_user: Annotated[schemas.User, Depends(get_current_active_user)],
					producto: schemas.Productos, db: Session = Depends(get_db)):
	try:
		db_producto = models.Productos(
			prod_nombre = producto.prod_nombre
		)			
		db.add(db_producto)   	
		db.commit()
		db.refresh(db_producto)			
		
		return {"Result":"Producto creado satisfactoriamente"}
		
	except IntegrityError as e:
		raise HTTPException(status_code=500, detail="Error de integridad creando objeto Producto")
	except SQLAlchemyError as e: 
		raise HTTPException(status_code=405, detail="Error inesperado creando el objeto Producto")		

@app.get("/leer_productos/", status_code=status.HTTP_201_CREATED)  
async def leer_productos(current_user: Annotated[schemas.User, Security(get_current_user, scopes=["cliente"])],
					skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):    
	
	db_productos = db.query(models.Productos).all()	
	
	return db_productos
	
@app.delete("/eliminar_producto/{id}", status_code=status.HTTP_201_CREATED) 
async def eliminar_producto(current_user: Annotated[schemas.User, Depends(get_current_active_user)],
					id: str, db: Session = Depends(get_db)):
	
	db_producto = db.query(models.Productos
						).filter(models.Productos.id_producto == id
						).first()
	
	if db_producto is None:
		raise HTTPException(status_code=404, detail="El Producto no existe en la base de datos")	
	
	db.delete(db_producto)	
	db.commit()
	
	return {"Result": "Producto eliminado satisfactoriamente"}
	
@app.put("/actualizar_producto/{id}", status_code=status.HTTP_201_CREATED) 
async def actualizar_producto(current_user: Annotated[schemas.User, Security(get_current_user, scopes=["cliente"])], 
				id: str, producto: schemas.Productos_UPD, db: Session = Depends(get_db)):
	
	db_producto = db.query(models.Productos).filter(models.Productos.id_producto == id).first()
	
	if db_producto is None:
		raise HTTPException(status_code=404, detail="El producto no existen en la base de datos")
	
	db_producto.prod_nombre = producto.prod_nombre
	
	db.commit()
	db.refresh(db_producto)	
	
	return {"Result": "Producto actualizado satisfactoriamente"}

######################
####   CLI-PROD  #####
######################
@app.post("/crear_cliente_producto/", status_code=status.HTTP_201_CREATED)
async def crear_cliente_producto(current_user: Annotated[schemas.User, Depends(get_current_active_user)],
					cli_prod: schemas.Clientes_Productos, db: Session = Depends(get_db)):
	try:
		db_cli_prod = models.Clientes_Productos(
			cli_pro_valoracion = cli_prod.cli_pro_valoracion,
			cliente_pro_id = cli_prod.cliente_pro_id,
			producto_cli_id = cli_prod.producto_cli_id,
		)			
		db.add(db_cli_prod)   	
		db.commit()
		db.refresh(db_cli_prod)			
		
		return {"Result":"Consumo cliente producto creado satisfactoriamente"}
		
	except IntegrityError as e:
		raise HTTPException(status_code=500, detail="Error de integridad creando objeto Cliente Producto")
	except SQLAlchemyError as e: 
		raise HTTPException(status_code=405, detail="Error inesperado creando el objeto Cliente Producto")		

@app.get("/leer_cliente_producto/", status_code=status.HTTP_201_CREATED)  
async def leer_cliente_producto(current_user: Annotated[schemas.User, Security(get_current_user, scopes=["cliente"])],
					skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):    
	
	db_cliente_producto = db.query(models.Clientes_Productos).all()	
	
	return db_cliente_producto
	
@app.delete("/eliminar_cliente_producto/{id}", status_code=status.HTTP_201_CREATED) 
async def eliminar_cliente_producto(current_user: Annotated[schemas.User, Depends(get_current_active_user)],
					id: str, db: Session = Depends(get_db)):
	
	db_cliente_producto = db.query(models.Clientes_Productos
						).filter(models.Clientes_Productos.id_cliente_producto == id
						).first()
	
	if db_cliente_producto is None:
		raise HTTPException(status_code=404, detail="El consumo Cliente Producto no existe en la base de datos")	
	
	db.delete(db_cliente_producto)	
	db.commit()
	
	return {"Result": "Consumo Cliente Producto eliminado satisfactoriamente"}
	
@app.put("/actualizar_cliente_producto/{id}", status_code=status.HTTP_201_CREATED) 
async def actualizar_cliente_producto(current_user: Annotated[schemas.User, Security(get_current_user, scopes=["cliente"])], 
				id: str, cli_prod: schemas.Clientes_Productos_UPD, db: Session = Depends(get_db)):
	
	db_cliente_producto = db.query(models.Clientes_Productos).filter(models.Clientes_Productos.id_cliente_producto == id).first()
	
	if db_cliente_producto is None:
		raise HTTPException(status_code=404, detail="El consumo cliente producto no existen en la base de datos")
	
	db_cliente_producto.cli_pro_valoracion = cli_prod.cli_pro_valoracion
	
	db.commit()
	db.refresh(db_cliente_producto)	
	
	return {"Result": "Consumo Cliente Producto actualizado satisfactoriamente"}
	
@app.get("/leer_productos_por_cliente/{id}", status_code=status.HTTP_201_CREATED)  
async def leer_productos_por_cliente(current_user: Annotated[schemas.User, Security(get_current_user, scopes=["cliente"])],
					id: str, db: Session = Depends(get_db)):    
	
	db_productos_clientes = db.query(
		models.Clientes_Productos.id_cliente_producto,
		models.Productos.prod_nombre,		
		models.Clientes_Productos.cli_pro_valoracion
		).select_from(
			models.Clientes_Productos
		).join(
			models.Productos, models.Productos.id_producto == models.Clientes_Productos.producto_cli_id
		).join(
			models.Clientes, models.Clientes.id_cliente == models.Clientes_Productos.cliente_pro_id
		).where(
			models.Clientes_Productos.cliente_pro_id == id
		).all()
	
	return db_productos_clientes	
	
######################
######  QUERY  #######
######################
def create_csv(query, columns_names):
	csvtemp = ""		
	header = [i for i in columns_names]
	csvtemp = ",".join(header) + "\n"
	
	for row in query:		
		csvtemp += (str(row)).replace("(", "").replace(")", "").replace("'", "") + "\n"		
		
	return StringIO(csvtemp)
	
@app.get("/leer_clientes_ratings/", status_code=status.HTTP_201_CREATED)  
async def leer_clientes_ratings(current_user: Annotated[schemas.User, Security(get_current_user, scopes=["cliente"])],
					skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):    
	
	db_clientes_ratings = db.query(
		models.Clientes_Productos.id_cliente_producto,		
		models.Clientes_Productos.cli_pro_valoracion,
		models.Clientes_Productos.producto_cli_id,
		models.Productos.prod_nombre,		
		models.Clientes_Productos.cliente_pro_id,
		models.Clientes.cli_nombre,
		models.Clientes.cli_nacionalidad,
		models.Clientes.cli_edad,
		models.Clientes.cli_genero
		).select_from(
			models.Clientes_Productos
		).join(
			models.Clientes, models.Clientes.id_cliente == models.Clientes_Productos.cliente_pro_id
		).join(
			models.Productos, models.Productos.id_producto == models.Clientes_Productos.producto_cli_id
		).all()
	
	return db_clientes_ratings
	
@app.get("/save_csv_clientes_ratings/", status_code=status.HTTP_201_CREATED)  
async def save_csv_clientes_ratings(current_user: Annotated[schemas.User, Security(get_current_user, scopes=["cliente"])],
					db: Session = Depends(get_db)):    
	
	db_clientes_ratings = db.query(
		models.Clientes_Productos.id_cliente_producto.label("id_consumo"),		
		models.Clientes_Productos.cli_pro_valoracion.label("valoracion"),
		models.Clientes_Productos.producto_cli_id.label("id_producto"),
		models.Productos.prod_nombre.label("producto"),		
		models.Clientes_Productos.cliente_pro_id.label("id_cliente"),
		models.Clientes.cli_nombre.label("cliente"),
		models.Clientes.cli_nacionalidad.label("nacionalidad"),
		models.Clientes.cli_edad.label("edad"),
		models.Clientes.cli_genero.label("genero")
		).select_from(
			models.Clientes_Productos
		).join(
			models.Clientes, models.Clientes.id_cliente == models.Clientes_Productos.cliente_pro_id
		).join(
			models.Productos, models.Productos.id_producto == models.Clientes_Productos.producto_cli_id
		).all()
	
	col_cli_prod = ["id_consumo","valoracion"]
	col_prod = ["id_producto","producto"]
	col_cli = ["id_cliente","cliente","nacionalidad","edad","genero"]
	columns = col_cli_prod + col_prod + col_cli
	myfile = create_csv(db_clientes_ratings, columns)	
	headers = {'Content-Disposition': 'attachment; filename="clientes_raitings.csv"'} 
	return StreamingResponse(iter([myfile.getvalue()]), media_type="application/csv", headers=headers)		
	
@app.get("/sql_to_df_clientes_ratings/", status_code=status.HTTP_201_CREATED)  
async def sql_to_df_clientes_ratings(current_user: Annotated[schemas.User, Security(get_current_user, scopes=["cliente"])],
					db: Session = Depends(get_db)):    
	
	db_clientes_ratings = db.query(
		models.Clientes_Productos.id_cliente_producto.label("id_consumo"),		
		models.Clientes_Productos.cli_pro_valoracion.label("valoracion"),
		models.Clientes_Productos.producto_cli_id.label("id_producto"),
		models.Productos.prod_nombre.label("producto"),		
		models.Clientes_Productos.cliente_pro_id.label("id_cliente"),
		models.Clientes.cli_nombre.label("cliente"),
		models.Clientes.cli_nacionalidad.label("nacionalidad"),
		models.Clientes.cli_edad.label("edad"),
		models.Clientes.cli_genero.label("genero")
		).select_from(
			models.Clientes_Productos
		).join(
			models.Clientes, models.Clientes.id_cliente == models.Clientes_Productos.cliente_pro_id
		).join(
			models.Productos, models.Productos.id_producto == models.Clientes_Productos.producto_cli_id
		).statement
	

	df = pd.read_sql(db_clientes_ratings, con=engine)	
	#Preparando datos
	print(df.describe())
	
	return {"Result": "Done"}

###############################
######  RECOMENDATIONS  #######
###############################
def create_customer_item_matrix(df, _index, _col, _val):
    #Construimos una matriz de elementos para el cliente
    item_matrix = df.pivot_table(
        index=_index,
        columns=_col,
        values=_val,
        aggfunc='sum')
    
    return item_matrix
	
def format_customer_item_matrix(cu_item_matrix):
    #Ahora, codifiquemos 0-1 estos datos, de manera que un valor de 1 significa que el producto dado fue comprado
    #por el cliente dado, y un valor de 0 significa que el producto dado nunca fue comprado por el cliente dado
    return cu_item_matrix.applymap(lambda x: 1 if x > 0 else 0)
	
def create_uu_sim_item_matrix(for_cu_item_matrix):
    #Crear la matriz de similitud entre usuarios
    return pd.DataFrame(cosine_similarity(for_cu_item_matrix))
	
def reset_index_uu_sim_item_matrix(uu_sim_matriz, cu_item_matrix, _index):
    #Pasamos las columnas a los índices
    uu_sim_matriz.columns = cu_item_matrix.index
    #Renombrar los índices de los clientes 
    uu_sim_matriz[_index] = cu_item_matrix.index
    #Hacemos que la columna correspondiente a "_index" sea el índice del dataframe
    uu_sim_matriz = uu_sim_matriz.set_index(_index)
    
    return uu_sim_matriz
	
def get_items_from_target_A(cu_items_matrix, _tA):
    #Obtener items de el usuario target
    items_bought_by_A = set(cu_items_matrix.loc[_tA].iloc[
        cu_items_matrix.loc[_tA].to_numpy().nonzero()].index)
    
    return items_bought_by_A
	
def get_items_from_target_B(cu_items_matrix, _tB):
    #Obtener items de el usuario top similar a target
    items_bought_by_B = set(cu_items_matrix.loc[_tB].iloc[
        cu_items_matrix.loc[_tB].to_numpy().nonzero()].index)  
    
    return items_bought_by_B
	
def compute_different_items(items_target_user, items_top_sim_user):
    #Calcular los items comprados por A que no tiene B
    if items_target_user > items_top_sim_user:
        return items_target_user - items_top_sim_user 
    
    return items_top_sim_user - items_target_user  
	
def get_top_user(ri_uu_sim_matrix, _target):
	#Obtener los k_top usuarios de la matriz con índices actualizados 
	#(o de un dataframe previamente guardado con la matriz de usuarios similares)
	top_users = ri_uu_sim_matrix.loc[_target].sort_values(ascending=False)
	#Obtener los índices de los tops (no se escogen el 1 o el 2 pues se parecen mucho,
	#SE ESCOGE EL PRIMERO DESPUÉS DE LA MEDIA)
	list_indexes = top_users.index
	list_values = top_users.values
	less_sim_user = []
	[less_sim_user.append(list_indexes[i]) for i in range(len(list_values)) if list_values[i] <= list_values.mean()]

	return less_sim_user[0]
	
def combine_steps_to_make_uu_sim_matrix(df):
	customer_item_matrix = create_customer_item_matrix(df, 'id_cliente', 'id_producto', 'valoracion')
	cu_items_matrix = format_customer_item_matrix(customer_item_matrix)
	uu_sim_matriz = create_uu_sim_item_matrix(cu_items_matrix)
	ri_uu_sim_matrix = reset_index_uu_sim_item_matrix(uu_sim_matriz, cu_items_matrix, 'id_cliente')
		
	return cu_items_matrix, ri_uu_sim_matrix
	
def combine_steps_to_select_items(cu_items_matrix, user_target, top_sim_user):	
	items_bought_by_target = get_items_from_target_A(cu_items_matrix, user_target)
	items_bought_by_top_user = get_items_from_target_B(cu_items_matrix, top_sim_user)
	#se devuelve el ID de los items (productos) recomendados
	return compute_different_items(items_bought_by_target, items_bought_by_top_user)
	
#Recomendador para productos
def make_recomendations(df, items_to_recomendate, return_cols_list, delete_duplicates_in):
    #Extraer sus caracteristicas del DF
    #busca las filas donde se encuentren los items recomendados 
    #Extrae las columnas correspondientes a "cols_list"
    #y elimina los valores duplicados guiándose por la columna "valoración"
    return df.loc[df['id_producto'].isin(items_to_recomendate), return_cols_list
        ].drop_duplicates().set_index(delete_duplicates_in)
		
def combine_all_for_recomendatios(df, user_target, return_cols_list, delete_duplicates_in):
	#Extraer la matriz de usuarios y de similitud entre usuarios
	cu_items_matrix, ri_uu_sim_matrix = combine_steps_to_make_uu_sim_matrix(df)
	top_sim_user = get_top_user(ri_uu_sim_matrix, user_target)
	items_to_recomendate = combine_steps_to_select_items(cu_items_matrix, user_target, top_sim_user)
	
	return make_recomendations(df, items_to_recomendate, return_cols_list, delete_duplicates_in)
	
@app.get("/hacer_recomendaciones_cliente_basicas/{id}", status_code=status.HTTP_201_CREATED)  
async def hacer_recomendaciones_cliente_basicas(current_user: Annotated[schemas.User, Security(get_current_user, scopes=["cliente"])],
					id: str, db: Session = Depends(get_db)):    
	
	db_clientes_ratings = db.query(
		models.Clientes_Productos.id_cliente_producto.label("id_consumo"),		
		models.Clientes_Productos.cli_pro_valoracion.label("valoracion"),
		models.Clientes_Productos.producto_cli_id.label("id_producto"),
		models.Productos.prod_nombre.label("producto"),		
		models.Clientes_Productos.cliente_pro_id.label("id_cliente"),
		models.Clientes.cli_nombre.label("cliente"),
		models.Clientes.cli_nacionalidad.label("nacionalidad"),
		models.Clientes.cli_edad.label("edad"),
		models.Clientes.cli_genero.label("genero")
		).select_from(
			models.Clientes_Productos
		).join(
			models.Clientes, models.Clientes.id_cliente == models.Clientes_Productos.cliente_pro_id
		).join(
			models.Productos, models.Productos.id_producto == models.Clientes_Productos.producto_cli_id
		).statement
	
	#Preparando datos
	df = pd.read_sql(db_clientes_ratings, con=engine)
	
	if df.size < 5:
		raise HTTPException(status_code=505, detail="No existen datos suficientes para hacer recomendaciones")	
		
	#Obtener el ID del cliente
	db_cliente = db.query(models.Clientes
						).filter(models.Clientes.id_cliente == id
						).first()
	#Definir el usuario target
	user_target = db_cliente.id_cliente
	return_cols_list = ['producto'] 
	delete_duplicates_in = 'producto'
	recomendaciones = combine_all_for_recomendatios(df, user_target, return_cols_list, delete_duplicates_in)
	recomendaciones = recomendaciones.reset_index()
	
	return {"Result": recomendaciones.values.tolist()}

	
	
