# database.py
# Este archivo conecta con la base de datos

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Usamos SQLite (archivo local, fácil para empezar)
SQLALCHEMY_DATABASE_URL = "sqlite:///./sistema_usuarios.db"

# Crear el motor de base de datos
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, 
    connect_args={"check_same_thread": False}
)

# Crear sesión para consultas
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base para crear modelos
Base = declarative_base()

# Función para obtener conexión a la base de datos
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()