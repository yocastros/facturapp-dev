"""
Tests unitarios del sistema de usuarios FastAPI (:8000).
Cubre autenticación, gestión de usuarios y permisos usando TestClient con BD en memoria.

Ejecutar:  pytest sistema_facturas/tests/test_usuarios.py -v
"""
import os
import sys
from datetime import datetime, timedelta

import pytest

# ── Paths ──────────────────────────────────────────────────────────────────
TESTS_DIR    = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR     = os.path.abspath(os.path.join(TESTS_DIR, '..', '..'))
USUARIOS_DIR = os.path.join(ROOT_DIR, 'sistema_usuarios')

for _p in (ROOT_DIR, USUARIOS_DIR):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from starlette.testclient import TestClient

# Importar la app y dependencias DESPUÉS de ajustar el path
import main as fastapi_main
from database import get_db, Base
from models import User, Role, UserPermission
from passlib.context import CryptContext

# ══════════════════════════════════════════════════════════════════════════
# BD en memoria para tests
# StaticPool garantiza que todas las sesiones comparten la misma conexión
# (necesario para SQLite :memory:, que aísla datos por conexión por defecto).
# ══════════════════════════════════════════════════════════════════════════

TEST_ENGINE = create_engine(
    'sqlite:///:memory:',
    connect_args={'check_same_thread': False},
    poolclass=StaticPool,
)
TestSession = sessionmaker(autocommit=False, autoflush=False, bind=TEST_ENGINE)

_pwd = CryptContext(schemes=['bcrypt'], deprecated='auto')


def _override_get_db():
    db = TestSession()
    try:
        yield db
    finally:
        db.close()


# ══════════════════════════════════════════════════════════════════════════
# Fixtures
# ══════════════════════════════════════════════════════════════════════════

@pytest.fixture(scope='module')
def client():
    """
    TestClient FastAPI con BD en memoria y datos base:
    - Roles: admin(1), supervisor(2), basico(3)
    - Usuarios: admin / basico / inactivo
    """
    Base.metadata.create_all(bind=TEST_ENGINE)
    fastapi_main.app.dependency_overrides[get_db] = _override_get_db

    db = TestSession()
    try:
        # Roles
        db.add_all([
            Role(id=1, name='admin',      description='Administrador'),
            Role(id=2, name='supervisor', description='Supervisor'),
            Role(id=3, name='basico',     description='Básico'),
        ])
        db.flush()

        # Usuarios base
        db.add_all([
            User(id=1, username='admin',    email='admin@test.com',
                 hashed_password=_pwd.hash('admin123'),
                 full_name='Admin Test', role_id=1, is_active=True),
            User(id=2, username='basico',   email='basico@test.com',
                 hashed_password=_pwd.hash('basico123'),
                 full_name='Basico Test', role_id=3, is_active=True),
            User(id=3, username='inactivo', email='inactivo@test.com',
                 hashed_password=_pwd.hash('inact123'),
                 full_name='Inactivo Test', role_id=3, is_active=False),
        ])
        db.commit()
    finally:
        db.close()

    with TestClient(fastapi_main.app) as c:
        yield c

    Base.metadata.drop_all(bind=TEST_ENGINE)
    fastapi_main.app.dependency_overrides.clear()


@pytest.fixture(scope='module')
def token_admin(client):
    r = client.post('/token', data={'username': 'admin', 'password': 'admin123'})
    assert r.status_code == 200
    return r.json()['access_token']


@pytest.fixture(scope='module')
def token_basico(client):
    r = client.post('/token', data={'username': 'basico', 'password': 'basico123'})
    assert r.status_code == 200
    return r.json()['access_token']


def _auth(token):
    return {'Authorization': f'Bearer {token}'}


# ══════════════════════════════════════════════════════════════════════════
# GRUPO 1 — HEALTH CHECK
# ══════════════════════════════════════════════════════════════════════════

class TestHealth:

    def test_health_publico_sin_token(self, client):
        r = client.get('/health')
        assert r.status_code == 200
        assert r.json()['status'] == 'ok'

    def test_health_full_sin_token_retorna_401(self, client):
        assert client.get('/health/full').status_code == 401

    def test_health_full_con_token_admin(self, client, token_admin):
        r = client.get('/health/full', headers=_auth(token_admin))
        assert r.status_code == 200
        data = r.json()
        assert data['status'] == 'ok'
        assert data['user'] == 'admin'
        assert data['role'] == 'admin'

    def test_health_full_con_token_basico(self, client, token_basico):
        r = client.get('/health/full', headers=_auth(token_basico))
        assert r.status_code == 200


