from fastapi import FastAPI
from functools import lru_cache
from fastapi.middleware.cors import CORSMiddleware
from uuid import uuid4

import core.config as config
from routers.user import users
from routers.security import auth
from routers.productos import producto

#Create our main app "https://pp-back-end.onrender.com"
app = FastAPI()

app.include_router(auth.router)  #, prefix="/auth", tags=["auth"]
app.include_router(users.router, prefix="/usuario", tags=["usuario"])
app.include_router(producto.router, prefix="/producto", tags=["producto"])


# Allow these methods to be used
methods = ["GET", "POST", "PUT", "DELETE"]

# Only these headers are allowed
headers = ["Content-Type", "Authorization"]

app.add_middleware(
	CORSMiddleware,
	allow_origins=config.CORS_ORIGINS,
	allow_credentials=True,
	allow_methods=methods,
	allow_headers=["*"],
	expose_headers=["*"]
)

@app.get("/")
def index():
	return {"Aplicación": "Sistema de recomendación de productos hoteleros"}
	
