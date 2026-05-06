"""
Tests unitarios del backend Flask (:5000).
Cubre autenticación, documentos, neteo, proveedores,
estadísticas, alertas y logs usando TestClient con BD temporal.

Ejecutar:  pytest sistema_facturas/tests/test_backend.py -v
"""
import io
import os
import sys
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock

import pytest

# ── Paths (conftest.py ya los añade, pero por si se ejecuta solo) ──────────
TESTS_DIR   = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR    = os.path.abspath(os.path.join(TESTS_DIR, '..', '..'))
BACKEND_DIR = os.path.join(ROOT_DIR, 'backend')
for _p in (ROOT_DIR, BACKEND_DIR):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from conftest import auth_admin, auth_basico, crear_documento, crear_proveedor, token_expirado


# ══════════════════════════════════════════════════════════════════════════
# GRUPO 1 — AUTENTICACIÓN / SEGURIDAD
# ══════════════════════════════════════════════════════════════════════════

class TestAutenticacion:

    def test_sin_cabecera_auth_retorna_401(self, client):
        r = client.get('/api/documentos')
        assert r.status_code == 401

    def test_cabecera_auth_vacia_retorna_401(self, client):
        r = client.get('/api/documentos', headers={'Authorization': ''})
        assert r.status_code == 401

    def test_token_inventado_retorna_401(self, client):
        r = client.get('/api/documentos',
                       headers={'Authorization': 'Bearer token_completamente_falso'})
        assert r.status_code == 401

    def test_token_mal_firmado_retorna_401(self, client):
        import jwt as pyjwt
        tok = pyjwt.encode({'sub': 'u', 'role': 'admin'}, 'clave_incorrecta', algorithm='HS256')
        r = client.get('/api/documentos', headers={'Authorization': f'Bearer {tok}'})
        assert r.status_code == 401

    def test_token_expirado_retorna_401(self, client):
        tok = token_expirado('admin_test', 'admin')
        r = client.get('/api/documentos', headers={'Authorization': f'Bearer {tok}'})
        assert r.status_code == 401

    def test_bearer_sin_token_retorna_401(self, client):
        r = client.get('/api/documentos', headers={'Authorization': 'Bearer '})
        assert r.status_code == 401

    def test_token_valido_admin_permite_acceso(self, client):
        r = client.get('/api/documentos', headers=auth_admin())
        assert r.status_code == 200

    def test_token_valido_basico_permite_acceso(self, client):
        r = client.get('/api/documentos', headers=auth_basico())
        assert r.status_code == 200


# ══════════════════════════════════════════════════════════════════════════
# GRUPO 2 — HEALTH CHECK
# ══════════════════════════════════════════════════════════════════════════

class TestHealth:

    def test_health_publico_sin_token(self, client):
        r = client.get('/api/health')
        assert r.status_code == 200

    def test_health_devuelve_status_ok(self, client):
        data = client.get('/api/health').get_json()
        assert data['status'] == 'ok'

    def test_health_devuelve_timestamp(self, client):
        data = client.get('/api/health').get_json()
        assert 'timestamp' in data
        # Debe ser parseable como ISO datetime
        datetime.fromisoformat(data['timestamp'])


# ══════════════════════════════════════════════════════════════════════════
# GRUPO 3 — ESTADÍSTICAS
# ══════════════════════════════════════════════════════════════════════════

class TestEstadisticas:

    def test_estadisticas_sin_token_retorna_401(self, client):
        assert client.get('/api/estadisticas').status_code == 401

    def test_estadisticas_con_token_retorna_200(self, client):
        assert client.get('/api/estadisticas', headers=auth_admin()).status_code == 200

    def test_estadisticas_contiene_campos_requeridos(self, client):
        data = client.get('/api/estadisticas', headers=auth_admin()).get_json()
        for campo in ('total_documentos', 'facturas', 'albaranes', 'procesados',
                      'pendientes', 'errores', 'neteados',
                      'importe_facturas', 'importe_albaranes', 'importe_total'):
            assert campo in data, f'Campo ausente: {campo}'

    def test_estadisticas_bd_vacia_todo_cero(self, client):
        data = client.get('/api/estadisticas', headers=auth_admin()).get_json()
        assert data['total_documentos'] == 0
        assert data['facturas'] == 0
        assert data['albaranes'] == 0

    def test_estadisticas_reflejan_documentos_creados(self, client, flask_app):
        crear_documento(client, tipo='factura', numero='FAC-STAT-001', total=100.0)
        crear_documento(client, tipo='albaran', numero='ALB-STAT-001', total=50.0)
        data = client.get('/api/estadisticas', headers=auth_admin()).get_json()
        assert data['total_documentos'] == 2
        assert data['facturas'] == 1
        assert data['albaranes'] == 1
        assert data['importe_facturas'] == 100.0
        assert data['importe_albaranes'] == 50.0

    def test_estadisticas_con_token_basico(self, client):
        assert client.get('/api/estadisticas', headers=auth_basico()).status_code == 200


# ══════════════════════════════════════════════════════════════════════════
# GRUPO 4 — DOCUMENTOS: LISTAR
# ══════════════════════════════════════════════════════════════════════════

