# limpeza.py — o corpo que os motores devolvem, limpo do que não é texto: a imagem que o Google Docs embute e a caixa de seleção que o OCR lê como ideograma.
from __future__ import annotations

import re
from pathlib import Path

# A caixa de seleção vista pelo OCR (口 日 目 品) e os marcadores Symbol/Wingdings de uso privado (U+F0B7, U+F0D8): o verificar.py recusa todos.
CAIXAS = str.maketrans({'口': '☐', '日': '☐', '目': '☐', '品': '☐', '': '•', '': '➢'})


def sem_imagens(corpo: str) -> str:
    """Tira a imagem que o Google Docs embute em base64 (`[image1]: <data:…>` e o `![][image1]` que a usa): é brasão,
    não texto, e sozinha estoura o limite de tamanho do arquivo."""
    corpo = re.sub(r'^\[image\d+\]: <data:[^>]*>\s*$', '', corpo, flags=re.M)
    return re.sub(r'!\[[^\]]*\]\[image\d+\]', '', corpo)


def caixas(corpo: str) -> str:
    return corpo.translate(CAIXAS)


def arquivo(destino: Path) -> str:
    """Limpa o corpo do .md convertido e o devolve; o frontmatter fica byte a byte."""
    texto = destino.read_text(encoding='utf-8')
    fim = texto.find('\n---\n', 4) + 5 if texto.startswith('---\n') else 0
    corpo = caixas(texto[fim:])
    destino.write_text(texto[:fim] + corpo, encoding='utf-8')
    return corpo
