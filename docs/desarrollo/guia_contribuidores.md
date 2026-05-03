# Guía para Contribuidores y Desarrolladores

Todo lo necesario para entender, modificar y extender el sistema.

---

## Entorno de desarrollo

### Requisitos previos

- Python 3.8+
- Tesseract OCR + idioma español (ver `@docs/instalacion/`)
- Poppler (para procesado de PDFs)
- Editor recomendado: VS Code

### Configuración inicial

```bash
# 1. Clonar / descomprimir el proyecto en una carpeta local

# 2. Dependencias del backend de facturas
cd backend
pip install -r requirements.txt

# 3. Dependencias del sistema de usuarios
cd ../sistema_usuarios
pip install -r requirements.txt

# 4. Arrancar ambos servicios
cd ..
python start.py
```

El sistema quedará disponible en:
- Frontend + Backend facturas: `http://localhost:5000`
- Sistema de usuarios: `http://localhost:8000`
- Docs interactivos FastAPI: `http://localhost:8000/docs`

### Variables de entorno

La `SECRET_KEY` compartida entre los dos servicios se lee desde `config_loader.py`.
Por defecto usa un valor hardcodeado para desarrollo. En producción, crea un fichero
`config.env` en la raíz con:

```env
SECRET_KEY=tu_clave_secreta_larga_y_aleatoria
```

`config.env` está en `.gitignore` y nunca debe versionarse.

---

## Arquitectura del sistema

Dos microservicios Python independientes que comparten JWT:

```
┌─────────────────────────────────────────────────┐
│                   Navegador                      │
│              http://localhost:5000               │
└────────────────────┬────────────────────────────┘
                     │ HTTP / JWT
          ┌──────────┴──────────┐
          │                     │
   ┌──────▼──────┐       ┌──────▼──────┐
   │   backend/  │       │ sistema_    │
   │  Flask :5000│       │ usuarios/   │
   │  SQLite     │       │ FastAPI:8000│
   │  facturas.db│       │ usuarios.db │
   └─────────────┘       └─────────────┘
          │                     │
          └─────────────────────┘
            SECRET_KEY compartida
            (config_loader.py)
```

El flujo de autenticación es:
1. El usuario hace login en `:8000/token`
2. Recibe un JWT firmado con `SECRET_KEY`
3. Envía ese JWT en cada petición a `:5000/api/*`
4. Flask valida la firma con la misma `SECRET_KEY` sin consultar al servicio de usuarios

---

## Estructura de ficheros clave

```
/
├── CLAUDE.md                  ← Contexto del proyecto para Claude Code
├── config_loader.py           ← SECRET_KEY compartida
├── start.py                   ← Arranque multiplataforma
│
├── backend/
│   ├── app.py                 ← Todos los endpoints Flask + auth + logs
│   ├── models.py              ← Modelos SQLAlchemy (Documento, Proveedor, LogActividad)
│   ├── ocr_processor.py       ← Pipeline OCR completo
│   ├── report_generator.py    ← Generación de Excel con OpenPyXL
│   └── requirements.txt
│
├── frontend/
│   └── index.html             ← SPA completa (HTML + CSS + JS en un solo fichero)
│
├── sistema_usuarios/
│   ├── main.py                ← API FastAPI (auth, usuarios, roles, permisos)
│   ├── models.py              ← User, Role, UserPermission
│   ├── schemas.py             ← Schemas Pydantic
│   └── database.py            ← Configuración SQLAlchemy
│
└── sistema_facturas/
    └── tests/
        └── test_integracion.py ← Tests end-to-end
```

---

## Convenciones de código

### Python — Backend Flask (`backend/`)

**Docstrings:** Formato Google style en todas las funciones públicas.

```python
def extraer_cif(texto: str) -> str | None:
    """Extrae el CIF/NIF del texto OCR.

    Args:
        texto: Texto completo extraído por Tesseract.

    Returns:
        CIF en formato estándar (ej: 'B12345678') o None si no se encuentra.
    """
```

**Endpoints Flask:** Siempre con `@require_auth` y `registrar_log` en operaciones de escritura.