class TestDocumentosListar:

    def test_listar_sin_token_retorna_401(self, client):
        assert client.get('/api/documentos').status_code == 401

    def test_listar_bd_vacia_retorna_lista_vacia(self, client):
        data = client.get('/api/documentos', headers=auth_admin()).get_json()
        assert data['documentos'] == []
        assert data['total'] == 0

    def test_listar_estructura_respuesta(self, client):
        data = client.get('/api/documentos', headers=auth_admin()).get_json()
        for campo in ('documentos', 'total', 'pagina', 'por_pagina', 'paginas'):
            assert campo in data

    def test_listar_con_documentos(self, client):
        crear_documento(client, tipo='factura', numero='FAC-L001')
        crear_documento(client, tipo='albaran', numero='ALB-L001')
        data = client.get('/api/documentos', headers=auth_admin()).get_json()
        assert data['total'] == 2

    def test_filtro_tipo_factura(self, client):
        crear_documento(client, tipo='factura', numero='FAC-F001')
        crear_documento(client, tipo='albaran', numero='ALB-F001')
        data = client.get('/api/documentos?tipo=factura', headers=auth_admin()).get_json()
        assert all(d['tipo'] == 'factura' for d in data['documentos'])
        assert data['total'] == 1

    def test_filtro_tipo_albaran(self, client):
        crear_documento(client, tipo='factura', numero='FAC-A001')
        crear_documento(client, tipo='albaran', numero='ALB-A001')
        data = client.get('/api/documentos?tipo=albaran', headers=auth_admin()).get_json()
        assert all(d['tipo'] == 'albaran' for d in data['documentos'])

    def test_filtro_estado_procesado(self, client):
        crear_documento(client, tipo='factura', numero='FAC-E001', estado='PROCESADO')
        crear_documento(client, tipo='factura', numero='FAC-E002', estado='PENDIENTE')
        data = client.get('/api/documentos?estado=PROCESADO', headers=auth_admin()).get_json()
        assert all(d['estado'] == 'PROCESADO' for d in data['documentos'])

    def test_filtro_busqueda_por_numero(self, client):
        crear_documento(client, tipo='factura', numero='BUSCAR-999')
        crear_documento(client, tipo='factura', numero='OTRO-001')
        data = client.get('/api/documentos?q=BUSCAR', headers=auth_admin()).get_json()
        assert data['total'] == 1
        assert data['documentos'][0]['numero'] == 'BUSCAR-999'

    def test_filtro_busqueda_por_proveedor(self, client):
        crear_documento(client, tipo='factura', numero='FAC-P001', proveedor='Acme Corp SA')
        crear_documento(client, tipo='factura', numero='FAC-P002', proveedor='Otra Empresa SL')
        data = client.get('/api/documentos?q=Acme', headers=auth_admin()).get_json()
        assert data['total'] == 1

    def test_paginacion_por_pagina(self, client):
        for i in range(5):
            crear_documento(client, tipo='factura', numero=f'FAC-PAG-{i:03d}')
        data = client.get('/api/documentos?por_pagina=2&pagina=1', headers=auth_admin()).get_json()
        assert len(data['documentos']) == 2
        assert data['total'] == 5
        assert data['paginas'] == 3

    def test_paginacion_segunda_pagina(self, client):
        for i in range(4):
            crear_documento(client, tipo='factura', numero=f'FAC-P2-{i:03d}')
        r1 = client.get('/api/documentos?por_pagina=2&pagina=1', headers=auth_admin()).get_json()
        r2 = client.get('/api/documentos?por_pagina=2&pagina=2', headers=auth_admin()).get_json()
        ids_p1 = {d['id'] for d in r1['documentos']}
        ids_p2 = {d['id'] for d in r2['documentos']}
        assert ids_p1.isdisjoint(ids_p2)


# ══════════════════════════════════════════════════════════════════════════
# GRUPO 5 — DOCUMENTOS: OBTENER / EDITAR / ELIMINAR
# ══════════════════════════════════════════════════════════════════════════

class TestDocumentoCRUD:

    def test_obtener_sin_token_retorna_401(self, client):
        assert client.get('/api/documentos/1').status_code == 401

    def test_obtener_inexistente_retorna_404(self, client):
        assert client.get('/api/documentos/99999', headers=auth_admin()).status_code == 404

    def test_obtener_existente_retorna_200(self, client):
        doc = crear_documento(client, numero='FAC-OBT-001')
        r = client.get(f'/api/documentos/{doc["id"]}', headers=auth_admin())
        assert r.status_code == 200
        data = r.get_json()
        assert data['id'] == doc['id']
        assert data['numero'] == 'FAC-OBT-001'

    def test_obtener_contiene_campos_completos(self, client):
        doc = crear_documento(client, numero='FAC-CAMPOS-001')
        data = client.get(f'/api/documentos/{doc["id"]}', headers=auth_admin()).get_json()
        for campo in ('id', 'tipo', 'numero', 'fecha', 'proveedor', 'cif',
                      'base_imponible', 'total', 'estado', 'albaranes_asociados', 'lineas'):
            assert campo in data, f'Campo ausente: {campo}'

    def test_editar_sin_token_retorna_401(self, client):
        assert client.put('/api/documentos/1', json={}).status_code == 401

    def test_editar_inexistente_retorna_404(self, client):
        r = client.put('/api/documentos/99999', json={'numero': 'X'}, headers=auth_admin())
        assert r.status_code == 404

    def test_editar_actualiza_campos(self, client):
        doc = crear_documento(client, numero='FAC-EDIT-001')
        r = client.put(f'/api/documentos/{doc["id"]}',
                       json={'numero': 'FAC-EDIT-002', 'total': 500.0},
                       headers=auth_admin())
        assert r.status_code == 200
        data = r.get_json()
        assert data['numero'] == 'FAC-EDIT-002'
        assert data['total'] == 500.0

    def test_editar_actualiza_solo_campos_enviados(self, client):
        doc = crear_documento(client, numero='FAC-PART-001', proveedor='Empresa Original SA')
        client.put(f'/api/documentos/{doc["id"]}',
                   json={'numero': 'FAC-PART-002'},
                   headers=auth_admin())
        r = client.get(f'/api/documentos/{doc["id"]}', headers=auth_admin())
        data = r.get_json()
        assert data['numero'] == 'FAC-PART-002'
        assert data['proveedor'] == 'Empresa Original SA'  # no modificado

    def test_eliminar_sin_token_retorna_401(self, client):
        assert client.delete('/api/documentos/1').status_code == 401

    def test_eliminar_inexistente_retorna_404(self, client):
        assert client.delete('/api/documentos/99999', headers=auth_admin()).status_code == 404

    def test_eliminar_existente_retorna_200(self, client):
        doc = crear_documento(client, numero='FAC-DEL-001')
        r = client.delete(f'/api/documentos/{doc["id"]}', headers=auth_admin())
        assert r.status_code == 200
        assert 'eliminado' in r.get_json().get('mensaje', '').lower()

    def test_eliminar_quita_el_documento(self, client):
        doc = crear_documento(client, numero='FAC-DEL-002')
        client.delete(f'/api/documentos/{doc["id"]}', headers=auth_admin())
        assert client.get(f'/api/documentos/{doc["id"]}', headers=auth_admin()).status_code == 404

    def test_eliminar_factura_desasocia_albaranes(self, client, flask_app):
        """Borrar una factura debe dejar sus albaranes libres (factura_id=None)."""
        import app as m
        from models import db, Documento
        with flask_app.app_context():
            fac = Documento(tipo='factura', numero='FAC-DASOC-001', estado='FACTURA_ASOCIADA')
            alb = Documento(tipo='albaran', numero='ALB-DASOC-001', estado='FACTURA_ASOCIADA')
            db.session.add_all([fac, alb])
            db.session.flush()
            alb.factura_id = fac.id
            db.session.commit()
            fac_id = fac.id
            alb_id = alb.id

        client.delete(f'/api/documentos/{fac_id}', headers=auth_admin())

        with flask_app.app_context():
            alb_post = Documento.query.get(alb_id)
            assert alb_post.factura_id is None
            assert alb_post.estado == 'PROCESADO'


