# main.py
# Archivo principal - API de usuarios con protección por roles

from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse, RedirectResponse
import os

# Importamos nuestros archivos
from database import get_db
from models import User, Role, UserPermission
from schemas import UserCreate, UserUpdate, MODULOS_FACTURAS

# Configuración de seguridad
SECRET_KEY = "clave-secreta-muy-larga-cambiar-en-produccion"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 480  # 8 horas (jornada laboral completa)

# Para encriptar contraseñas
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Esquema de autenticación OAuth2
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# Crear la aplicación FastAPI
app = FastAPI(
    title="Sistema de Usuarios HORECA",
    description="API de autenticación con roles",
    version="1.0.0"
)

# CORS: permite que el sistema de facturas (puerto 5000) consulte esta API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5000", "http://127.0.0.1:5000",
                   "C:/FacturasAlbaranes", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configurar templates
BASE_DIR = os.path.dirname(os.path.abspath(__file__))


# ==================== FUNCIONES AUXILIARES ====================

def verify_password(plain_password, hashed_password):
    """Verifica si la contraseña coincide con el hash"""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password):
    """Crea hash de una contraseña"""
    return pwd_context.hash(password)


def authenticate_user(db: Session, username: str, password: str):
    """Busca usuario y verifica contraseña"""
    user = db.query(User).filter(User.username == username).first()
    if not user:
        return False
    if not verify_password(password, user.hashed_password):
        return False
    return user


def create_access_token(data: dict, expires_delta=None):
    """Crea token JWT"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


async def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    """Obtiene usuario actual desde el token"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Credenciales inválidas",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    user = db.query(User).filter(User.username == username).first()
    if user is None:
        raise credentials_exception
    return user


async def get_current_active_user(current_user: User = Depends(get_current_user)):
    """Verifica que el usuario esté activo"""
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Usuario inactivo")
    return current_user


# ==================== HEALTH CHECK ====================

@app.get("/health")
async def health():
    return {"status": "ok"}

@app.get("/health/full")
async def health_full(current_user: User = Depends(get_current_active_user)):
    """Health check autenticado — confirma que el token es válido."""
    return {
        "status": "ok",
        "user": current_user.username,
        "role": current_user.role.name
    }


# ==================== RUTAS DE AUTENTICACIÓN ====================

@app.post("/token")
async def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """
    Login con username y password.
    Devuelve token JWT.
    """
    user = authenticate_user(db, form_data.username, form_data.password)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuario o contraseña incorrectos",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Actualizar último login
    user.last_login = datetime.utcnow()
    db.commit()
    
    # Crear token
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username, "role": user.role.name},
        expires_delta=access_token_expires
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "role": user.role.name
    }


@app.get("/me")
async def read_users_me(current_user: User = Depends(get_current_user)):
    """
    Obtiene información del usuario logueado.
    Requiere token válido.
    """
    return {
        "id": current_user.id,
        "username": current_user.username,
        "email": current_user.email,
        "full_name": current_user.full_name,
        "role": current_user.role.name,
        "is_active": current_user.is_active,
        "created_at": current_user.created_at
    }


# ==================== LISTAR USUARIOS (SOLO ADMIN) ====================

