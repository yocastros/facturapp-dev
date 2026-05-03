# Instalación en Windows

Requisitos mínimos: Windows 10 64-bit, 4 GB RAM, 2 GB de espacio libre, conexión a Internet durante la instalación.

---

## Opción A — Instalador automático (recomendado)

El instalador `instalar_windows.bat` descarga e instala todo automáticamente:
Python 3.11, Tesseract OCR con idioma español, Poppler, y todas las dependencias Python.

### Pasos

1. Haz clic derecho sobre `instalar_windows.bat` → **Ejecutar como administrador**
2. Acepta la ventana de control de cuentas (UAC) si aparece
3. El instalador realiza 6 pasos y muestra el progreso en pantalla:
   - `[1/6]` Verificar / instalar Python 3.11
   - `[2/6]` Verificar / instalar Tesseract OCR + idioma español
   - `[3/6]` Verificar / instalar Poppler
   - `[4/6]` Configurar variables de entorno (`TESSDATA_PREFIX`)
   - `[5/6]` Instalar dependencias Python (backend + sistema de usuarios)
   - `[6/6]` Crear acceso directo en el escritorio
4. Al finalizar verás el mensaje **"Instalacion completada correctamente!"**
5. Cierra la ventana y haz doble clic en el acceso directo del escritorio para arrancar

> **Si el instalador falla** en algún paso, consulta la sección de resolución de problemas al final de este documento.

---

## Opción B — Instalación manual

Si prefieres instalar cada componente por tu cuenta o el instalador automático no funciona en tu entorno.

### Paso 1 — Python 3.11

1. Descarga Python 3.11 desde [python.org](https://www.python.org/ftp/python/3.11.9/python-3.11.9-amd64.exe)
2. Ejecuta el instalador
3. **Importante:** Marca la casilla **"Add Python to PATH"** antes de instalar
4. Selecciona "Install Now"
5. Verifica la instalación abriendo un terminal (`Win + R` → `cmd`):

```cmd
python --version
```

Debe mostrar `Python 3.11.x`.

### Paso 2 — Tesseract OCR

1. Descarga el instalador desde [UB Mannheim](https://github.com/UB-Mannheim/tesseract/releases/download/v5.5.0.20241111/tesseract-ocr-w64-setup-5.5.0.20241111.exe)
2. Ejecuta el instalador (requiere permisos de administrador)
3. Durante la instalación, en la sección de componentes adicionales, activa **"Spanish"** (idioma español)
4. Instala en la ruta por defecto: `C:\Program Files\Tesseract-OCR\`
5. Si no activaste el español durante la instalación, descárgalo manualmente:

```cmd
powershell -Command "Invoke-WebRequest -Uri 'https://github.com/tesseract-ocr/tessdata/raw/main/spa.traineddata' -OutFile 'C:\Program Files\Tesseract-OCR\tessdata\spa.traineddata'"
```

6. Configura la variable de entorno:

```cmd
setx /M TESSDATA_PREFIX "C:\Program Files\Tesseract-OCR\tessdata"
```

### Paso 3 — Poppler

1. Descarga Poppler desde [GitHub](https://github.com/oschwartz10612/poppler-windows/releases/download/v24.08.0-0/Release-24.08.0-0.zip)
2. Extrae el ZIP
3. Copia la carpeta extraída a `C:\poppler\`
4. Verifica que exista el fichero `C:\poppler\Library\bin\pdftoppm.exe`

### Paso 4 — Dependencias Python

Abre un terminal **como administrador** en la raíz del proyecto:

```cmd
cd backend
python -m pip install -r requirements.txt

cd ..\sistema_usuarios
python -m pip install -r requirements.txt

python -m pip install pystray pillow pywin32 uvicorn
```

### Paso 5 — Arrancar el sistema

```cmd
python start.py
```

El sistema abre automáticamente el navegador en `http://localhost:5000`. También aparece un icono en la bandeja del sistema (junto al reloj) desde el que puedes detenerlo.

---

## Resolución de problemas

**"Python no se encontró"**  
Abre un terminal nuevo tras la instalación. Si sigue fallando, ve a *Panel de Control → Sistema → Variables de entorno* y añade `C:\Program Files\Python311\` y `C:\Program Files\Python311\Scripts\` a la variable `Path`.

**"Tesseract no encontrado" o imágenes no se procesan**  
Verifica que existe `C:\Program Files\Tesseract-OCR\tesseract.exe`. Comprueba también que `TESSDATA_PREFIX` está definida en las variables de entorno del sistema (no solo del usuario).

**"pdftoppm no encontrado" o PDFs no se procesan**  
Verifica que existe `C:\poppler\Library\bin\pdftoppm.exe`. Si lo instalaste en otra ruta, actualiza la variable `_get_poppler_path()` en `backend/ocr_processor.py`.

**El sistema arranca pero el navegador no abre**  
Ve manualmente a `http://localhost:5000` en el navegador.

**Puerto 5000 o 8000 ya en uso**  
El sistema intenta liberar el puerto automáticamente en Windows. Si persiste, abre el Administrador de Tareas, busca procesos Python y ciérralos.

**Error de permisos en pip**  
Ejecuta el terminal como administrador o añade `--user` al final del comando pip.