# ══════════════════════════════════════════════════════════════════════════
# GRUPO 6 — ESCANEAR (con OCR mockeado)
# ══════════════════════════════════════════════════════════════════════════

class TestEscanear:

    def test_escanear_sin_token_retorna_401(self, client):
        r = client.post('/api/escanear', data={})
        assert r.status_code == 401

    def test_escanear_sin_archivo_retorna_400(self, client):
        r = client.post('/api/escanear', data={}, headers=auth_admin())
        assert r.status_code == 400

    def test_escanear_nombre_vacio_retorna_400(self, client):
        data = {'archivo': (io.BytesIO(b'data'), '')}
        r = client.post('/api/escanear', data=data,
                        content_type='multipart/form-data', headers=auth_admin())
        assert r.status_code == 400

    def test_escanear_formato_no_soportado_retorna_400(self, client):
        data = {'archivo': (io.BytesIO(b'data'), 'virus.exe')}
        r = client.post('/api/escanear', data=data,
                        content_type='multipart/form-data', headers=auth_admin())
        assert r.status_code == 400
        assert 'Formato no soportado' in r.get_json().get('error', '')

    def test_escanear_docx_retorna_400(self, client):
        data = {'archivo': (io.BytesIO(b'data'), 'informe.docx')}
        r = client.post('/api/escanear', data=data,
                        content_type='multipart/form-data', headers=auth_admin())
        assert r.status_code == 400

    def test_escanear_pdf_ocr_ok_retorna_201(self, client):
        ocr_mock = {
            'tipo': 'factura', 'numero': 'FAC-OCR-001', 'fecha': '01/01/2025',
            'proveedor': 'Empresa Mock SA', 'cif': 'B99990001',
            'base_imponible': 100.0, 'iva': 21.0, 'total': 121.0,
            'porcentaje_iva': 21.0, 'texto_ocr': 'Texto OCR simulado',
            'lineas': [], 'albaranes_referenciados': [],
        }
        with patch('app.procesar_documento', return_value=ocr_mock):
            data = {'archivo': (io.BytesIO(b'%PDF fake content'), 'factura.pdf')}
            r = client.post('/api/escanear', data=data,
                            content_type='multipart/form-data', headers=auth_admin())
        assert r.status_code == 201
        resp = r.get_json()
        assert resp['numero'] == 'FAC-OCR-001'
        assert resp['tipo'] == 'factura'

    def test_escanear_png_ocr_ok_retorna_201(self, client):
        ocr_mock = {
            'tipo': 'albaran', 'numero': 'ALB-OCR-001', 'fecha': '02/01/2025',
            'proveedor': 'Empresa Mock SA', 'cif': 'B99990001',
            'base_imponible': 80.0, 'iva': 0.0, 'total': 80.0,
            'porcentaje_iva': 0.0, 'texto_ocr': 'Albarán texto',
            'lineas': [], 'albaranes_referenciados': [],
        }
        with patch('app.procesar_documento', return_value=ocr_mock):
            data = {'archivo': (io.BytesIO(b'\x89PNG fake'), 'albaran.png')}
            r = client.post('/api/escanear', data=data,
                            content_type='multipart/form-data', headers=auth_admin())
        assert r.status_code == 201

    def test_escanear_ocr_retorna_estado_error_retorna_422(self, client):
        ocr_mock = {'estado': 'ERROR', 'error': 'No se pudo procesar el documento'}
        with patch('app.procesar_documento', return_value=ocr_mock):
            data = {'archivo': (io.BytesIO(b'fake'), 'factura.jpg')}
            r = client.post('/api/escanear', data=data,
                            content_type='multipart/form-data', headers=auth_admin())
        assert r.status_code == 422

    def test_escanear_ocr_lanza_excepcion_retorna_500(self, client):
        with patch('app.procesar_documento', side_effect=Exception('Error OCR grave')):
            data = {'archivo': (io.BytesIO(b'fake'), 'factura.pdf')}
            r = client.post('/api/escanear', data=data,
                            content_type='multipart/form-data', headers=auth_admin())
        assert r.status_code == 500

    def test_escanear_normaliza_proveedor_existente(self, client):
        """Si hay un proveedor con el mismo CIF, el doc queda vinculado."""
        crear_proveedor(client, nombre='Empresa Match SA', cif='B11110001')
        ocr_mock = {
            'tipo': 'factura', 'numero': 'FAC-NORM-001', 'fecha': '01/01/2025',
            'proveedor': 'Empresa Match SA', 'cif': 'B11110001',
            'base_imponible': 100.0, 'iva': 21.0, 'total': 121.0,
            'porcentaje_iva': 21.0, 'texto_ocr': 'texto',
            'lineas': [], 'albaranes_referenciados': [],
        }
        with patch('app.procesar_documento', return_value=ocr_mock):
            data = {'archivo': (io.BytesIO(b'%PDF'), 'factura_norm.pdf')}
            r = client.post('/api/escanear', data=data,
                            content_type='multipart/form-data', headers=auth_admin())
        assert r.status_code == 201
        assert r.get_json()['proveedor_normalizado'] is True


