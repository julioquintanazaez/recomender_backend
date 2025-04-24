from db.database import SessionLocal, Base
from models.data import User
from sqlalchemy.exc import IntegrityError
from security.auth import get_password_hash

def create_user(session, username, password):
    """
    Crea un nuevo usuario en la base de datos.
    
    :param session: Sesión de la base de datos
    :param username: Nombre de usuario único
    :param role: Rol del usuario (dict)
    :param password: Contraseña del usuario (será hasheada)
    """
    try:
        nuevo_usuario = User(
            usuario=username,
            role=["admin", "cliente"],
            hashed_password=get_password_hash(password)
        )
        session.add(nuevo_usuario)
        session.commit()
        print(f"Usuario '{username}' creado con éxito.")
    except IntegrityError:
        session.rollback()
        print(f"Error: El nombre de usuario '{username}' ya existe.")
    except Exception as e:
        session.rollback()
        print(f"Error inesperado: {str(e)}")

if __name__ == "__main__":
    # Iniciar sesión con la base de datos
    db = SessionLocal()
    
    # Datos del nuevo usuario
    username = input("Ingrese el nombre de usuario: ")
    password = input("Ingrese la contraseña: ")
    
    # Crear el usuario
    create_user(db, username, password)
    
    # Cerrar la sesión
    db.close()
