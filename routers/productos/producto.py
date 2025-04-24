from fastapi import APIRouter, Depends, HTTPException, status, Security, Query
from fastapi.responses import JSONResponse, Response
from fastapi.encoders import jsonable_encoder
from fastapi import File, UploadFile, Form
from sqlalchemy.orm import Session
from db.database import SessionLocal, engine, get_db
from models.data import Producto
from schemas.producto import ProductoBase, ProductoConsumo, ProductoRecomendar, DeleteRequest
from schemas.user import User_InDB
from security.auth import get_current_active_user, get_current_user
from typing_extensions import Annotated
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
import pandas as pd
from engine.recomendador import recomendar_productos 



router = APIRouter()

# Ruta para crear un producto
@router.post("/crear_producto_temp/", status_code=status.HTTP_201_CREATED)
async def crear_producto_temp(
				current_user: Annotated[User_InDB, Security(get_current_user, scopes=["admin"])],
				nombre_producto: str = Form(...), 
				desc_producto: str = Form(...), 
				imagen: UploadFile = File(...),
				db: Session = Depends(get_db)):
	
    producto = Producto(
		nombre_producto=nombre_producto, 
		desc_producto=desc_producto, 
		imagen_b64=await imagen.read())
	
    db.add(producto)
    db.commit()
    db.refresh(producto)
    return {"mensaje": "Producto creado con éxito", "id": producto.id_producto}

# Ruta para actualizar un producto
@router.put("/actualizar_producto_temp/{id}", status_code=status.HTTP_201_CREATED)
async def actualizar_producto_temp(
				current_user: Annotated[User_InDB, Security(get_current_user, scopes=["admin"])],
				id: str, 
				nombre_producto: str = Form(None), 
				desc_producto: str = Form(None), 
				imagen: UploadFile = File(None),
				db: Session = Depends(get_db)):
	
	print(nombre_producto)
	producto = db.query(Producto).filter(Producto.id_producto == id).first()
	if producto:
		if nombre_producto:
			producto.nombre_producto = nombre_producto
		if desc_producto:
			producto.desc_producto = desc_producto
		if imagen:
			producto.imagen_b64 = await imagen.read()
		db.commit()
		db.refresh(producto)
		return {"mensaje": "Producto actualizado con éxito"}
	return {"mensaje": "Producto no encontrado"}


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

@router.get("/leer_productos/", status_code=status.HTTP_201_CREATED)  
async def leer_productos(current_user: Annotated[User_InDB, Security(get_current_user, scopes=["cliente"])],
					skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):    
	return [{"id_producto": p.id_producto, "nombre_producto": p.nombre_producto, "desc_producto": p.desc_producto} 
            for p in db.query(Producto).all()]
	
@router.get("/leer_productos_libres/", status_code=status.HTTP_200_OK)  
async def leer_productos_libres(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):    
	return [{"id_producto": p.id_producto, "nombre_producto": p.nombre_producto, "desc_producto": p.desc_producto} 
            for p in db.query(Producto).all()]

@router.post("/leer_productos_recomendados/", status_code=status.HTTP_200_OK)  
async def leer_productos_recomendados(nombres: ProductoRecomendar,
				db: Session = Depends(get_db)):  
	descrip = []	  
	productos = db.query(Producto).all()
	for p in productos:
		print((p.nombre_producto, p.desc_producto))
		descrip.append((p.nombre_producto, p.desc_producto))
	df_productos = pd.DataFrame(data=descrip, columns=["nombre_producto","desc_producto"])
	df_productos = recomendar_productos(df_productos, nombres.nombres_productos, top_n=2)
	dictres = []
	for index, row in df_productos.iterrows():
		dictres.append({
			"nombre_producto": row.nombre_producto,
			"desc_producto": row.desc_producto
		})
	return dictres

@router.delete("/delete-productos/")
async def delete_items(request: DeleteRequest, db: Session = Depends(get_db)):
    indices_to_delete = request.indices
    items_to_delete = db.query(Producto).filter(
		Producto.id_producto.in_(indices_to_delete)).all()
    if not items_to_delete:
        raise HTTPException(status_code=404, detail="No items found to delete")
    for item in items_to_delete:
        db.delete(item)
    db.commit()
    return {"message": "Productos eliminados satisfactoriamente"}

# Ruta para obtener la imagen de un producto por ID
@router.get("/imagen/{id}")
async def obtener_imagen(id: str):
    db = SessionLocal()
    producto = db.query(Producto).filter(Producto.id_producto == id).first()
    if producto and producto.imagen_b64:
        return Response(content=producto.imagen_b64, media_type="image/jpeg")
    return {"mensaje": "Imagen no encontrada"}