# ══════════════════════════════════════════════════════════════════════════
# GRUPO 7 — ARCHIVO ORIGINAL
# ══════════════════════════════════════════════════════════════════════════

class TestArchivoOriginal:

    def test_ver_archivo_sin_token_retorna_401(self, client):
        assert client.get('/api/documentos/1/archivo').status_code == 401

    def test_ver_archivo_documento_inexistente_retorna_404(self, client):
        r = client.get('/api/documentos/99999/archivo', headers=auth_admin())
        assert r.status_code == 404

    def test_ver_archivo_sin_ruta_retorna_404(self, client):
        doc = crear_documento(client, numero='FAC-ARC-001')
        r = client.get(f'/api/documentos/{doc["id"]}/archivo', headers=auth_admin())
        assert r.status_code == 404

    def test_ver_archivo_con_ruta_inexistente_retorna_404(self, client, flask_app):
        import app as m
        from models import db, Documento
        with flask_app.app_context():
            d = Documento(tipo='factura', numero='FAC-ARC-002',
                          archivo_original='uuid_que_no_existe.pdf')
            db.session.add(d)
            db.session.commit()
            doc_id = d.id
        r = client.get(f'/api/documentos/{doc_id}/archivo', headers=auth_admin())
        assert r.status_code == 404


# ══════════════════════════════════════════════════════════════════════════
# GRUPO 8 — NETEO
# ══════════════════════════════════════════════════════════════════════════

