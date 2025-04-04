from dotenv import load_dotenv
from os import getenv

#Load envirnment variables
load_dotenv()

ALGORITHM = getenv("ALGORITHM")
SECRET_KEY = getenv("SECRET_KEY")
APP_NAME = getenv("APP_NAME")
ACCESS_TOKEN_EXPIRE_MINUTES = getenv("ACCESS_TOKEN_EXPIRE_MINUTES")


CORS_ORIGINS = [	
	"https://recomender-frontend.onrender.com",		
    "http://recomender-frontend.onrender.com",		
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


DESCRIPTIONS_FILE: str = "engine/descripcion/descripciones.json"
STOPWORDS_FILE: str = "engine/stopwords/"