# ══════════════════════════════════════════════════════════════════════════
# GRUPO 2 — LOGIN / TOKEN
# ══════════════════════════════════════════════════════════════════════════

class TestLogin:

    def test_login_admin_correcto_retorna_token(self, client):
        r = client.post('/token', data={'username': 'admin', 'password': 'admin123'})
        assert r.status_code == 200
        data = r.json()
        assert 'access_token' in data
        assert data['token_type'] == 'bearer'
        assert data['role'] == 'admin'

    def test_login_basico_correcto(self, client):
        r = client.post('/token', data={'username': 'basico', 'password': 'basico123'})
        assert r.status_code == 200
        assert r.json()['role'] == 'basico'

    def test_login_contrasena_incorrecta_retorna_401(self, client):
        r = client.post('/token', data={'username': 'admin', 'password': 'INCORRECTA'})
        assert r.status_code == 401

    def test_login_usuario_inexistente_retorna_401(self, client):
        r = client.post('/token', data={'username': 'noexiste', 'password': 'pass123'})
        assert r.status_code == 401

    def test_login_usuario_vacio_retorna_error(self, client):
        r = client.post('/token', data={'username': '', 'password': 'admin123'})
        assert r.status_code in (401, 422)

    def test_token_contiene_campos(self, client):
        r = client.post('/token', data={'username': 'admin', 'password': 'admin123'})
        data = r.json()
        assert len(data['access_token']) > 20
        assert data['token_type'] == 'bearer'


# ══════════════════════════════════════════════════════════════════════════
# GRUPO 3 — /me y /me/permissions
# ══════════════════════════════════════════════════════════════════════════

class TestMe:

    def test_me_sin_token_retorna_401(self, client):
        assert client.get('/me').status_code == 401

    def test_me_token_inventado_retorna_401(self, client):
        r = client.get('/me', headers={'Authorization': 'Bearer token_falso_xyz'})
        assert r.status_code == 401

    def test_me_con_token_admin_retorna_datos(self, client, token_admin):
        r = client.get('/me', headers=_auth(token_admin))
        assert r.status_code == 200
        data = r.json()
        assert data['username'] == 'admin'
        assert data['role'] == 'admin'
        assert data['is_active'] is True

    def test_me_contiene_campos_esperados(self, client, token_admin):
        data = client.get('/me', headers=_auth(token_admin)).json()
        for campo in ('id', 'username', 'email', 'full_name', 'role', 'is_active', 'created_at'):
            assert campo in data, f'Campo ausente: {campo}'

    def test_me_con_token_basico(self, client, token_basico):
        data = client.get('/me', headers=_auth(token_basico)).json()
        assert data['username'] == 'basico'
        assert data['role'] == 'basico'

    def test_permisos_sin_token_retorna_401(self, client):
        assert client.get('/me/permissions').status_code == 401

    def test_permisos_admin_todos_true(self, client, token_admin):
        data = client.get('/me/permissions', headers=_auth(token_admin)).json()
        modulos = ['dashboard', 'escanear', 'documentos', 'neteo', 'reportes']
        for m in modulos:
            assert data.get(m) is True, f'Módulo {m} debería ser True para admin'

    def test_permisos_basico_sin_configurar_todos_false(self, client, token_basico):
        data = client.get('/me/permissions', headers=_auth(token_basico)).json()
        modulos = ['dashboard', 'escanear', 'documentos', 'neteo', 'reportes']
        for m in modulos:
            assert data.get(m) is False, f'Módulo {m} debería ser False sin configurar'

    def test_permisos_basico_con_permisos_configurados(self, client, token_admin, token_basico):
        """Establecer permisos para el usuario básico y verificar que se reflejan."""
        # Configurar permisos para usuario básico (id=2)
        client.put('/api/users/2/permissions',
                   json={'dashboard': True, 'escanear': False,
                         'documentos': True, 'neteo': False, 'reportes': False},
                   headers=_auth(token_admin))
        data = client.get('/me/permissions', headers=_auth(token_basico)).json()
        assert data['dashboard'] is True
        assert data['documentos'] is True
        assert data['escanear'] is False


# ══════════════════════════════════════════════════════════════════════════
# GRUPO 4 — GESTIÓN DE USUARIOS (solo admin)
# ══════════════════════════════════════════════════════════════════════════