class TestNeteo:

    def test_sin_asociar_sin_token_retorna_401(self, client):
        assert client.get('/api/neteo/sin-asociar').status_code == 401

    def test_sin_asociar_con_token_retorna_200(self, client):
        r = client.get('/api/neteo/sin-asociar', headers=auth_admin())
        assert r.status_code == 200

    def test_sin_asociar_estructura_respuesta(self, client):
        data = client.get('/api/neteo/sin-asociar', headers=auth_admin()).get_json()
        assert 'facturas_sin_albaran' in data
        assert 'albaranes_sin_factura' in data

    def test_sin_asociar_incluye_facturas_procesadas(self, client):
        crear_documento(client, tipo='factura', numero='FAC-SA-001', estado='PROCESADO')
        data = client.get('/api/neteo/sin-asociar', headers=auth_admin()).get_json()
        nums = [d['numero'] for d in data['facturas_sin_albaran']]
        assert 'FAC-SA-001' in nums

    def test_sin_asociar_no_incluye_facturas_neteadas(self, client, flask_app):
        import app as m
        from models import db, Documento
        with flask_app.app_context():
            fac = Documento(tipo='factura', numero='FAC-NET-001', estado='FACTURA_ASOCIADA')
            db.session.add(fac)
            db.session.commit()
        data = client.get('/api/neteo/sin-asociar', headers=auth_admin()).get_json()
        nums = [d['numero'] for d in data['facturas_sin_albaran']]
        assert 'FAC-NET-001' not in nums

    def test_asociar_sin_token_retorna_401(self, client):
        assert client.post('/api/neteo/asociar', json={}).status_code == 401

    def test_asociar_sin_factura_id_retorna_400(self, client):
        r = client.post('/api/neteo/asociar', json={'albaran_ids': []}, headers=auth_admin())
        assert r.status_code == 400

    def test_asociar_factura_inexistente_retorna_404(self, client):
        r = client.post('/api/neteo/asociar',
                        json={'factura_id': 99999, 'albaran_ids': []},
                        headers=auth_admin())
        assert r.status_code == 404

    def test_asociar_albaran_a_factura_correctamente(self, client, flask_app):
        import app as m
        from models import db, Documento
        with flask_app.app_context():
            fac = Documento(tipo='factura', numero='FAC-ASOC-001', estado='PROCESADO')
            alb = Documento(tipo='albaran', numero='ALB-ASOC-001', estado='PROCESADO')
            db.session.add_all([fac, alb])
            db.session.commit()
            fac_id, alb_id = fac.id, alb.id

        r = client.post('/api/neteo/asociar',
                        json={'factura_id': fac_id, 'albaran_ids': [alb_id]},
                        headers=auth_admin())
        assert r.status_code == 200
        data = r.get_json()
        assert data['factura']['estado'] == 'FACTURA_ASOCIADA'
        assert len(data['asociados']) == 1

    def test_asociar_actualiza_estado_albaran(self, client, flask_app):
        import app as m
        from models import db, Documento
        with flask_app.app_context():
            fac = Documento(tipo='factura', numero='FAC-ASOC-002', estado='PROCESADO')
            alb = Documento(tipo='albaran', numero='ALB-ASOC-002', estado='PROCESADO')
            db.session.add_all([fac, alb])
            db.session.commit()
            fac_id, alb_id = fac.id, alb.id

        client.post('/api/neteo/asociar',
                    json={'factura_id': fac_id, 'albaran_ids': [alb_id]},
                    headers=auth_admin())

        with flask_app.app_context():
            alb_db = Documento.query.get(alb_id)
            assert alb_db.estado == 'FACTURA_ASOCIADA'
            assert alb_db.factura_id == fac_id

    def test_asociar_ids_de_tipo_incorrecto_no_cuenta(self, client, flask_app):
        """Un ID que apunta a una factura (no albarán) no debe asociarse."""
        import app as m
        from models import db, Documento
        with flask_app.app_context():
            fac1 = Documento(tipo='factura', numero='FAC-TIP-001', estado='PROCESADO')
            fac2 = Documento(tipo='factura', numero='FAC-TIP-002', estado='PROCESADO')
            db.session.add_all([fac1, fac2])
            db.session.commit()
            fac1_id, fac2_id = fac1.id, fac2.id

        r = client.post('/api/neteo/asociar',
                        json={'factura_id': fac1_id, 'albaran_ids': [fac2_id]},
                        headers=auth_admin())
        assert r.status_code == 200
        assert len(r.get_json()['asociados']) == 0

    def test_desasociar_sin_token_retorna_401(self, client):
        assert client.post('/api/neteo/desasociar/1').status_code == 401

    def test_desasociar_no_albaran_retorna_404(self, client, flask_app):
        import app as m
        from models import db, Documento
        with flask_app.app_context():
            fac = Documento(tipo='factura', numero='FAC-DESA-001')
            db.session.add(fac)
            db.session.commit()
            fac_id = fac.id
        r = client.post(f'/api/neteo/desasociar/{fac_id}', headers=auth_admin())
        assert r.status_code == 404

    def test_desasociar_inexistente_retorna_404(self, client):
        assert client.post('/api/neteo/desasociar/99999', headers=auth_admin()).status_code == 404

    def test_desasociar_albaran_libera_de_factura(self, client, flask_app):
        import app as m
        from models import db, Documento
        with flask_app.app_context():
            fac = Documento(tipo='factura', numero='FAC-LIB-001', estado='FACTURA_ASOCIADA')
            alb = Documento(tipo='albaran', numero='ALB-LIB-001', estado='FACTURA_ASOCIADA')
            db.session.add_all([fac, alb])
            db.session.flush()
            alb.factura_id = fac.id
            db.session.commit()
            fac_id, alb_id = fac.id, alb.id

        r = client.post(f'/api/neteo/desasociar/{alb_id}', headers=auth_admin())
        assert r.status_code == 200
        data = r.get_json()
        assert data['albaran']['factura_id'] is None
        assert data['albaran']['estado'] == 'PROCESADO'

    def test_desasociar_ultimo_albaran_reactiva_factura(self, client, flask_app):
        """Al desasociar el último albarán la factura vuelve a PROCESADO."""
        import app as m
        from models import db, Documento
        with flask_app.app_context():
            fac = Documento(tipo='factura', numero='FAC-REAC-001', estado='FACTURA_ASOCIADA')
            alb = Documento(tipo='albaran', numero='ALB-REAC-001', estado='FACTURA_ASOCIADA')
            db.session.add_all([fac, alb])
            db.session.flush()
            alb.factura_id = fac.id
            db.session.commit()
            fac_id, alb_id = fac.id, alb.id

        client.post(f'/api/neteo/desasociar/{alb_id}', headers=auth_admin())

        with flask_app.app_context():
            fac_db = Documento.query.get(fac_id)
            assert fac_db.estado == 'PROCESADO'


# ══════════════════════════════════════════════════════════════════════════
# GRUPO 9 — PROVEEDORES
# ══════════════════════════════════════════════════════════════════════════

class TestProveedoresListar:

    def test_listar_sin_token_retorna_401(self, client):
        assert client.get('/api/proveedores').status_code == 401

    def test_listar_bd_vacia(self, client):
        data = client.get('/api/proveedores', headers=auth_admin()).get_json()
        assert data['total'] == 0
        assert data['proveedores'] == []

    def test_listar_estructura_respuesta(self, client):
        data = client.get('/api/proveedores', headers=auth_admin()).get_json()
        for campo in ('proveedores', 'total', 'pagina', 'paginas'):
            assert campo in data

    def test_listar_muestra_proveedores_creados(self, client):
        crear_proveedor(client, nombre='Empresa A SL', cif='A11111111')
        crear_proveedor(client, nombre='Empresa B SA', cif='B22222222')
        data = client.get('/api/proveedores', headers=auth_admin()).get_json()
        assert data['total'] == 2

    def test_busqueda_por_nombre(self, client):
        crear_proveedor(client, nombre='Distribuciones Norte SL', cif='C33333333')
        crear_proveedor(client, nombre='Suministros Sur SA', cif='D44444444')
        data = client.get('/api/proveedores?q=Norte', headers=auth_admin()).get_json()
        assert data['total'] == 1
        assert 'Norte' in data['proveedores'][0]['nombre']

    def test_busqueda_por_cif(self, client):
        crear_proveedor(client, nombre='Empresa CIF Test', cif='E55555555')
        data = client.get('/api/proveedores?q=E55555555', headers=auth_admin()).get_json()
        assert data['total'] == 1

    def test_filtro_activo_true(self, client, flask_app):
        import app as m
        from models import db, Proveedor
        with flask_app.app_context():
            p_act = Proveedor(nombre='Activo SA', cif='F11111111', activo=True)
            p_ina = Proveedor(nombre='Inactivo SL', cif='G22222222', activo=False)
            db.session.add_all([p_act, p_ina])
            db.session.commit()
        data = client.get('/api/proveedores?activo=true', headers=auth_admin()).get_json()
        assert all(p['activo'] for p in data['proveedores'])

    def test_filtro_activo_false(self, client, flask_app):
        import app as m
        from models import db, Proveedor
        with flask_app.app_context():
            db.session.add(Proveedor(nombre='Inactivo2 SL', cif='H33333333', activo=False))
            db.session.commit()
        data = client.get('/api/proveedores?activo=false', headers=auth_admin()).get_json()
        assert all(not p['activo'] for p in data['proveedores'])


