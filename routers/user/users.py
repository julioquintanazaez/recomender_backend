from fastapi import APIRouter, Depends, HTTPException, status, Security
from sqlalchemy.orm import Session
from db.database import SessionLocal, get_db
from models.data import User
from schemas.user import User_Add, User_Base, User_ResetPassword, User_InDB, DeleteRequest
from security.auth import get_password_hash, get_current_active_user, get_current_user, pwd_context
from typing_extensions import Annotated


router = APIRouter()

@router.post("/crear_usuario/", status_code=status.HTTP_201_CREATED)
async def create_user(user: User_Add, db: Session = Depends(get_db)): 
    user.hashed_password = get_password_hash(user.hashed_password)
    db_user = User(**user.dict())
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

@router.get("/leer_usuarios/", status_code=status.HTTP_201_CREATED) 
async def leer_usuarios(usuario_actual: Annotated[User_InDB, Security(get_current_user, scopes=["admin"])],
		skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):    	
	db_users = db.query(User).offset(skip).limit(limit).all()    
	return db_users

@router.delete("/eliminar_usuario/{id}", status_code=status.HTTP_201_CREATED) 
async def eliminar_usuario(usuario_actual: Annotated[User_InDB, Security(get_current_user, scopes=["admin"])],
				id: str, db: Session = Depends(get_db)):
	db_user = db.query(User).filter(User.id == id).first()
	if db_user is None:
		raise HTTPException(status_code=404, detail="Usuario no encontrado")	
	if id != usuario_actual.id:
		db.delete(db_user)	
		db.commit()
	return {"Eliminar": "Usuario eliminado satisfactoriamente"}
	
@router.put("/actualizar_usuario/{id}", status_code=status.HTTP_201_CREATED) 
async def actualizar_usuario(usuario_actual: Annotated[User_InDB, Security(get_current_user, scopes=["admin"])], 
				id: str, nuevo_usuario: User_Base, db: Session = Depends(get_db)):
	db_user = db.query(User).filter(User.id == id).first()
	if db_user is None:
		raise HTTPException(status_code=404, detail="Usuario no encontrado en la base de datos")
	db_user.usuario=nuevo_usuario.usuario	
	db_user.role=nuevo_usuario.role
	db.commit()
	db.refresh(db_user)	
	return db_user	

@router.put("/actualizar_contrasenna/{id}", status_code=status.HTTP_201_CREATED) 
async def actualizar_contrasenna(usuario_actual: Annotated[User_InDB, Security(get_current_user, scopes=["trabajador", "cliente"])],
				id: str, password: User_ResetPassword, db: Session = Depends(get_db)):
	db_user = db.query(User).filter(User.id == id).first()
	if db_user is None:
		raise HTTPException(status_code=404, detail="Usuario no encontrado en la base de datos")	
	db_user.hashed_password=pwd_context.hash(password.newpassword)
	db.commit()
	db.refresh(db_user)	
	return {"Resultado": "Contraseña actualizada satisfactoriamente"}


@router.delete("/delete-usuarios/")
async def delete_items(request: DeleteRequest, db: Session = Depends(get_db)):
    indices_to_delete = request.indices
    items_to_delete = db.query(User).filter(
		User.id.in_(indices_to_delete)).all()
    if not items_to_delete:
        raise HTTPException(status_code=404, detail="No items found to delete")
    for item in items_to_delete:
        db.delete(item)
    db.commit()
    return {"message": "Usuarios eliminados satisfactoriamente"}