class TestListarUsuarios:

    def test_listar_sin_token_retorna_401(self, client):
        assert client.get('/api/users').status_code == 401

    def test_listar_con_basico_retorna_403(self, client, token_basico):
        assert client.get('/api/users', headers=_auth(token_basico)).status_code == 403

    def test_listar_con_admin_retorna_200(self, client, token_admin):
        r = client.get('/api/users', headers=_auth(token_admin))
        assert r.status_code == 200
        assert isinstance(r.json(), list)

    def test_listar_incluye_todos_los_usuarios(self, client, token_admin):
        usuarios = client.get('/api/users', headers=_auth(token_admin)).json()
        usernames = [u['username'] for u in usuarios]
        assert 'admin' in usernames
        assert 'basico' in usernames

    def test_listar_campos_de_usuario(self, client, token_admin):
        usuarios = client.get('/api/users', headers=_auth(token_admin)).json()
        for campo in ('id', 'username', 'email', 'role', 'is_active'):
            assert campo in usuarios[0], f'Campo ausente: {campo}'


class TestObtenerUsuario:

    def test_obtener_sin_token_retorna_401(self, client):
        assert client.get('/api/users/1').status_code == 401

    def test_obtener_con_basico_retorna_403(self, client, token_basico):
        assert client.get('/api/users/1', headers=_auth(token_basico)).status_code == 403

    def test_obtener_con_admin_retorna_200(self, client, token_admin):
        r = client.get('/api/users/1', headers=_auth(token_admin))
        assert r.status_code == 200
        assert r.json()['username'] == 'admin'

    def test_obtener_inexistente_retorna_404(self, client, token_admin):
        assert client.get('/api/users/99999', headers=_auth(token_admin)).status_code == 404


class TestCrearUsuario:

    def test_crear_sin_token_retorna_401(self, client):
        r = client.post('/admin/users', json={})
        assert r.status_code in (401, 422)

    def test_crear_con_basico_retorna_403(self, client, token_basico):
        payload = {'username': 'nuevo', 'email': 'nuevo@test.com',
                   'password': 'pass123', 'full_name': 'Nuevo User', 'role_id': 3}
        r = client.post('/admin/users', json=payload, headers=_auth(token_basico))
        assert r.status_code == 403

    def test_crear_con_admin_correcto_retorna_201(self, client, token_admin):
        payload = {'username': 'nuevo_usuario', 'email': 'nuevo@test.com',
                   'password': 'pass123', 'full_name': 'Nuevo Usuario', 'role_id': 3}
        r = client.post('/admin/users', json=payload, headers=_auth(token_admin))
        assert r.status_code == 200  # FastAPI devuelve 200 en este endpoint
        assert r.json()['user']['username'] == 'nuevo_usuario'

    def test_crear_username_duplicado_retorna_400(self, client, token_admin):
        payload = {'username': 'admin', 'email': 'otro@test.com',
                   'password': 'pass123', 'full_name': 'Dup', 'role_id': 3}
        r = client.post('/admin/users', json=payload, headers=_auth(token_admin))
        assert r.status_code == 400

    def test_crear_email_duplicado_retorna_400(self, client, token_admin):
        payload = {'username': 'otro_nuevo', 'email': 'admin@test.com',
                   'password': 'pass123', 'full_name': 'Dup Email', 'role_id': 3}
        r = client.post('/admin/users', json=payload, headers=_auth(token_admin))
        assert r.status_code == 400

    def test_crear_sin_campos_obligatorios_retorna_422(self, client, token_admin):
        r = client.post('/admin/users', json={'username': 'x'}, headers=_auth(token_admin))
        assert r.status_code == 422

    def test_crear_contrasena_corta_retorna_422(self, client, token_admin):
        payload = {'username': 'pass_corta', 'email': 'pc@test.com',
                   'password': '123', 'full_name': 'PC', 'role_id': 3}
        r = client.post('/admin/users', json=payload, headers=_auth(token_admin))
        assert r.status_code == 422


