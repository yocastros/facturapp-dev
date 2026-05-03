# Instalación en Linux

Compatible con Ubuntu 20.04+, Debian 11+, Linux Mint, Fedora 36+, CentOS/RHEL 8+.  
Requisitos: 4 GB RAM, 2 GB de espacio libre, conexión a Internet durante la instalación.

---

## Opción A — Instalador automático (recomendado)

```bash
bash instalar_linux.sh
```

El script detecta automáticamente la distribución y gestiona los 5 pasos con el gestor de paquetes correspondiente (`apt-get`, `dnf` o `yum`):

- `[1/5]` Instalar dependencias del sistema (Python, Tesseract, Poppler)
- `[2/5]` Instalar dependencias Python
- `[3/5]` Verificar instalación
- `[4/5]` Crear acceso directo en el escritorio
- `[5/5]` Resumen final

Al finalizar ejecuta:

```bash
python3 start.py
```

---

## Opción B — Instalación manual por distribución

### Ubuntu / Debian / Linux Mint

```bash
sudo apt-get update
sudo apt-get install -y \
    python3 python3-pip python3-tk \
    tesseract-ocr tesseract-ocr-spa \
    poppler-utils \
    libgl1-mesa-glx libglib2.0-0
```

### Fedora

```bash
sudo dnf install -y \
    python3 python3-pip python3-tkinter \
    tesseract tesseract-langpack-spa \
    poppler-utils \
    mesa-libGL glib2
```

### CentOS / RHEL

```bash
sudo yum install -y epel-release
sudo yum install -y \
    python3 python3-pip python3-tkinter \
    tesseract tesseract-langpack-spa \
    poppler-utils
```

### Dependencias Python (todas las distribuciones)

```bash
cd backend
pip3 install -r requirements.txt

cd ../sistema_usuarios
pip3 install -r requirements.txt

pip3 install pystray pillow uvicorn
```

> Si pip da error de entorno gestionado externamente (Ubuntu 23.04+):
> ```bash
> pip3 install -r requirements.txt --break-system-packages
> ```

### Arrancar el sistema

```bash
python3 start.py
```

El sistema abre automáticamente el navegador en `http://localhost:5000`.

---

## Arranque automático al iniciar sesión (opcional)

Para que el sistema arranque automáticamente con el usuario, crea un servicio de escritorio:

```bash
mkdir -p ~/.config/autostart
cat > ~/.config/autostart/facturas.desktop << DESKTOP
[Desktop Entry]
Type=Application
Name=Facturas y Albaranes
Exec=python3 /ruta/al/proyecto/start.py
Hidden=false
NoDisplay=false
X-GNOME-Autostart-enabled=true
DESKTOP
```

Sustituye `/ruta/al/proyecto/` por la ruta real del proyecto.

---

## Servidor sin interfaz gráfica (modo headless)

Si el servidor no tiene entorno de escritorio, arranca los dos servicios manualmente:

```bash
# Terminal 1 — Sistema de usuarios
cd sistema_usuarios
uvicorn main:app --host 0.0.0.0 --port 8000 &

# Terminal 2 — Backend de facturas
cd backend
python3 app.py
```

La interfaz web es accesible desde cualquier equipo de la red en `http://<IP-del-servidor>:5000`.

Para que los servicios sobrevivan al cierre del terminal, usa `screen` o `tmux`:

```bash
screen -S facturas
python3 start.py
# Ctrl+A, D para despegar
```

---

## Rutas de Tesseract en Linux

El sistema busca los datos de idioma en estas rutas, en orden:

1. `/usr/share/tesseract-ocr/5/tessdata`
2. `/usr/share/tesseract-ocr/4/tessdata`
3. `/usr/share/tessdata`
4. `/usr/local/share/tessdata`

Si Tesseract está instalado en una ruta no estándar:

```bash
export TESSERACT_CMD=/ruta/a/tesseract
export TESSDATA_PREFIX=/ruta/a/tessdata
```

---

## Resolución de problemas

**"tesseract: command not found"**  
```bash
# Ubuntu/Debian
sudo apt-get install tesseract-ocr tesseract-ocr-spa

# Fedora
sudo dnf install tesseract tesseract-langpack-spa
```

**"No module named 'cv2'"**  
```bash
pip3 install opencv-python --break-system-packages
```

**"ImportError: libGL.so.1: cannot open shared object file"**  
```bash
# Ubuntu/Debian
sudo apt-get install libgl1-mesa-glx

# Fedora
sudo dnf install mesa-libGL
```

**"pdf2image: Unable to get page count" o PDFs no se procesan**  
```bash
sudo apt-get install poppler-utils   # Ubuntu/Debian
sudo dnf install poppler-utils        # Fedora
```

Verifica con `which pdftoppm`.

**Puerto 5000 ya en uso**  
```bash
sudo lsof -ti:5000 | xargs kill -9
sudo lsof -ti:8000 | xargs kill -9
```

**Permisos en pip (Ubuntu 23.04+)**  
Usa siempre `--break-system-packages` o crea un entorno virtual:
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r backend/requirements.txt
```
