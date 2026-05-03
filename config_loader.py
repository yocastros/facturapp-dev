import secrets
from pathlib import Path

_CONFIG_FILE = Path(__file__).resolve().parent / "config.env"


def get_secret_key() -> str:
    """Lee la SECRET_KEY de config.env; la genera y persiste si no existe.

    Returns:
        Clave secreta de 64 caracteres hex compartida entre servicios.
    """
    key = _leer_clave()
    if not key or key == "AUTOGENERAR":
        key = secrets.token_hex(32)
        _escribir_clave(key)
    return key


def _leer_clave() -> str:
    """Devuelve el valor de SECRET_KEY en config.env, o cadena vacía si no existe."""
    if not _CONFIG_FILE.exists():
        return ""
    for line in _CONFIG_FILE.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line.startswith("SECRET_KEY="):
            return line.split("=", 1)[1].strip()
    return ""


def _escribir_clave(key: str) -> None:
    """Persiste SECRET_KEY en config.env, reemplazando la línea existente si la hay."""
    lines = []
    if _CONFIG_FILE.exists():
        lines = _CONFIG_FILE.read_text(encoding="utf-8").splitlines()
    nuevas = []
    reemplazado = False
    for line in lines:
        if line.strip().startswith("SECRET_KEY="):
            nuevas.append(f"SECRET_KEY={key}")
            reemplazado = True
        else:
            nuevas.append(line)
    if not reemplazado:
        nuevas.append(f"SECRET_KEY={key}")
    _CONFIG_FILE.write_text("\n".join(nuevas) + "\n", encoding="utf-8")
