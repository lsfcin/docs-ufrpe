# duplicatas.py — o mesmo documento noutro link: o gêmeo DOC/DOCX de um PDF e a cópia byte a byte viram nota no `origin_note`; o mesmo ato noutro arquivo vai para a revisão.
from __future__ import annotations

import hashlib
import re
from pathlib import Path

import nomes
import regras
import verificar


class MesmoAto(OSError):
    """O link tem o nome de um ato do acervo e outro arquivo: versão, cópia assinada ou outro ato? Decide o mantenedor."""


def ato(texto: str) -> tuple[str, str, int, str] | None:
    """(tipo, órgão ou '', número, ano) do ato numerado que o texto nomeia; None se não nomeia."""
    partes = nomes.ato(texto)
    if not partes:
        return None
    tipo, *orgao, numero, ano = partes
    return tipo, orgao[0] if orgao else '', int(numero), ano


def mesmo_ato(a: tuple[str, str, int, str], b: tuple[str, str, int, str]) -> bool:
    """Mesmo tipo, número e ano; o órgão só separa quando os dois lados o dizem."""
    return (a[0], a[2], a[3]) == (b[0], b[2], b[3]) and (not a[1] or not b[1] or a[1] == b[1])


def no_acervo(linha: dict, dados: bytes, docs: list[tuple[Path, dict]]) -> tuple[str, Path] | None:
    """('copia', rel) se o arquivo baixado é byte a byte o de um documento; ('ato', rel) se o título e o nome do arquivo
    dizem o ato de uma pasta do acervo; None se é novo."""
    sha, proprio = hashlib.sha256(dados).hexdigest(), verificar.chave(linha['url'])
    docs = [(rel, c) for rel, c in docs if verificar.chave(str(c.get('origin', ''))) != proprio]  # no --refazer, o próprio documento
    for rel, campos in docs:
        if campos.get('sha256') == sha:
            return 'copia', rel
    arquivo = Path(regras.arquivo(linha['url'])).stem
    novo = ato(f'{linha["titulo"]} {arquivo}')
    for rel, _ in docs if novo else ():
        if (velho := ato(rel.parent.name)) and mesmo_ato(novo, velho):
            return 'ato', rel
    return None


def nota(destino: Path, frase: str) -> None:
    """Acrescenta a frase ao `origin_note`, ou o cria logo depois do `origin_checked`, onde o motor de PDF não escreve."""
    texto = destino.read_text(encoding='utf-8')
    antiga = (verificar.cabecalho(texto) or {}).get('origin_note')
    if isinstance(antiga, str) and antiga:
        texto, n = re.subn(r'^origin_note:.*\n', lambda _: verificar.campo('origin_note', f'{antiga.rstrip(".")}; {frase}'), texto, count=1, flags=re.M)
    else:
        texto, n = re.subn(r'^origin_checked:.*\n', lambda m: m.group(0) + verificar.campo('origin_note', frase), texto, count=1, flags=re.M)
    if not n or not verificar.cabecalho(texto):
        raise OSError(f'sem origin_checked para anotar em {destino.name}')
    destino.write_text(texto, encoding='utf-8')


def gemeos(destino: Path, urls: list[str]) -> None:
    """O DOC/DOCX do mesmo formulário que o PDF convertido."""
    formatos = '/'.join(dict.fromkeys(regras.extensao(u).upper() for u in urls))
    nota(destino, f'o mesmo formulário circula também em {formatos}: {", ".join(urls)}')


def copia(destino: Path, url: str) -> None:
    nota(destino, f'o mesmo arquivo circula também em: {url}')
