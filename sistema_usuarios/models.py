# models.py
# Aquí definimos las tablas de la base de datos

from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from database import Base

# ==================== TABLA DE ROLES ====================

class Role(Base):
    """Rol de acceso (admin, supervisor, basico)."""

    __tablename__ = "roles"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    description = Column(String)
    
    # Relación: un rol tiene muchos usuarios
    users = relationship("User", back_populates="role")


# ==================== TABLA DE USUARIOS ====================

class User(Base):
    """Usuario del sistema con credenciales, rol y permisos por módulo."""

    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)  # Contraseña encriptada
    full_name = Column(String, nullable=True)
    role_id = Column(Integer, ForeignKey("roles.id"), default=3)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_login = Column(DateTime, nullable=True)

    role = relationship("Role", back_populates="users")
    permissions = relationship("UserPermission", back_populates="user", cascade="all, delete-orphan")


# ==================== TABLA DE PERMISOS POR USUARIO ====================

class UserPermission(Base):
    """Permiso explícito de un usuario sobre un módulo concreto del sistema."""

    __tablename__ = "user_permissions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"))
    module = Column(String)       # 'dashboard','escanear','documentos','neteo','reportes'
    can_access = Column(Boolean, default=True)

    user = relationship("User", back_populates="permissions")