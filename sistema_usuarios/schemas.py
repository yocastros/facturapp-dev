# schemas.py
# Esquemas de validación con Pydantic

from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime


# ==================== ROLES ====================

class RoleBase(BaseModel):
    name: str
    description: Optional[str] = None


class Role(RoleBase):
    id: int
    
    class Config:
        from_attributes = True


# ==================== USUARIOS ====================

class UserBase(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    full_name: Optional[str] = None
    is_active: bool = True


class UserCreate(UserBase):
    """Para crear nuevo usuario"""
    password: str = Field(..., min_length=6)
    role_id: int = 3  # Por defecto básico


class UserUpdate(BaseModel):
    """Para actualizar usuario (todos los campos opcionales)"""
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    role_id: Optional[int] = None
    is_active: Optional[bool] = None
    password: Optional[str] = Field(None, min_length=6)  # Opcional para cambiar contraseña
    
    class Config:
        from_attributes = True


class User(UserBase):
    """Para mostrar usuario (respuesta de API)"""
    id: int
    role_id: int
    created_at: datetime
    last_login: Optional[datetime] = None
    role: Optional[Role] = None
    
    class Config:
        from_attributes = True


# ==================== AUTH ====================

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: str


class TokenData(BaseModel):
    username: Optional[str] = None
    role: Optional[str] = None


class LoginRequest(BaseModel):
    username: str
    password: str


# ==================== PERMISOS ====================

MODULOS_FACTURAS = ['dashboard', 'escanear', 'documentos', 'neteo', 'reportes']

class ModulePermission(BaseModel):
    module: str
    can_access: bool

class UserPermissionsUpdate(BaseModel):
    permissions: dict  # {'dashboard': True, 'escanear': False, ...}


# ==================== RESPUESTAS ====================

class MessageResponse(BaseModel):
    message: str
    success: bool = True