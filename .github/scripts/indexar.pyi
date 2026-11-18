from _typeshed import Incomplete
from pathlib import Path

FIGURA: Incomplete
COMENTARIO: Incomplete
IMAGEM: Incomplete
ETIQUETA: Incomplete
LINK: Incomplete
MARCAS: Incomplete
PASTAS: Incomplete
ESPACO: Incomplete

def campos(texto: str) -> tuple[dict, str]: ...
def puro(md: str) -> str: ...
def documento(raiz: Path, arquivo: Path) -> dict: ...
def indice(raiz: Path) -> list[dict]: ...
def main() -> None: ...