class TestProveedoresCRUD:

    def test_crear_sin_token_retorna_401(self, client):
        assert client.post('/api/proveedores', json={'nombre': 'X'}).status_code == 401

    def test_crear_sin_nombre_retorna_400(self, client):
        r = client.post('/api/proveedores', json={}, headers=auth_admin())
        assert r.status_code == 400

    def test_crear_nombre_vacio_retorna_400(self, client):
        r = client.post('/api/proveedores', json={'nombre': '  '}, headers=auth_admin())
        assert r.status_code == 400

    def test_crear_correcto_retorna_201(self, client):
        r = client.post('/api/proveedores',
                        json={'nombre': 'Nuevo Proveedor SA', 'cif': 'Z99999999'},
                        headers=auth_admin())
        assert r.status_code == 201

    def test_crear_devuelve_campos_completos(self, client):
        r = client.post('/api/proveedores',
                        json={'nombre': 'Completo SA', 'cif': 'Z88888888',
                              'email': 'info@completo.es', 'telefono': '912345678'},
                        headers=auth_admin())
        data = r.get_json()
        assert data['nombre'] == 'Completo SA'
        assert data['cif'] == 'Z88888888'
        assert data['email'] == 'info@completo.es'
        assert 'id' in data

    def test_crear_sin_cif_retorna_201(self, client):
        r = client.post('/api/proveedores', json={'nombre': 'Sin CIF SL'}, headers=auth_admin())
        assert r.status_code == 201
        assert r.get_json()['cif'] is None

    def test_crear_cif_duplicado_retorna_409(self, client):
        crear_proveedor(client, nombre='Primero SA', cif='DUP123456')
        r = client.post('/api/proveedores',
                        json={'nombre': 'Segundo SA', 'cif': 'DUP123456'},
                        headers=auth_admin())
        assert r.status_code == 409

    def test_obtener_sin_token_retorna_401(self, client):
        assert client.get('/api/proveedores/1').status_code == 401

    def test_obtener_inexistente_retorna_404(self, client):
        assert client.get('/api/proveedores/99999', headers=auth_admin()).status_code == 404

    def test_obtener_existente_retorna_200(self, client):
        p = crear_proveedor(client, nombre='Proveedor Get SA', cif='G11111110')
        r = client.get(f'/api/proveedores/{p["id"]}', headers=auth_admin())
        assert r.status_code == 200
        assert r.get_json()['id'] == p['id']

    def test_obtener_incluye_ultimos_documentos(self, client):
        p = crear_proveedor(client, nombre='Prov Docs SA', cif='G22222220')
        r = client.get(f'/api/proveedores/{p["id"]}', headers=auth_admin())
        assert 'ultimos_documentos' in r.get_json()

    def test_actualizar_sin_token_retorna_401(self, client):
        assert client.put('/api/proveedores/1', json={}).status_code == 401

    def test_actualizar_inexistente_retorna_404(self, client):
        r = client.put('/api/proveedores/99999', json={'nombre': 'X'}, headers=auth_admin())
        assert r.status_code == 404

    def test_actualizar_nombre_correcto(self, client):
        p = crear_proveedor(client, nombre='Antes SA', cif='G33333330')
        r = client.put(f'/api/proveedores/{p["id"]}',
                       json={'nombre': 'Despues SA'}, headers=auth_admin())
        assert r.status_code == 200
        assert r.get_json()['nombre'] == 'Despues SA'

    def test_actualizar_cif_duplicado_retorna_409(self, client):
        p1 = crear_proveedor(client, nombre='P1 SA', cif='G44444441')
        p2 = crear_proveedor(client, nombre='P2 SL', cif='G44444442')
        r = client.put(f'/api/proveedores/{p2["id"]}',
                       json={'cif': 'G44444441'}, headers=auth_admin())
        assert r.status_code == 409

    def test_actualizar_mismo_cif_no_falla(self, client):
        """Actualizar un proveedor con su propio CIF no debe retornar 409."""
        p = crear_proveedor(client, nombre='Mismo CIF SA', cif='G55555550')
        r = client.put(f'/api/proveedores/{p["id"]}',
                       json={'cif': 'G55555550', 'nombre': 'Mismo CIF SA V2'},
                       headers=auth_admin())
        assert r.status_code == 200

    def test_eliminar_sin_token_retorna_401(self, client):
        assert client.delete('/api/proveedores/1').status_code == 401

    def test_eliminar_inexistente_retorna_404(self, client):
        assert client.delete('/api/proveedores/99999', headers=auth_admin()).status_code == 404

    def test_eliminar_sin_documentos_retorna_200(self, client):
        p = crear_proveedor(client, nombre='Eliminar SA', cif='G66666660')
        r = client.delete(f'/api/proveedores/{p["id"]}', headers=auth_admin())
        assert r.status_code == 200

    def test_eliminar_con_documentos_retorna_409(self, client, flask_app):
        import app as m
        from models import db, Proveedor, Documento
        with flask_app.app_context():
            p = Proveedor(nombre='Prov Con Docs', cif='G77777770')
            db.session.add(p)
            db.session.flush()
            d = Documento(tipo='factura', numero='FAC-CON-001', proveedor_id=p.id)
            db.session.add(d)
            db.session.commit()
            p_id = p.id

        r = client.delete(f'/api/proveedores/{p_id}', headers=auth_admin())
        assert r.status_code == 409
        assert 'documento' in r.get_json()['error'].lower()


