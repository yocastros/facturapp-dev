# init_db.py
# Este archivo crea las tablas y datos iniciales

from database import engine, Base, SessionLocal
from models import Role, User
from passlib.context import CryptContext

# Para encriptar contraseñas
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def init_database():
    """
    Crea todas las tablas y datos iniciales
    """
    print("🔄 Creando tablas...")
    
    # Crear tablas (si no existen)
    Base.metadata.create_all(bind=engine)
    
    # Crear sesión para insertar datos
    db = SessionLocal()
    
    try:
        # ========== INSERTAR ROLES ==========
        print("🔄 Creando roles...")
        
        roles_data = [
            {"id": 1, "name": "admin", "description": "Administrador - Control total del sistema"},
            {"id": 2, "name": "advanced", "description": "Usuario Avanzado - Crear y gestionar contenido"},
            {"id": 3, "name": "basic", "description": "Usuario Básico - Solo lectura y perfil"},
        ]
        
        for role_data in roles_data:
            # Verificar si ya existe
            existing = db.query(Role).filter(Role.id == role_data["id"]).first()
            if not existing:
                new_role = Role(**role_data)
                db.add(new_role)
                print(f"   ✅ Rol creado: {role_data['name']}")
            else:
                print(f"   ℹ️ Rol ya existe: {role_data['name']}")
        
        # Guardar roles
        db.commit()
        
        # ========== CREAR USUARIO ADMIN ==========
        print("🔄 Verificando usuario admin...")
        
        admin = db.query(User).filter(User.username == "admin").first()
        
        if not admin:
            # Crear hash de contraseña
            hashed_password = pwd_context.hash("admin123")
            
            admin_user = User(
                username="admin",
                email="admin@sistema.com",
                hashed_password=hashed_password,
                full_name="Administrador",
                role_id=1,  # admin
                is_active=True
            )
            
            db.add(admin_user)
            db.commit()
            
            print("   ✅ Usuario admin creado")
            print("   📧 Email: admin@sistema.com")
            print("   🔑 Contraseña: admin123")
        else:
            print("   ℹ️ Usuario admin ya existe")
        
        print("\n✅ Base de datos inicializada correctamente")
        print("🚀 Puedes iniciar el sistema")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        db.rollback()
    
    finally:
        db.close()


# Si ejecutamos este archivo directamente
if __name__ == "__main__":
    init_database()