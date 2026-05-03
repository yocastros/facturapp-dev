# Instalación en macOS

Compatible con macOS 11 Big Sur o superior, Intel y Apple Silicon (M1/M2/M3).  
Requisitos: 4 GB RAM, 2 GB de espacio libre, conexión a Internet durante la instalación.

---

## Opción A — Instalador automático (recomendado)

```bash
bash instalar_mac.sh
```

El script detecta automáticamente si el Mac es Intel o Apple Silicon y realiza 5 pasos:

- `[1/5]` Verificar / instalar Homebrew
- `[2/5]` Instalar Tesseract + Poppler vía Homebrew
- `[3/5]` Instalar dependencias Python
- `[4/5]` Verificar instalación
- `[5/5]` Crear acceso directo en el escritorio (`FacturasAlbaranes.app`)

Al finalizar, haz doble clic en **Facturas y Albaranes** en el escritorio para arrancar.

> Si macOS muestra el aviso *"No se puede abrir porque es de un desarrollador no identificado"*, ve a **Preferencias del Sistema → Privacidad y Seguridad** y haz clic en **"Abrir de todas formas"**.

---

## Opción B — Instalación manual

### Paso 1 — Homebrew

Si no tienes Homebrew instalado:

```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

En Apple Silicon (M1/M2/M3), añade Homebrew al PATH si el instalador no lo hace automáticamente:

```bash
echo 'eval "$(/opt/homebrew/bin/brew shellenv)"' >> ~/.zprofile
eval "$(/opt/homebrew/bin/brew shellenv)"
```

### Paso 2 — Tesseract y Poppler

```bash
brew install tesseract tesseract-lang poppler
```

Verifica:

```bash
tesseract --version
pdftoppm -v
```

### Paso 3 — Python y dependencias

macOS incluye Python pero se recomienda la versión de Homebrew:

```bash
brew install python3
```

Instala las dependencias:

```bash
cd backend
pip3 install -r requirements.txt

cd ../sistema_usuarios
pip3 install -r requirements.txt

pip3 install pystray pillow uvicorn
```

### Paso 4 — Arrancar el sistema

```bash
python3 start.py
```

El sistema abre automáticamente el navegador en `http://localhost:5000` y crea un icono en la barra de menú superior desde el que puedes detenerlo.

---

## Rutas de Tesseract según arquitectura

El sistema detecta automáticamente la ruta de Tesseract:

| Arquitectura | Ruta del ejecutable |
|---|---|
| Intel | `/usr/local/bin/tesseract` |
| Apple Silicon (M1/M2/M3) | `/opt/homebrew/bin/tesseract` |

Si instalaste Tesseract en una ruta diferente, define la variable de entorno:

```bash
export TESSERACT_CMD=/ruta/a/tesseract
```

O añádela permanentemente a `~/.zprofile`.

---

## Resolución de problemas

**"tesseract: command not found"**  
Cierra y vuelve a abrir el terminal. En Apple Silicon, asegúrate de que `/opt/homebrew/bin` está en tu `PATH`.

**"No module named 'cv2'"**  
```bash
pip3 install opencv-python
```

**"pdf2image: Unable to get page count"**  
Poppler no está en el PATH. Verifica con `which pdftoppm`. Si no aparece, reinstala con `brew install poppler`.

**El sistema arranca pero la interfaz no carga**  
Comprueba que el backend está activo en `http://localhost:5000/api/health`. Si devuelve `{"status": "ok"}`, el problema es el navegador. Prueba con otro (Chrome, Firefox, Safari).

**Error SSL en pip**  
```bash
pip3 install --trusted-host pypi.org --trusted-host files.pythonhosted.org -r requirements.txt
```