class TestProveedorDesdeDocumento:

    def test_sin_token_retorna_401(self, client):
        assert client.post('/api/proveedores/desde-documento/1').status_code == 401

    def test_documento_inexistente_retorna_404(self, client):
        r = client.post('/api/proveedores/desde-documento/99999', headers=auth_admin())
        assert r.status_code == 404

    def test_documento_ya_tiene_proveedor_retorna_409(self, client, flask_app):
        import app as m
        from models import db, Proveedor, Documento
        with flask_app.app_context():
            p = Proveedor(nombre='Ya Asignado SA', cif='G88888880')
            db.session.add(p)
            db.session.flush()
            d = Documento(tipo='factura', numero='FAC-YA-001',
                          proveedor='Ya Asignado SA', proveedor_id=p.id)
            db.session.add(d)
            db.session.commit()
            doc_id = d.id

        r = client.post(f'/api/proveedores/desde-documento/{doc_id}', headers=auth_admin())
        assert r.status_code == 409

    def test_crea_proveedor_desde_documento_sin_cif(self, client, flask_app):
        import app as m
        from models import db, Documento
        with flask_app.app_context():
            d = Documento(tipo='factura', numero='FAC-PDOC-001',
                          proveedor='Nuevo Prov Sin CIF')
            db.session.add(d)
            db.session.commit()
            doc_id = d.id

        r = client.post(f'/api/proveedores/desde-documento/{doc_id}', headers=auth_admin())
        assert r.status_code == 200
        data = r.get_json()
        assert data['proveedor']['nombre'] == 'Nuevo Prov Sin CIF'

    def test_reutiliza_proveedor_con_mismo_cif(self, client, flask_app):
        """Si ya existe un proveedor con el CIF del documento, lo reutiliza."""
        import app as m
        from models import db, Proveedor, Documento
        with flask_app.app_context():
            p = Proveedor(nombre='Reutilizar SA', cif='REUT-001')
            db.session.add(p)
            db.session.flush()
            d = Documento(tipo='factura', numero='FAC-REUT-001',
                          proveedor='Reutilizar SA', cif='REUT-001')
            db.session.add(d)
            db.session.commit()
            doc_id, p_id = d.id, p.id

        r = client.post(f'/api/proveedores/desde-documento/{doc_id}', headers=auth_admin())
        assert r.status_code == 200
        assert r.get_json()['proveedor']['id'] == p_id


# ══════════════════════════════════════════════════════════════════════════
# GRUPO 10 — ALERTAS
# ══════════════════════════════════════════════════════════════════════════

class TestAlertas:

    def test_alertas_sin_token_retorna_401(self, client):
        assert client.get('/api/alertas/sin-netear').status_code == 401

    def test_alertas_con_token_retorna_200(self, client):
        assert client.get('/api/alertas/sin-netear', headers=auth_admin()).status_code == 200

    def test_alertas_estructura_respuesta(self, client):
        data = client.get('/api/alertas/sin-netear', headers=auth_admin()).get_json()
        for campo in ('total', 'criticos', 'avisos', 'normales',
                      'importe_pendiente', 'documentos'):
            assert campo in data

    def test_alertas_bd_vacia_todo_cero(self, client):
        data = client.get('/api/alertas/sin-netear', headers=auth_admin()).get_json()
        assert data['total'] == 0
        assert data['importe_pendiente'] == 0.0

    def test_alertas_factura_neteada_no_aparece(self, client, flask_app):
        import app as m
        from models import db, Documento
        with flask_app.app_context():
            fac = Documento(tipo='factura', numero='FAC-NET-ALERT',
                            estado='FACTURA_ASOCIADA', total=500.0)
            db.session.add(fac)
            db.session.commit()
        data = client.get('/api/alertas/sin-netear', headers=auth_admin()).get_json()
        nums = [d['numero'] for d in data['documentos']]
        assert 'FAC-NET-ALERT' not in nums

    def test_alertas_factura_sin_netear_aparece(self, client, flask_app):
        import app as m
        from models import db, Documento
        with flask_app.app_context():
            fac = Documento(tipo='factura', numero='FAC-SINNET',
                            estado='PROCESADO', total=300.0)
            db.session.add(fac)
            db.session.commit()
        data = client.get('/api/alertas/sin-netear', headers=auth_admin()).get_json()
        nums = [d['numero'] for d in data['documentos']]
        assert 'FAC-SINNET' in nums

    def test_alertas_urgencia_critico_30_dias(self, client, flask_app):
        import app as m
        from models import db, Documento
        with flask_app.app_context():
            fac = Documento(
                tipo='factura', numero='FAC-CRITICO',
                estado='PROCESADO', total=100.0,
                fecha_subida=datetime.utcnow() - timedelta(days=35),
            )
            db.session.add(fac)
            db.session.commit()
        data = client.get('/api/alertas/sin-netear', headers=auth_admin()).get_json()
        assert data['criticos'] >= 1

    def test_alertas_urgencia_aviso_15_dias(self, client, flask_app):
        import app as m
        from models import db, Documento
        with flask_app.app_context():
            fac = Documento(
                tipo='factura', numero='FAC-AVISO',
                estado='PROCESADO', total=100.0,
                fecha_subida=datetime.utcnow() - timedelta(days=20),
            )
            db.session.add(fac)
            db.session.commit()
        data = client.get('/api/alertas/sin-netear', headers=auth_admin()).get_json()
        assert data['avisos'] >= 1

    def test_alertas_devuelve_max_10_documentos(self, client, flask_app):
        import app as m
        from models import db, Documento
        with flask_app.app_context():
            for i in range(15):
                db.session.add(Documento(
                    tipo='factura', numero=f'FAC-MAX-{i:03d}', estado='PROCESADO'
                ))
            db.session.commit()
        data = client.get('/api/alertas/sin-netear', headers=auth_admin()).get_json()
        assert len(data['documentos']) <= 10
        assert data['total'] == 15

    def test_alertas_con_token_basico(self, client):
        assert client.get('/api/alertas/sin-netear', headers=auth_basico()).status_code == 200


