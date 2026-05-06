"""
Fixtures compartidas para los tests unitarios del backend Flask.
No requieren servidores en ejecución — usan TestClient con BD en memoria.
"""
import os
import sys
import tempfile
from datetime import datetime, timedelta

import pytest

# ── Rutas ──────────────────────────────────────────────────────────────────
TESTS_DIR   = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR    = os.path.abspath(os.path.join(TESTS_DIR, '..', '..'))
BACKEND_DIR = os.path.join(ROOT_DIR, 'backend')

for _p in (ROOT_DIR, BACKEND_DIR):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import jwt as pyjwt


# ── Helpers de tokens ──────────────────────────────────────────────────────

def _jwt_secret():
    import app as m
    return m._JWT_SECRET


def token_valido(username='testuser', role='admin', exp_min=60):
    """Genera token JWT firmado con el mismo secreto que usa la app."""
    payload = {
        'sub': username,
        'role': role,
        'exp': datetime.utcnow() + timedelta(minutes=exp_min),
    }
    return pyjwt.encode(payload, _jwt_secret(), algorithm='HS256')


def token_expirado(username='testuser', role='admin'):
    payload = {
        'sub': username,
        'role': role,
        'exp': datetime.utcnow() - timedelta(minutes=5),
    }
    return pyjwt.encode(payload, _jwt_secret(), algorithm='HS256')


def cabeceras(tok):
    return {'Authorization': f'Bearer {tok}'}


def auth_admin():
    return cabeceras(token_valido('admin_test', 'admin'))


def auth_basico():
    return cabeceras(token_valido('basico_test', 'basico'))


# ── Fixture de app (sesión) ─────────────────────────────────────────────────

@pytest.fixture(scope='session')
def flask_app():
    """
    Configura la app Flask con una BD SQLite temporal para toda la sesión
    de tests. Limpia el archivo al finalizar.
    """
    import importlib.util as _ilu

    # Durante la colección del pytest, test_usuarios.py registra
    # sistema_usuarios/models.py como sys.modules['models'].
    # Debemos forzar backend/models.py antes de importar app.py
    # para que su 'from models import db, Documento...' resuelva correctamente.
    _spec = _ilu.spec_from_file_location('models', os.path.join(BACKEND_DIR, 'models.py'))
    _backend_models = _ilu.module_from_spec(_spec)
    sys.modules['models'] = _backend_models
    _spec.loader.exec_module(_backend_models)

    # Asegurar que BACKEND_DIR está al frente de sys.path
    while BACKEND_DIR in sys.path:
        sys.path.remove(BACKEND_DIR)
    sys.path.insert(0, BACKEND_DIR)

    import app as m
    from models import db

    fd, db_path = tempfile.mkstemp(suffix='.db', prefix='test_facturas_')

    m.app.config['TESTING'] = True
    m.app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'

    # Flask-SQLAlchemy 3.1 prohíbe llamar init_app dos veces sobre la misma app.
    # Eliminamos el registro previo para poder reinicializar con la nueva URI de tests.
    m.app.extensions.pop('sqlalchemy', None)
    db.init_app(m.app)

    with m.app.app_context():
        db.create_all()

    yield m.app

    with m.app.app_context():
        db.session.remove()
        db.drop_all()

    os.close(fd)
    os.unlink(db_path)


# ── Fixture de cliente (función) ───────────────────────────────────────────

@pytest.fixture()
def client(flask_app):
    """
    TestClient Flask con tablas vaciadas al inicio de cada test
    para garantizar aislamiento.
    """
    from models import db
    with flask_app.app_context():
        db.session.remove()
        db.drop_all()
        db.create_all()
    with flask_app.test_client() as c:
        yield c


# ── Helpers de creación de datos (usan la API) ─────────────────────────────

def crear_proveedor(client, nombre='Proveedor Test SA', cif='B12345678', **kwargs):
    """Crea un proveedor mediante la API y devuelve el JSON de respuesta."""
    payload = {'nombre': nombre, 'cif': cif, **kwargs}
    r = client.post('/api/proveedores', json=payload, headers=auth_admin())
    assert r.status_code == 201, f'Error creando proveedor: {r.get_json()}'
    return r.get_json()


def crear_documento(client, tipo='factura', numero='FAC-001', proveedor='Empresa SL',
                    total=121.0, estado='PROCESADO', **kwargs):
    """Inserta un documento directamente en la BD y devuelve su dict."""
    import app as m
    with m.app.app_context():
        doc = m.Documento(
            tipo=tipo, numero=numero, proveedor=proveedor,
            total=total, estado=estado,
            fecha='01/01/2025',
            **kwargs
        )
        m.db.session.add(doc)
        m.db.session.commit()
        return doc.to_dict()
