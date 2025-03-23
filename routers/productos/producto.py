from fastapi import APIRouter, Depends, HTTPException, status, Security
from sqlalchemy.orm import Session
from db.database import SessionLocal, engine, get_db
from models.data import Producto
from schemas.producto import ProductoBase, ProductoDB, ProductoConsumo
from schemas.user import User_InDB
from security.auth import get_current_active_user, get_current_user
from typing_extensions import Annotated
from sqlalchemy.exc import SQLAlchemyError, IntegrityError

router = APIRouter()

@router.post("/crear_producto/", status_code=status.HTTP_201_CREATED)
async def crear_producto(current_user: Annotated[User_InDB, Security(get_current_user, scopes=["admin"])],
					producto: ProductoBase, db: Session = Depends(get_db)):
	try:
		db_producto = Producto(
			nombre_producto = producto.nombre_producto,
			desc_producto = producto.desc_producto,
		)			
		db.add(db_producto)   	
		db.commit()
		db.refresh(db_producto)			
		return db_producto
	except IntegrityError as e:
		raise HTTPException(status_code=500, detail="Error de integridad creando objeto Producto")
	except SQLAlchemyError as e: 
		raise HTTPException(status_code=405, detail="Error inesperado SQLAlchemy creando el objeto Producto")		


@router.get("/leer_productos/", status_code=status.HTTP_201_CREATED)  
async def leer_productos(current_user: Annotated[User_InDB, Security(get_current_user, scopes=["cliente"])],
					skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):    
	return db.query(Producto).all()	
	

@router.delete("/eliminar_producto/{id}", status_code=status.HTTP_201_CREATED) 
async def eliminar_producto(current_user: Annotated[User_InDB, Security(get_current_user, scopes=["admin"])],
					id: str, db: Session = Depends(get_db)):
	db_producto = db.query(Producto).filter(Producto.id_producto == id).first()
	if db_producto is None:
		raise HTTPException(status_code=404, detail="El producto no existe en la base de datos")	
	db.delete(db_producto)	
	db.commit()
	return {"Result": "Producto eliminado satisfactoriamente"}


@router.put("/actualizar_producto/{id}", status_code=status.HTTP_201_CREATED) 
async def actualizar_producto(current_user: Annotated[User_InDB, Security(get_current_user, scopes=["admin"])], 
				id: str, nueva_producto: ProductoBase, db: Session = Depends(get_db)):
	db_producto = db.query(Producto).filter(Producto.id_producto == id).first()
	if db_producto is None:
		raise HTTPException(status_code=404, detail="El producto seleccionada no existe en la base de datos")
	db_producto.nombre_producto=nueva_producto.nombre_producto
	db_producto.desc_producto=nueva_producto.desc_producto
	db.commit()
	db.refresh(db_producto)	
	return {"Result": "Producto actualizado satisfactoriamente"}	

@router.put("/incrementar_consumo/{id}", status_code=status.HTTP_200_OK) 
async def incrementar_consumo(id: str, db: Session = Depends(get_db)):
	db_producto = db.query(Producto).filter(Producto.id_producto == id).first()
	if db_producto is None:
		raise HTTPException(status_code=404, detail="El producto seleccionada no existe en la base de datos")
	db_producto.consumo_producto=(db_producto.consumo_producto + 1)
	db.commit()
	db.refresh(db_producto)	
	return {"Result": "El consumo del producto actualizado satisfactoriamente"}	

@router.put("/reducir_consumo/{id}", status_code=status.HTTP_200_OK) 
async def reducir_consumo(id: str, db: Session = Depends(get_db)):
	db_producto = db.query(Producto).filter(Producto.id_producto == id).first()
	if db_producto is None:
		raise HTTPException(status_code=404, detail="El producto seleccionada no existe en la base de datos")
	if db_producto.consumo_producto > 0:
		db_producto.consumo_producto=(db_producto.consumo_producto - 1)
	else:
		db_producto.consumo_producto=0
	db.commit()
	db.refresh(db_producto)	
	return {"Result": "El consumo del producto actualizado satisfactoriamente"}	
	
@router.put("/actualizar_producto_consumo/{id}", status_code=status.HTTP_201_CREATED) 
async def actualizar_producto_consumo(current_user: Annotated[User_InDB, Security(get_current_user, scopes=["admin"])], 
				id: str, nueva_producto: ProductoConsumo, db: Session = Depends(get_db)):
	db_producto = db.query(Producto).filter(Producto.id_producto == id).first()
	if db_producto is None:
		raise HTTPException(status_code=404, detail="El producto seleccionada no existe en la base de datos")
	db_producto.consumo_producto=nueva_producto.consumo_producto
	db.commit()
	db.refresh(db_producto)	
	return {"Result": "Producto actualizado satisfactoriamente"}	

@router.get("/leer_productos_libres/", status_code=status.HTTP_200_OK)  
async def leer_productos_libres(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):    
	return db.query(Producto).all()	

@router.get("/leer_productos_recomendados/", status_code=status.HTTP_200_OK)  
async def leer_productos_recomendados(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):    
	productos = db.query(Producto).filter(Producto.consumo_producto != 0).all()
	return productos