@app.get("/api/users")
async def list_users(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Obtener lista de todos los usuarios.
    SOLO ADMIN puede ver el listado completo.
    """
    # Verificar que sea admin
    if current_user.role.name != "admin":
        raise HTTPException(
            status_code=403,
            detail="Solo administradores pueden ver el listado de usuarios"
        )
    
    users = db.query(User).all()
    
    return [
        {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "full_name": user.full_name,
            "role": user.role.name,
            "is_active": user.is_active,
            "created_at": user.created_at
        }
        for user in users
    ]


# ==================== OBTENER USUARIO POR ID (SOLO ADMIN) ====================

@app.get("/api/users/{user_id}")
async def get_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Obtener información de un usuario específico.
    SOLO ADMIN puede ver información de otros usuarios.
    """
    # Verificar que sea admin
    if current_user.role.name != "admin":
        raise HTTPException(
            status_code=403,
            detail="Solo administradores pueden ver información de otros usuarios"
        )
    
    user = db.query(User).filter(User.id == user_id).first()
    
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    
    return {
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "full_name": user.full_name,
        "role": user.role.name,
        "is_active": user.is_active,
        "created_at": user.created_at
    }


# ==================== EDITAR USUARIO ====================

@app.put("/users/{user_id}")
async def update_user(
    user_id: int,
    user_update: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Editar un usuario existente.
    - ADMIN puede editar a cualquier usuario (incluyendo contraseñas)
    - Usuarios normales SOLO pueden editarse a sí mismos (email, nombre, y su propia contraseña)
    """
    
    # Buscar el usuario a editar
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    
    # Verificar permisos: si no es admin, solo puede editarse a sí mismo
    if current_user.role.name != "admin" and current_user.id != user_id:
        raise HTTPException(
            status_code=403, 
            detail="No tienes permiso para editar este usuario"
        )
    
    # Los usuarios normales NO pueden cambiar su rol
    if current_user.role.name != "admin" and user_update.role_id is not None:
        raise HTTPException(
            status_code=403,
            detail="No puedes cambiar tu rol"
        )
    
    # Los usuarios normales NO pueden cambiar su estado (activar/desactivar)
    if current_user.role.name != "admin" and user_update.is_active is not None:
        raise HTTPException(
            status_code=403,
            detail="No puedes cambiar tu estado de activación"
        )
    
    # NOTA: Los usuarios normales SÍ pueden cambiar su propia contraseña
    # (se valida en el frontend que sea su propia contraseña)
    
    # Actualizar campos
    update_data = user_update.dict(exclude_unset=True)
    
    # Manejar cambio de contraseña si se proporcionó
    if "password" in update_data and update_data["password"]:
        user.hashed_password = get_password_hash(update_data["password"])
        del update_data["password"]
    
    # Actualizar el resto de campos
    for field, value in update_data.items():
        setattr(user, field, value)
    
    db.commit()
    db.refresh(user)
    
    return {
        "message": "Usuario actualizado correctamente",
        "user": {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "full_name": user.full_name,
            "role": user.role.name,
            "is_active": user.is_active
        }
    }


# ==================== CREAR USUARIO (SOLO ADMIN) ====================

@app.post("/admin/users")
async def create_user_admin(
    user_data: UserCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Crear nuevo usuario (solo admin).
    """
    # Verificar que sea admin
    if current_user.role.name != "admin":
        raise HTTPException(
            status_code=403,
            detail="Solo administradores pueden crear usuarios"
        )
    
    # Verificar que no exista el username
    existing_user = db.query(User).filter(User.username == user_data.username).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="El usuario ya existe")
    
    # Verificar que no exista el email
    existing_email = db.query(User).filter(User.email == user_data.email).first()
    if existing_email:
        raise HTTPException(status_code=400, detail="El email ya está registrado")
    
    # Crear hash de contraseña
    hashed_password = get_password_hash(user_data.password)
    
    # Crear usuario
    new_user = User(
        username=user_data.username,
        email=user_data.email,
        hashed_password=hashed_password,
        full_name=user_data.full_name,
        role_id=user_data.role_id,
        is_active=user_data.is_active
    )
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    return {
        "message": "Usuario creado exitosamente",
        "user": {
            "id": new_user.id,
            "username": new_user.username,
            "email": new_user.email,
            "full_name": new_user.full_name,
            "role": new_user.role.name
        }
    }


# ==================== ELIMINAR USUARIO (SOLO ADMIN) ====================

@app.delete("/api/users/{user_id}")
async def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Eliminar un usuario (solo admin).
    """
    # Verificar que sea admin
    if current_user.role.name != "admin":
        raise HTTPException(
            status_code=403,
            detail="Solo administradores pueden eliminar usuarios"
        )
    
    # No permitir eliminarse a sí mismo
    if current_user.id == user_id:
        raise HTTPException(
            status_code=400,
            detail="No puedes eliminar tu propio usuario"
        )
    
    # Buscar usuario
    user = db.query(User).filter(User.id == user_id).first()
    
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    
    # Eliminar usuario
    db.delete(user)
    db.commit()
    
    return {"message": f"Usuario '{user.username}' eliminado correctamente"}


# ==================== PERMISOS POR USUARIO ====================

@app.get("/me/permissions")
async def get_my_permissions(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Devuelve los permisos del usuario logueado sobre el sistema de facturas."""
    # Admin siempre tiene acceso total
    if current_user.role.name == "admin":
        return {m: True for m in MODULOS_FACTURAS}

    perms = db.query(UserPermission).filter(UserPermission.user_id == current_user.id).all()
    base = {m: False for m in MODULOS_FACTURAS}
    for p in perms:
        if p.module in base:
            base[p.module] = p.can_access
    return base


@app.get("/api/users/{user_id}/permissions")
async def get_user_permissions(
    user_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Obtiene los permisos de un usuario (solo admin)."""
    if current_user.role.name != "admin":
        raise HTTPException(status_code=403, detail="Solo administradores")

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    # Admin siempre tiene todo aunque no tenga filas en la tabla
    if user.role.name == "admin":
        return {m: True for m in MODULOS_FACTURAS}

    perms = db.query(UserPermission).filter(UserPermission.user_id == user_id).all()
    base = {m: False for m in MODULOS_FACTURAS}
    for p in perms:
        if p.module in base:
            base[p.module] = p.can_access
    return base


@app.put("/api/users/{user_id}/permissions")
async def set_user_permissions(
    user_id: int,
    permissions: dict,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Establece los permisos de un usuario (solo admin)."""
    if current_user.role.name != "admin":
        raise HTTPException(status_code=403, detail="Solo administradores")

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    db.query(UserPermission).filter(UserPermission.user_id == user_id).delete()
    for module, can_access in permissions.items():
        if module in MODULOS_FACTURAS:
            db.add(UserPermission(user_id=user_id, module=module, can_access=bool(can_access)))
    db.commit()
    return {"message": "Permisos actualizados correctamente"}


# ==================== PÁGINAS HTML (SIN PROTECCIÓN DE BACKEND) ====================
# La protección se hace en el frontend con JavaScript

@app.get("/", response_class=HTMLResponse)
async def root_page():
    """Página de inicio - login"""
    return FileResponse(os.path.join(BASE_DIR, "static", "login.html"))


@app.get("/login", response_class=HTMLResponse)
async def login_page():
    """Página de login"""
    return FileResponse(os.path.join(BASE_DIR, "static", "login.html"))


@app.get("/users", response_class=HTMLResponse)
async def users_list_page():
    """Página de listado de usuarios - La protección es en el frontend"""
    return FileResponse(os.path.join(BASE_DIR, "static", "users_list.html"))


@app.get("/create-user", response_class=HTMLResponse)
async def create_user_page():
    """Página para crear usuarios - La protección es en el frontend"""
    return FileResponse(os.path.join(BASE_DIR, "static", "create_user.html"))


@app.get("/edit-user", response_class=HTMLResponse)
async def edit_user_page():
    """Página para editar usuarios - La protección es en el frontend"""
    return FileResponse(os.path.join(BASE_DIR, "static", "edit_user.html"))


@app.get("/profile", response_class=HTMLResponse)
async def profile_page():
    """Página de Mi Perfil"""
    return FileResponse(os.path.join(BASE_DIR, "static", "profile.html"))


# Montar estáticos al final para que no interfiera con las rutas
app.mount("/static", StaticFiles(directory=os.path.join(BASE_DIR, "static")), name="static")


# Ejecutar si corremos este archivo directamente
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)