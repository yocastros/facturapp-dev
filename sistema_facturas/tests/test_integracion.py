"""
Tests de integración: Sistema de Usuarios (:8000) ↔ Sistema de Facturas (:5000)
Ejecutar con: pytest tests/test_integracion.py -v
Requisito: ambos servidores deben estar corriendo antes de ejecutar.
"""
import pytest
import requests

USUARIOS = "http://localhost:8000"
FACTURAS  = "http://localhost:5000"


def get_token(username="admin", password="admin123"):
    r = requests.post(f"{USUARIOS}/token",
                      data={"username": username, "password": password})
    assert r.status_code == 200, f"Login fallido: {r.text}"
    return r.json()["access_token"]


def auth(token):
    return {"Authorization": f"Bearer {token}"}


# ──────────────────────────────────────────────
# GRUPO 1 — Sistema de usuarios (:8000)
# ──────────────────────────────────────────────

class TestUsuarios:

    def test_health_publico(self):
        r = requests.get(f"{USUARIOS}/health")
        assert r.status_code == 200

    def test_login_correcto(self):
        token = get_token()
        assert token and len(token) > 10

    def test_login_incorrecto(self):
        r = requests.post(f"{USUARIOS}/token",
                          data={"username": "admin", "password": "INCORRECTA"})
        assert r.status_code == 401

    def test_me_con_token(self):
        r = requests.get(f"{USUARIOS}/me", headers=auth(get_token()))
        assert r.status_code == 200
        data = r.json()
        assert data["username"] == "admin"
        assert data["role"] == "admin"

    def test_me_sin_token(self):
        r = requests.get(f"{USUARIOS}/me")
        assert r.status_code == 401

    def test_health_full_con_token(self):
        r = requests.get(f"{USUARIOS}/health/full", headers=auth(get_token()))
        assert r.status_code == 200
        data = r.json()
        assert data["status"] == "ok"
        assert data["user"] == "admin"
        assert data["role"] == "admin"

    def test_health_full_sin_token(self):
        r = requests.get(f"{USUARIOS}/health/full")
        assert r.status_code == 401

    def test_permisos_admin(self):
        r = requests.get(f"{USUARIOS}/me/permissions", headers=auth(get_token()))
        assert r.status_code == 200
        perms = r.json()
        assert perms.get("dashboard") is True


# ──────────────────────────────────────────────
# GRUPO 2 — Sistema de facturas (:5000)
# ──────────────────────────────────────────────

class TestFacturas:

    def test_estadisticas_sin_token(self):
        r = requests.get(f"{FACTURAS}/api/estadisticas")
        assert r.status_code == 401

    def test_estadisticas_con_token(self):
        r = requests.get(f"{FACTURAS}/api/estadisticas", headers=auth(get_token()))
        assert r.status_code == 200
        data = r.json()
        assert "total_documentos" in data

    def test_documentos_sin_token(self):
        r = requests.get(f"{FACTURAS}/api/documentos")
        assert r.status_code == 401

    def test_documentos_con_token(self):
        r = requests.get(f"{FACTURAS}/api/documentos", headers=auth(get_token()))
        assert r.status_code == 200
        data = r.json()
        assert "documentos" in data

    def test_token_falso_rechazado(self):
        r = requests.get(f"{FACTURAS}/api/documentos",
                         headers={"Authorization": "Bearer token_inventado_xyz"})
        assert r.status_code == 401

    def test_health_publico(self):
        r = requests.get(f"{FACTURAS}/api/health")
        assert r.status_code == 200

    def test_neteo_sin_token(self):
        r = requests.get(f"{FACTURAS}/api/neteo/sin-asociar")
        assert r.status_code == 401

    def test_neteo_con_token(self):
        r = requests.get(f"{FACTURAS}/api/neteo/sin-asociar", headers=auth(get_token()))
        assert r.status_code == 200


# ──────────────────────────────────────────────
# GRUPO 3 — Flujo end-to-end
# ──────────────────────────────────────────────

class TestEndToEnd:

    def test_token_valido_en_ambos_sistemas(self):
        """Un token emitido por :8000 debe ser aceptado por :5000."""
        token = get_token()
        r_usuarios = requests.get(f"{USUARIOS}/me", headers=auth(token))
        r_facturas  = requests.get(f"{FACTURAS}/api/estadisticas", headers=auth(token))
        assert r_usuarios.status_code == 200
        assert r_facturas.status_code == 200

    def test_token_expirado_rechazado_en_facturas(self):
        """Token completamente inventado debe dar 401 en facturas."""
        r = requests.get(f"{FACTURAS}/api/estadisticas",
                         headers={"Authorization": "Bearer eyJhbGciOiJIUzI1NiJ9.falso.falso"})
        assert r.status_code == 401

    def test_flujo_login_y_uso(self):
        """Simula el flujo completo: login → obtener perfil → consultar facturas."""
        # 1. Login
        token = get_token("admin", "admin123")
        assert token

        # 2. Obtener perfil
        perfil = requests.get(f"{USUARIOS}/me", headers=auth(token)).json()
        assert perfil["role"] == "admin"

        # 3. Usar sistema de facturas con el mismo token
        stats = requests.get(f"{FACTURAS}/api/estadisticas", headers=auth(token)).json()
        assert "total_documentos" in stats