```python
@app.route('/api/mi_recurso', methods=['POST'])
@require_auth
def crear_mi_recurso():
    """Descripción breve del endpoint."""
    datos = request.get_json() or {}
    # ... lógica ...
    registrar_log(_get_usuario(), 'MI_ACCION', entidad='mi_recurso',
                  entidad_id=nuevo.id, detalle=str(nuevo))
    return jsonify(nuevo.to_dict()), 201
```

**Modelos SQLAlchemy:** Siempre con `to_dict()` y opcionalmente `to_dict_simple()` para listados.

```python
def to_dict(self):
    return {
        'id': self.id,
        'campo': self.campo,
        # Nunca incluir texto_ocr — puede ser muy largo
    }
```

**Base de datos:** Siempre ORM, nunca SQL raw. Las migraciones se hacen con `ALTER TABLE` manual en el bloque de arranque de `app.py`.

**Nombres:** Variables y funciones en `snake_case`, constantes en `UPPER_SNAKE_CASE`, clases en `PascalCase`. Nombres en español para reflejar el dominio de negocio.

### Python — Sistema de usuarios (`sistema_usuarios/`)

Sigue las convenciones de FastAPI + Pydantic:
- Schemas en `schemas.py` para validación de entrada/salida
- Modelos SQLAlchemy en `models.py`
- Lógica de endpoints en `main.py`
- Contraseñas siempre cifradas con bcrypt, nunca en texto plano

### JavaScript — Frontend (`frontend/index.html`)

Todo el código vive en un único fichero. Convenciones:

- `authHeaders(extra?)` para inyectar JWT en cualquier `fetch`
- `toast(mensaje, tipo)` para notificaciones (`'success'`, `'error'`, `'warning'`)
- IDs de páginas con prefijo `page-` (ej: `page-dashboard`, `page-neteo`)
- IDs de KPIs con prefijo `kpi-`
- IDs de badges con prefijo `badge-`
- Funciones agrupadas por sección con comentarios separadores `/* ── SECCIÓN ── */`

---

## Cómo añadir un nuevo endpoint

1. **Añade la función en `backend/app.py`** siguiendo la plantilla:

```python
@app.route('/api/mi_endpoint', methods=['GET'])
@require_auth
def mi_endpoint():
    """Descripción del endpoint."""
    # lógica
    return jsonify({...})
```

2. **Actualiza `@docs/tecnica/api_referencia.md`** con el nuevo endpoint:
   método, URL, parámetros, cuerpo de petición, respuesta y errores.

3. **Si crea un nuevo recurso, actualiza también `CLAUDE.md`** en la sección API REST.

4. **Añade un test** en `sistema_facturas/tests/test_integracion.py`.

---

## Cómo añadir un nuevo campo a un modelo

1. **Añade la columna en `backend/models.py`**:

```python
mi_campo_nuevo = db.Column(db.String(100), nullable=True)
```

2. **Añade la migración en `backend/app.py`** dentro del bloque `with app.app_context()`:

```python
if 'mi_campo_nuevo' not in _cols_doc:
    _conn.execute(text(
        'ALTER TABLE documentos ADD COLUMN mi_campo_nuevo VARCHAR(100)'))
```

3. **Añade el campo a `to_dict()`** del modelo.

4. **Actualiza `@docs/tecnica/modelos_bd.md`** con la nueva columna.

---

## Cómo añadir un nuevo tipo de reporte Excel

1. **Crea la función generadora en `backend/report_generator.py`** siguiendo el patrón de `generar_reporte_contable()`.

2. **Añade el endpoint en `backend/app.py`**:

```python
@app.route('/api/reportes/mi_reporte', methods=['POST'])
@require_auth
def generar_mi_reporte():
    ...
    registrar_log(_get_usuario(), LOG_REPORTE, detalle='Mi reporte')
    return send_file(ruta, as_attachment=True, download_name=nombre)
```

3. **Añade el botón en `frontend/index.html`** en la sección de Reportes.

4. **Actualiza `@docs/tecnica/api_referencia.md`**.

---

## Tests

### Ejecutar los tests de integración

Los tests son de integración: requieren que **ambos servicios estén corriendo** antes de ejecutarlos.

