# Sistema de Gestión de Facturas y Albaranes

Sistema web de gestión documental con OCR automático, neteo de facturas/albaranes,
gestión de proveedores y reportes Excel. Dos microservicios Python en producción.

---

## Arquitectura

Dos servicios independientes que comparten JWT:

| Servicio | Tecnología | Puerto | Descripción |
|---|---|---|---|
| `backend/` | Python 3.8+ · Flask · SQLAlchemy · SQLite | 5000 | API principal de documentos |
| `sistema_usuarios/` | Python 3.8+ · FastAPI · SQLAlchemy · SQLite | 8000 | Autenticación y roles |
| `frontend/` | HTML5 · CSS3 · JS vanilla (sin dependencias) | — | Servido por Flask en `/` |

**Flujo de auth:** El frontend hace login en `:8000/token` → recibe JWT → lo envía en `Authorization: Bearer <token>` a `:5000/api/*`. Flask valida el JWT con la misma `SECRET_KEY`.

---

## Comandos esenciales

```bash
# Arrancar todo (recomendado)
python start.py

# Arrancar manualmente
cd sistema_usuarios && uvicorn main:app --port 8000 &
cd backend && python app.py     # puerto 5000

# Tests de integración
python -m pytest sistema_facturas/tests/test_integracion.py -v

# Instalar dependencias
cd backend && pip install -r requirements.txt
cd sistema_usuarios && pip install -r requirements.txt

# Instaladores de sistema (primera vez)
bash instalar_linux.sh    # Ubuntu/Debian/Fedora
bash instalar_mac.sh      # macOS Intel + Apple Silicon
instalar_windows.bat      # Windows

# Inicializar BD de usuarios (solo primera vez, crea admin por defecto)
cd sistema_usuarios && python init_db.py
```

---

## Estructura del proyecto

```
/                                    ← raíz del repositorio
├── CLAUDE.md                        ← este fichero
├── README.md
├── start.py                         ← arranque multiplataforma (Windows/macOS/Linux)
├── config_loader.py                 ← SECRET_KEY compartida entre los dos servicios
├── config.env                       ← variables de entorno (gitignoreado)
├── instalar_linux.sh
├── instalar_mac.sh
├── instalar_windows.bat
├── build_windows.py                 ← empaquetador .exe para Windows
├── deploy_local.py
├── crear_acceso_directo.py
├── docs/                            ← documentación del proyecto
│   ├── tecnica/
│   ├── usuario/
│   ├── instalacion/
│   └── desarrollo/
├── backend/
│   ├── app.py                       ← API REST Flask (todos los endpoints)
│   ├── models.py                    ← Documento, Proveedor, LogActividad (SQLAlchemy)
│   ├── ocr_processor.py             ← Tesseract + extracción de campos con regex
│   ├── report_generator.py          ← Generador Excel con OpenPyXL
│   └── requirements.txt
├── frontend/
│   └── index.html                   ← SPA completa (JS inline, sin dependencias externas)
├── sistema_usuarios/
│   ├── main.py                      ← API FastAPI de auth, usuarios y permisos
│   ├── models.py                    ← User, Role, UserPermission
│   ├── schemas.py                   ← Pydantic schemas
│   ├── database.py
│   ├── init_db.py                   ← Inicializa BD y crea usuario admin por defecto (primera vez)
│   ├── requirements.txt
│   └── static/                      ← UI de gestión de usuarios (servida por FastAPI)
│       ├── login.html
│       ├── users_list.html
│       ├── create_user.html
│       ├── edit_user.html
│       ├── profile.html
│       └── sistema_usuarios_shared.css
├── sistema_facturas/
│   └── tests/test_integracion.py
├── uploads/                         ← PDFs/imágenes subidos (gitignoreado)
├── reports/                         ← Excels generados (gitignoreado)
└── dist/                            ← build Windows (gitignoreado)
```

---

## Modelos de base de datos

**`backend` (SQLite: `sistema_facturas.db`)**
- `Documento`: id, tipo (factura/albaran), numero, fecha, proveedor, cif, base_imponible, iva_importe, porcentaje_iva, total, estado (PENDIENTE/PROCESADO/ERROR/FACTURA_ASOCIADA), factura_id (FK self), proveedor_id (FK), archivo, archivo_original (UUID), texto_ocr, proveedor_normalizado
- `LineaDocumento`: id, documento_id (FK), descripcion, cantidad, precio_unitario, total_linea
- `Proveedor`: id, nombre, cif, email, telefono, direccion, notas, activo
- `LogActividad`: id, usuario, accion, entidad, entidad_id, detalle, resultado, timestamp, ip

**`sistema_usuarios` (SQLite: `usuarios.db`)**
- `User`: id, username, email, hashed_password, full_name, role_id, is_active, created_at, last_login
- `Role`: id, name (admin/supervisor/basico), description
- `UserPermission`: id, user_id, module (dashboard/escanear/documentos/neteo/reportes), can_access

---

## API REST (`:5000`)

Todos los endpoints requieren `Authorization: Bearer <jwt>` salvo `/api/health`.

**Documentos**
- `POST /api/escanear` — Subir PDF/PNG/JPG/JPEG/TIFF/BMP, ejecuta OCR, guarda en BD
- `GET /api/documentos` — Listar con filtros (tipo, estado, proveedor, fechas, q)
- `GET /api/documentos/:id` — Detalle
- `PUT /api/documentos/:id` — Editar campos extraídos
- `DELETE /api/documentos/:id` — Eliminar

**Neteo** (asociar facturas ↔ albaranes)
- `POST /api/neteo/asociar` — `{factura_id, albaran_ids[]}`
- `POST /api/neteo/desasociar/:id` — Desasociar albarán
- `GET /api/neteo/sin-asociar` — Facturas sin albarán + albaranes sin factura

