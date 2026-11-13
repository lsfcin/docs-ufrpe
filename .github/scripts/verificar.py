# verificar.py — confere o cabeçalho de cada documento do docs-ufrpe: os campos, a pasta e, com --online, se o sha256 bate com o arquivo oficial.
"""Uso: python .github/scripts/verificar.py [--online] [arquivo.md ...]

Sem arquivos, confere todos. Sai com 1 se algum documento tem erro; avisos não reprovam.
Só stdlib: a Action roda sem instalar nada.
"""
from __future__ import annotations

import argparse
import datetime
import hashlib
import json
import re
import ssl
import sys
import urllib.request
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
PASTAS = ('modelos', 'normas', 'orientacoes', 'tabelas')
FORA = {'CONTEXT.md', 'README.md', 'ISSUES.md'}
NOME = re.compile(r'^[a-z0-9]+(?:-[a-z0-9]+)*$')
DATA = re.compile(r'^\d{4}-\d{2}-\d{2}$')
HASH = re.compile(r'^[0-9a-f]{64}$')
# Os servidores da UFRPE não mandam o certificado intermediário; ele vem da URL de AIA do próprio certificado.
INTERMEDIARIOS = ('http://secure.globalsign.com/cacert/rnpicpedugr46ovtlsca2025.crt',)


def cabecalho(texto: str) -> dict | None:
    """O frontmatter `chave: valor` do topo; o valor é JSON quando dá, senão o texto cru."""
    if not texto.startswith('---\n'):
        return None
    fim = texto.find('\n---\n', 4)
    if fim < 0:
        return None
    campos = {}
    for linha in texto[4:fim].splitlines():
        if not linha.strip() or linha.startswith((' ', '#')):
            continue
        chave, _, valor = linha.partition(':')
        valor = valor.strip()
        try:
            campos[chave.strip()] = json.loads(valor) if valor else None
        except json.JSONDecodeError:
            campos[chave.strip()] = None if valor in ('null', '~') else valor.strip('"\'')
    return campos


def lugar(rel: Path) -> str | None:
    """Erro de pasta ou de nome, ou None. Formatos: <pasta>/<nome>/<nome>.md, e normas/federais/<nome>.md."""
    partes = rel.parts
    if partes[0] not in PASTAS:
        return f'fora das pastas {", ".join(PASTAS)}'
    if not NOME.match(rel.stem):
        return f'nome "{rel.stem}" não é minúsculo-com-hífens'
    if partes[:2] == ('normas', 'federais') and len(partes) == 3:
        return None
    dentro = partes[2:] if partes[:2] == ('normas', 'federais') else partes[1:]
    if len(dentro) != 2 or dentro[0] != rel.stem:
        return f'o arquivo deve ser {partes[0]}/<nome>/<nome>.md'
    return None


def conferir(rel: Path, texto: str, hoje: datetime.date) -> tuple[list[str], list[str], dict]:
    erros, avisos = [], []
    if (onde := lugar(rel)):
        erros.append(onde)
    campos = cabecalho(texto)
    if campos is None:
        return erros + ['sem cabeçalho (--- no topo)'], avisos, {}
    if not isinstance(campos.get('description'), str) or not campos['description'].strip():
        erros.append('falta description')
    origem = campos.get('origin')
    if not isinstance(origem, str) or not origem.startswith(('https://', 'http://')):
        erros.append('origin tem de ser o link oficial (https://...) do original')
    data = campos.get('origin_checked')
    if not isinstance(data, str) or not DATA.match(data):
        erros.append('origin_checked tem de ser AAAA-MM-DD')
    elif datetime.date.fromisoformat(data) > hoje:
        erros.append('origin_checked está no futuro')
    sha = campos.get('sha256')
    if sha is None:
        if rel.parts[:2] != ('normas', 'federais'):
            avisos.append('sem sha256: o mantenedor completa antes do merge')
    elif not isinstance(sha, str) or not HASH.match(sha):
        erros.append('sha256 tem de ter 64 caracteres hexadecimais')
    return erros, avisos, campos


def contexto_ssl() -> ssl.SSLContext:
    ctx = ssl.create_default_context()
    for url in INTERMEDIARIOS:
        try:
            der = urllib.request.urlopen(url, timeout=20).read()
            ctx.load_verify_locations(cadata=ssl.DER_cert_to_PEM_cert(der))
        except OSError:
            pass
    return ctx


def baixar_hash(url: str, ctx: ssl.SSLContext) -> str:
    pedido = urllib.request.Request(url, headers={'User-Agent': 'docs-ufrpe-verificar'})
    with urllib.request.urlopen(pedido, timeout=60, context=ctx) as resposta:
        return hashlib.sha256(resposta.read()).hexdigest()


def documentos(nomes: list[str]) -> list[Path]:
    if nomes:
        caminhos = [Path(n) for n in nomes]
    else:
        caminhos = [p.relative_to(RAIZ) for p in RAIZ.rglob('*.md') if '.git' not in p.parts]
    return sorted(p for p in caminhos
                  if p.suffix == '.md' and p.name not in FORA and p.parts[0] != '.github' and (RAIZ / p).exists())


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('--online', action='store_true', help='baixa o original e compara o sha256')
    ap.add_argument('arquivos', nargs='*')
    args = ap.parse_args(argv)
    hoje, ctx, reprovados = datetime.date.today(), None, 0
    for rel in documentos(args.arquivos):
        erros, avisos, campos = conferir(rel, (RAIZ / rel).read_text(encoding='utf-8'), hoje)
        if args.online and not erros and campos.get('sha256'):
            ctx = ctx or contexto_ssl()
            try:
                if baixar_hash(campos['origin'], ctx) != campos['sha256']:
                    erros.append('o sha256 não bate com o arquivo em origin (o original mudou, ou o link é de outro arquivo)')
            except OSError as e:
                avisos.append(f'não consegui baixar origin para conferir o sha256: {e}')
        for e in erros:
            print(f'ERRO  {rel}: {e}')
        for a in avisos:
            print(f'AVISO {rel}: {a}')
        if not erros and not avisos:
            print(f'ok    {rel}')
        reprovados += bool(erros)
    print(f'\n{reprovados} documento(s) com erro')
    return 1 if reprovados else 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
