#!/usr/bin/env python3
"""
Despliega los cambios del proyecto a C:/FacturasAlbaranes/ para pruebas locales.
No requiere PyInstaller ni permisos de administrador.
Uso: python deploy_local.py
"""
import shutil
import sys
from pathlib import Path

SRC = Path(__file__).resolve().parent
DST = Path("C:/FacturasAlbaranes")

CARPETAS = ["backend", "frontend", "sistema_usuarios"]
ARCHIVOS = ["start.py", "crear_acceso_directo.py", "config_loader.py", "config.env"]

EXCLUIR_DIRS = {"__pycache__", "uploads", "reports", "venv", ".git"}
EXCLUIR_EXT  = {".pyc", ".db", ".sqlite3"}


def copiar():
    if not DST.exists():
        print(f"ERROR: {DST} no existe.")
        print("       Ejecuta el instalador original al menos una vez antes de usar este script.")
        sys.exit(1)

    copiados = 0
    errores  = 0

    for carpeta in CARPETAS:
        src_dir = SRC / carpeta
        dst_dir = DST / carpeta
        if not src_dir.exists():
            print(f"  [AVISO] carpeta no encontrada: {src_dir}")
            continue
        for src_file in src_dir.rglob("*"):
            if not src_file.is_file():
                continue
            if any(p in EXCLUIR_DIRS for p in src_file.parts):
                continue
            if src_file.suffix in EXCLUIR_EXT:
                continue
            dst_file = dst_dir / src_file.relative_to(src_dir)
            try:
                dst_file.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(src_file, dst_file)
                print(f"  -> {dst_file.relative_to(DST)}")
                copiados += 1
            except Exception as e:
                print(f"  [ERROR] {src_file.name}: {e}")
                errores += 1

    for archivo in ARCHIVOS:
        src_file = SRC / archivo
        if not src_file.exists():
            continue
        try:
            shutil.copy2(src_file, DST / archivo)
            print(f"  -> {archivo}")
            copiados += 1
        except Exception as e:
            print(f"  [ERROR] {archivo}: {e}")
            errores += 1

    print()
    print("=" * 45)
    print(f"  {copiados} archivo(s) copiado(s)  |  {errores} error(es)")
    print(f"  Destino: {DST}")
    print("=" * 45)
    if errores == 0:
        print("  Reinicia el sistema para aplicar los cambios.")
    else:
        print("  Algunos archivos no se pudieron copiar.")
        print("  Cierra el sistema antes de ejecutar este script.")


if __name__ == "__main__":
    print()
    print("=" * 45)
    print("  Deploy local - Facturas y Albaranes")
    print("=" * 45)
    copiar()