**Proveedores**
- `GET/POST /api/proveedores` — Listar (con paginación) / Crear
- `GET/PUT/DELETE /api/proveedores/:id` — Detalle / Editar / Eliminar
- `POST /api/proveedores/desde-documento/:doc_id` — Crear proveedor desde doc existente

**Reportes**
- `POST /api/reportes/generar` — Excel estándar `{fecha_desde?, fecha_hasta?}`
- `POST /api/reportes/contable` — Informe contable `{fecha_desde?, fecha_hasta?, proveedor_id?}`
- `POST /api/reportes/analitico` — CPP / análisis de compras

**Alertas y logs** (solo admin para logs)
- `GET /api/alertas/sin-netear` — Facturas sin albarán por urgencia (normal/aviso/critico)
- `GET /api/logs` — Auditoría con filtros (usuario, accion, resultado, fechas)
- `DELETE /api/logs` — Purgar logs anteriores a fecha
- `POST /api/logs/evento` — Registro interno de eventos desde `sistema_usuarios` (fire-and-forget)

**Estadísticas**
- `GET /api/estadisticas` — KPIs: totales, importes, estados

**Ficheros**
- `GET /api/documentos/:id/archivo` — Sirve el fichero original subido (PDF/imagen)

---

## API de usuarios (`:8000`)

Gestión de usuarios y permisos. Los endpoints `/api/*` requieren `Authorization: Bearer <jwt>` y rol admin salvo indicación.

**Auth**
- `POST /token` — Login; devuelve JWT (`{username, password}` form-data)
- `GET /me` — Usuario autenticado actual
- `GET /me/permissions` — Permisos del usuario actual por módulo
- `GET /health` — Health check público
- `GET /health/full` — Health check autenticado

**Usuarios** (solo admin)
- `GET /api/users` — Listar todos los usuarios
- `GET /api/users/:id` — Detalle de usuario
- `POST /admin/users` — Crear usuario `{username, email, password, full_name, role_id}`
- `PUT /users/:id` — Editar usuario (admin o el propio usuario)
- `DELETE /api/users/:id` — Eliminar usuario

**Permisos** (solo admin)
- `GET /api/users/:id/permissions` — Permisos de un usuario por módulo
- `PUT /api/users/:id/permissions` — Actualizar permisos `[{module, can_access}]`

**Páginas HTML** (UI de gestión servida por FastAPI/static)
- `GET /login` — Formulario de login
- `GET /users` — Lista de usuarios
- `GET /create-user` — Formulario de creación
- `GET /edit-user` — Formulario de edición
- `GET /profile` — Perfil del usuario actual

---

## Convenciones de código

**Python (backend Flask)**
- Docstrings en todas las funciones públicas: formato Google style
- Nombres de endpoints en español (consistente con el proyecto)
- Usar `registrar_log(usuario, accion, entidad?, entidad_id?, detalle?, resultado?)` en cada operación de escritura
- Decorator `@require_auth` en todos los endpoints protegidos
- `_es_admin()` para verificar rol antes de operaciones privilegiadas
- SQLAlchemy ORM siempre, no SQL raw

**JavaScript (frontend vanilla)**
- Todo en `frontend/index.html` (SPA sin bundler, sin dependencias externas)
- Función `authHeaders(extra?)` para inyectar JWT en fetch
- `toast(mensaje, tipo)` para notificaciones (success/error/warning)
- Prefijo `page-` para IDs de páginas, `kpi-` para KPIs del dashboard

---

## Flujo de trabajo con documentación

Cuando modifiques código, actualiza también la documentación afectada:

| Si cambias... | Actualiza... |
|---|---|
| Endpoint en `backend/app.py` | `@docs/tecnica/api_referencia.md` |
| Modelo en `backend/models.py` | `@docs/tecnica/modelos_bd.md` |
| `backend/ocr_processor.py` | `@docs/tecnica/ocr_pipeline.md` |
| Flujo de usuario en frontend | `@docs/usuario/manual_usuario.md` |
| Scripts de instalación | `@docs/instalacion/` (el .md del SO correspondiente) |

Para generar los entregables Word/PDF para el cliente:
```bash
python docs/scripts/generar_entregables.py
```

---

## Estado actual del proyecto (v1.2)

**Implementado y funcional:**
- OCR con Tesseract (PDF, PNG, JPG, TIFF) + extracción de campos con regex
- Neteo automático (por número de albarán en factura) y manual
- CRUD completo de documentos y proveedores
- Sistema de autenticación JWT con roles (admin/supervisor/básico) y permisos por módulo
- Reportes Excel: estándar, contable (por proveedor y fechas), análisis CPP
- Panel de alertas: facturas sin netear con badge + urgencia por antigüedad
- Log de auditoría completo por usuario

**Pendiente:**
- [ ] OCR fallback con Claude API cuando Tesseract no extrae líneas de detalle

---

## Dependencias críticas del sistema (no Python)

- **Tesseract OCR** + paquete de idioma español (`tesseract-ocr-spa`) — requerido para OCR real
- **Poppler** (`poppler-utils`) — requerido para convertir PDF a imagen antes del OCR
- Sin Tesseract: el sistema arranca en **modo simulación** (datos OCR de ejemplo)

---

## Referencias

- Documentación técnica completa: `@docs/tecnica/`
- Manual de usuario: `@docs/usuario/manual_usuario.md`
- Guía de instalación: `@docs/instalacion/`
- Guía para contribuidores: `@docs/desarrollo/guia_contribuidores.md`