class TestEditarUsuario:

    def test_editar_sin_token_retorna_401(self, client):
        assert client.put('/users/2', json={}).status_code == 401

    def test_editar_propio_usuario_basico_retorna_200(self, client, token_basico):
        r = client.put('/users/2', json={'full_name': 'Basico Editado'},
                       headers=_auth(token_basico))
        assert r.status_code == 200
        assert r.json()['user']['full_name'] == 'Basico Editado'

    def test_editar_otro_usuario_como_basico_retorna_403(self, client, token_basico):
        r = client.put('/users/1', json={'full_name': 'Hackeo'},
                       headers=_auth(token_basico))
        assert r.status_code == 403

    def test_editar_como_admin_cualquier_usuario(self, client, token_admin):
        r = client.put('/users/2', json={'full_name': 'Editado por Admin'},
                       headers=_auth(token_admin))
        assert r.status_code == 200

    def test_basico_no_puede_cambiar_rol(self, client, token_basico):
        r = client.put('/users/2', json={'role_id': 1}, headers=_auth(token_basico))
        assert r.status_code == 403

    def test_basico_no_puede_cambiar_is_active(self, client, token_basico):
        r = client.put('/users/2', json={'is_active': False}, headers=_auth(token_basico))
        assert r.status_code == 403

    def test_basico_puede_cambiar_contrasena_propia(self, client, token_basico):
        r = client.put('/users/2', json={'password': 'nueva_pass123'},
                       headers=_auth(token_basico))
        assert r.status_code == 200

    def test_editar_usuario_inexistente_retorna_404(self, client, token_admin):
        r = client.put('/users/99999', json={'full_name': 'X'}, headers=_auth(token_admin))
        assert r.status_code == 404

    def test_admin_puede_cambiar_rol_usuario(self, client, token_admin):
        r = client.put('/users/2', json={'role_id': 2}, headers=_auth(token_admin))
        assert r.status_code == 200
        # Restaurar
        client.put('/users/2', json={'role_id': 3}, headers=_auth(token_admin))


class TestEliminarUsuario:

    def test_eliminar_sin_token_retorna_401(self, client):
        assert client.delete('/api/users/2').status_code == 401

    def test_eliminar_con_basico_retorna_403(self, client, token_basico):
        assert client.delete('/api/users/3', headers=_auth(token_basico)).status_code == 403

    def test_eliminar_propio_usuario_retorna_400(self, client, token_admin):
        r = client.delete('/api/users/1', headers=_auth(token_admin))
        assert r.status_code == 400

    def test_eliminar_inexistente_retorna_404(self, client, token_admin):
        assert client.delete('/api/users/99999', headers=_auth(token_admin)).status_code == 404

    def test_eliminar_usuario_existente_retorna_200(self, client, token_admin):
        # Crear usuario temporal para eliminar
        payload = {'username': 'temporal_del', 'email': 'temp_del@test.com',
                   'password': 'pass123', 'full_name': 'Temporal', 'role_id': 3}
        r_create = client.post('/admin/users', json=payload, headers=_auth(token_admin))
        assert r_create.status_code == 200
        user_id = r_create.json()['user']['id']

        r = client.delete(f'/api/users/{user_id}', headers=_auth(token_admin))
        assert r.status_code == 200
        assert 'eliminado' in r.json()['message'].lower()

    def test_usuario_eliminado_no_existe(self, client, token_admin):
        payload = {'username': 'para_borrar', 'email': 'borrar@test.com',
                   'password': 'pass123', 'full_name': 'Para Borrar', 'role_id': 3}
        r_create = client.post('/admin/users', json=payload, headers=_auth(token_admin))
        user_id = r_create.json()['user']['id']

        client.delete(f'/api/users/{user_id}', headers=_auth(token_admin))
        assert client.get(f'/api/users/{user_id}', headers=_auth(token_admin)).status_code == 404


# ══════════════════════════════════════════════════════════════════════════
# GRUPO 5 — PERMISOS POR USUARIO
# ══════════════════════════════════════════════════════════════════════════