```bash
# 1. Arrancar el sistema
python start.py

# 2. En otro terminal, ejecutar los tests
python -m pytest sistema_facturas/tests/test_integracion.py -v
```

### Grupos de tests

| Clase | Qué prueba |
|-------|-----------|
| `TestUsuarios` | Endpoints del sistema de usuarios (:8000): login, token, permisos |
| `TestFacturas` | Endpoints del backend (:5000): auth, documentos, neteo |
| `TestEndToEnd` | Flujo completo: login → perfil → uso del sistema de facturas con el mismo token |

### Credenciales de test

Los tests usan las credenciales por defecto: `admin` / `admin123`.
Si las has cambiado, actualiza `get_token()` en `test_integracion.py`.

### Añadir un test nuevo

```python
class TestMiModulo:

    def test_mi_caso(self):
        token = get_token()
        r = requests.get(f"{FACTURAS}/api/mi_endpoint", headers=auth(token))
        assert r.status_code == 200
        assert "mi_campo" in r.json()
```

---

## Generar el instalador Windows

Para generar el `.exe` autocontenido que incluye el programa completo:

```bash
# Requiere PyInstaller instalado
pip install pyinstaller

python build_windows.py
```

El ejecutable se genera en `dist/`. El proceso:
1. Empaqueta `backend/`, `frontend/`, `sistema_usuarios/` y scripts de arranque en un ZIP
2. Embebe el ZIP en base64 dentro del launcher Python
3. PyInstaller compila el launcher en un `.exe` standalone

---

## Flujo de trabajo con documentación

Al hacer cualquier cambio en el código, actualiza también la documentación afectada:

| Si cambias... | Actualiza... |
|---|---|
| Endpoint en `backend/app.py` | `@docs/tecnica/api_referencia.md` |
| Modelo en `backend/models.py` | `@docs/tecnica/modelos_bd.md` |
| `backend/ocr_processor.py` | `@docs/tecnica/ocr_pipeline.md` |
| Flujo de usuario en `frontend/index.html` | `@docs/usuario/manual_usuario.md` |
| Scripts de instalación | `@docs/instalacion/` (el .md del SO correspondiente) |

Con Claude Code puedes pedir directamente: *"actualiza la documentación afectada por este cambio"* y lo hará automáticamente consultando los ficheros `@docs/` correspondientes.

---

## Depuración

### Logs del backend

El backend escribe logs en `backend_error.log` en la raíz. También los muestra en la consola con nivel `INFO`.

Para activar modo debug con más detalle:

```python
# En backend/app.py, última línea:
app.run(debug=True, host='0.0.0.0', port=5000)
```

### Inspeccionar el OCR

Cada documento procesado escribe en el log los primeros 1200 caracteres del texto extraído:

```
=== OCR DEBUG (primeros 1200 chars) ===
[texto extraído por Tesseract]
=== FIN OCR DEBUG ===
```

Esto permite diagnosticar por qué un campo no se extrae correctamente.

### Base de datos

Puedes inspeccionar la base de datos SQLite directamente con cualquier cliente:

```bash
# Con sqlite3 de línea de comandos
sqlite3 sistema_facturas.db
sqlite> .tables
sqlite> SELECT * FROM documentos LIMIT 5;
sqlite> .quit
```

O con extensiones de VS Code como **SQLite Viewer**.

### Verificar que el JWT funciona

```bash
curl -X GET http://localhost:5000/api/estadisticas \
  -H "Authorization: Bearer <tu_token>"

# Debe devolver 200 con los KPIs
# Si devuelve 401, el token es inválido o ha expirado
```

---

## Checklist antes de hacer cambios en producción

- [ ] Los tests de integración pasan: `pytest sistema_facturas/tests/test_integracion.py -v`
- [ ] El endpoint `/api/health` devuelve `{"status": "ok"}`
- [ ] La documentación afectada está actualizada en `docs/`
- [ ] `CLAUDE.md` refleja el estado actual si se añadieron funcionalidades
- [ ] `config.env` no está en el commit (comprueba con `git status`)
- [ ] Las bases de datos (`*.db`) no están en el commit