# ══════════════════════════════════════════════════════════════════════════
# GRUPO 11 — LOGS DE AUDITORÍA
# ══════════════════════════════════════════════════════════════════════════

class TestLogs:

    def test_listar_logs_sin_token_retorna_401(self, client):
        assert client.get('/api/logs').status_code == 401

    def test_listar_logs_con_basico_retorna_403(self, client):
        r = client.get('/api/logs', headers=auth_basico())
        assert r.status_code == 403

    def test_listar_logs_con_admin_retorna_200(self, client):
        r = client.get('/api/logs', headers=auth_admin())
        assert r.status_code == 200

    def test_listar_logs_estructura_respuesta(self, client):
        data = client.get('/api/logs', headers=auth_admin()).get_json()
        for campo in ('logs', 'total', 'pagina', 'por_pagina', 'paginas'):
            assert campo in data

    def test_logs_se_generan_al_operar(self, client):
        crear_proveedor(client, nombre='Log Prov SA', cif='LOG111111')
        data = client.get('/api/logs', headers=auth_admin()).get_json()
        assert data['total'] >= 1

    def test_filtro_logs_por_usuario(self, client):
        data = client.get('/api/logs?usuario=admin_test', headers=auth_admin()).get_json()
        for log in data['logs']:
            assert 'admin_test' in log['usuario']

    def test_filtro_logs_por_accion(self, client):
        crear_proveedor(client, nombre='Prov Filtro SA', cif='LOG222222')
        data = client.get('/api/logs?accion=CREAR_PROV', headers=auth_admin()).get_json()
        for log in data['logs']:
            assert log['accion'] == 'CREAR_PROV'

    def test_filtro_logs_por_resultado(self, client):
        data = client.get('/api/logs?resultado=ok', headers=auth_admin()).get_json()
        for log in data['logs']:
            assert log['resultado'] == 'ok'

    def test_logs_paginacion(self, client):
        data = client.get('/api/logs?por_pagina=1&pagina=1', headers=auth_admin()).get_json()
        assert data['por_pagina'] == 1

    def test_purgar_logs_sin_token_retorna_401(self, client):
        assert client.delete('/api/logs').status_code == 401

    def test_purgar_logs_con_basico_retorna_403(self, client):
        assert client.delete('/api/logs', headers=auth_basico()).status_code == 403

    def test_purgar_logs_con_admin_retorna_200(self, client):
        r = client.delete('/api/logs?dias=1', headers=auth_admin())
        assert r.status_code == 200
        assert 'eliminados' in r.get_json()

    def test_evento_externo_retorna_201(self, client):
        """POST /api/logs/evento desde localhost debe ser aceptado."""
        payload = {'usuario': 'sistema', 'accion': 'LOGIN', 'resultado': 'ok',
                   'detalle': 'Test evento externo'}
        r = client.post('/api/logs/evento', json=payload)
        assert r.status_code == 201

    def test_evento_externo_guarda_en_bd(self, client):
        payload = {'usuario': 'usuario_externo', 'accion': 'LOGIN', 'resultado': 'ok'}
        client.post('/api/logs/evento', json=payload)
        logs = client.get('/api/logs?usuario=usuario_externo', headers=auth_admin()).get_json()
        assert logs['total'] >= 1


# ══════════════════════════════════════════════════════════════════════════
# GRUPO 12 — REPORTES (solo verificar cabeceras, no contenido Excel)
# ══════════════════════════════════════════════════════════════════════════

class TestReportes:

    def test_reporte_sin_token_retorna_401(self, client):
        assert client.post('/api/reportes/generar', json={}).status_code == 401

    def test_reporte_contable_sin_token_retorna_401(self, client):
        assert client.post('/api/reportes/contable', json={}).status_code == 401

    def test_reporte_analitico_sin_token_retorna_401(self, client):
        assert client.post('/api/reportes/analitico', json={}).status_code == 401

    def test_reporte_contable_sin_facturas_retorna_404(self, client):
        r = client.post('/api/reportes/contable', json={}, headers=auth_admin())
        assert r.status_code == 404

    def test_reporte_analitico_sin_lineas_retorna_404(self, client):
        r = client.post('/api/reportes/analitico', json={}, headers=auth_admin())
        assert r.status_code == 404

    def test_reporte_general_con_docs_retorna_excel(self, client):
        crear_documento(client, tipo='factura', numero='FAC-RPT-001', total=100.0)
        with patch('app.generar_reporte_excel') as mock_gen:
            import tempfile
            tmp = tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False)
            tmp.write(b'PK fake xlsx')
            tmp.close()
            mock_gen.return_value = (tmp.name, None)
            r = client.post('/api/reportes/generar', json={}, headers=auth_admin())
        assert r.status_code == 200
        assert 'spreadsheet' in r.content_type