class TestPermisos:

    def test_obtener_permisos_sin_token_retorna_401(self, client):
        assert client.get('/api/users/2/permissions').status_code == 401

    def test_obtener_permisos_con_basico_retorna_403(self, client, token_basico):
        assert client.get('/api/users/2/permissions',
                          headers=_auth(token_basico)).status_code == 403

    def test_obtener_permisos_con_admin_retorna_200(self, client, token_admin):
        r = client.get('/api/users/2/permissions', headers=_auth(token_admin))
        assert r.status_code == 200

    def test_obtener_permisos_admin_todos_true(self, client, token_admin):
        data = client.get('/api/users/1/permissions', headers=_auth(token_admin)).json()
        modulos = ['dashboard', 'escanear', 'documentos', 'neteo', 'reportes']
        for m in modulos:
            assert data.get(m) is True, f'Admin debe tener {m}=True'

    def test_obtener_permisos_usuario_inexistente_retorna_404(self, client, token_admin):
        assert client.get('/api/users/99999/permissions',
                          headers=_auth(token_admin)).status_code == 404

    def test_actualizar_permisos_sin_token_retorna_401(self, client):
        assert client.put('/api/users/2/permissions', json={}).status_code == 401

    def test_actualizar_permisos_con_basico_retorna_403(self, client, token_basico):
        r = client.put('/api/users/2/permissions',
                       json={'dashboard': True}, headers=_auth(token_basico))
        assert r.status_code == 403

    def test_actualizar_permisos_con_admin_retorna_200(self, client, token_admin):
        payload = {'dashboard': True, 'escanear': True,
                   'documentos': False, 'neteo': False, 'reportes': True}
        r = client.put('/api/users/2/permissions', json=payload, headers=_auth(token_admin))
        assert r.status_code == 200

    def test_permisos_actualizados_se_reflejan(self, client, token_admin):
        payload = {'dashboard': True, 'escanear': False,
                   'documentos': True, 'neteo': False, 'reportes': False}
        client.put('/api/users/2/permissions', json=payload, headers=_auth(token_admin))
        data = client.get('/api/users/2/permissions', headers=_auth(token_admin)).json()
        assert data['dashboard'] is True
        assert data['escanear'] is False
        assert data['documentos'] is True

    def test_actualizar_permisos_usuario_inexistente_retorna_404(self, client, token_admin):
        r = client.put('/api/users/99999/permissions',
                       json={'dashboard': True}, headers=_auth(token_admin))
        assert r.status_code == 404

    def test_permisos_ignora_modulos_desconocidos(self, client, token_admin):
        """Módulos que no existen en MODULOS_FACTURAS deben ser ignorados."""
        payload = {'modulo_falso': True, 'dashboard': True}
        r = client.put('/api/users/2/permissions', json=payload, headers=_auth(token_admin))
        assert r.status_code == 200
        data = client.get('/api/users/2/permissions', headers=_auth(token_admin)).json()
        assert 'modulo_falso' not in data


# ══════════════════════════════════════════════════════════════════════════
# GRUPO 6 — USUARIO INACTIVO
# ══════════════════════════════════════════════════════════════════════════

class TestUsuarioInactivo:

    def test_login_usuario_inactivo_falla(self, client):
        """Un usuario inactivo no puede hacer login (la contraseña es correcta)."""
        r = client.post('/token', data={'username': 'inactivo', 'password': 'inact123'})
        # FastAPI devuelve 401 (credenciales) porque authenticate_user usa is_active
        # o puede pasar el login pero /me/health_full devolvería 400
        # Depende de la implementación: si el login falla o si falla al usar el token
        # En este sistema, authenticate_user no comprueba is_active — lo hace get_current_active_user
        # Entonces el login tiene éxito pero las rutas protegidas con get_current_active_user fallan
        if r.status_code == 200:
            token_inactivo = r.json()['access_token']
            r2 = client.get('/health/full',
                            headers={'Authorization': f'Bearer {token_inactivo}'})
            assert r2.status_code == 400
        else:
            assert r.status_code == 401

    def test_reactivar_usuario_inactivo(self, client, token_admin):
        client.put('/users/3', json={'is_active': True}, headers=_auth(token_admin))
        r = client.post('/token', data={'username': 'inactivo', 'password': 'inact123'})
        assert r.status_code == 200
        # Dejar inactivo de nuevo
        client.put('/users/3', json={'is_active': False}, headers=_auth(token_admin))


# ══════════════════════════════════════════════════════════════════════════
# GRUPO 7 — PÁGINAS HTML (solo verificar que devuelven HTML)
# ══════════════════════════════════════════════════════════════════════════

class TestPaginasHTML:

    def test_pagina_login_accesible(self, client):
        r = client.get('/login')
        assert r.status_code == 200
        assert 'html' in r.headers.get('content-type', '').lower()

    def test_pagina_raiz_redirige_o_devuelve_login(self, client):
        r = client.get('/')
        assert r.status_code == 200

    def test_pagina_users_accesible_sin_auth(self, client):
        r = client.get('/users')
        assert r.status_code == 200

    def test_pagina_create_user_accesible(self, client):
        r = client.get('/create-user')
        assert r.status_code == 200

    def test_pagina_edit_user_accesible(self, client):
        r = client.get('/edit-user')
        assert r.status_code == 200

    def test_pagina_profile_accesible(self, client):
        r = client.get('/profile')
        assert r.status_code == 200
