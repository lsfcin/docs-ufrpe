# verificar.py — confere o cabeçalho de cada documento do docs-ufrpe: os campos, a pasta e, com --online, se o sha256 bate com o arquivo oficial.
"""Uso: python .github/scripts/verificar.py [--online] [arquivo.md ...]

Sem arquivos, confere todos. Sai com 1 se algum documento tem erro; avisos não reprovam.
Só stdlib: a Action roda sem instalar nada.
"""
from __future__ import annotations

import argparse
import csv
import datetime
import hashlib
import json
import re
import sys
import urllib.parse
from pathlib import Path

import rede
from indexar import MANUTENCAO

RAIZ = Path(__file__).resolve().parents[2]
PASTA = {'calendario': 'calendarios', 'modelo': 'modelos', 'norma': 'normas', 'orientacao': 'orientacoes', 'tabela': 'tabelas'}  # tipo do censo → pasta
PASTAS = tuple(PASTA.values())
CENSO = RAIZ / 'censo.tsv'
FORA = {'CONTEXT.md', 'README.md', *MANUTENCAO}
NOME = re.compile(r'^[a-z0-9]+(?:-[a-z0-9]+)*$')
DATA = re.compile(r'^\d{4}-\d{2}-\d{2}$')
HASH = re.compile(r'^[0-9a-f]{64}$')
# O mesmo corte que paginas.py e indexar.py fazem para achar o nome do documento.
ROTULO = re.compile(r'^[^:]{2,40}:\s*\S')
# Uma norma se chama como no lote 1: "Res. CEPE 609/2023", "Res. CONSU 435-A/2024", "IN PRPG 01/2026" — sem "Resolução", sem "/UFRPE".
NORMA = re.compile(r'^(?:Res|IN|Instrução|Resolução)\b')
NORMA_CANONICA = re.compile(r'^(?:Res\. (?:CONSU|CEPE|CURA) \d{3,4}(?:-[A-Z])?|IN [A-Z]+ \d{2})/\d{4}$')
# Ideograma, kana, hangul, caractere de substituição ou de uso privado num documento em português: lixo de OCR (um brasão, um QR code).
ESTRANHO = re.compile('[⺀-鿿가-힯豈-﫿-�]')


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


def nome(descricao: str) -> str:
    """O nome do documento: o que vem antes do primeiro dois-pontos da description."""
    return descricao.partition(':')[0].strip()


def repetidos(nomes: dict[Path, str]) -> dict[Path, str]:
    """Erro para cada documento cujo nome outro documento também usa: no site e na busca, os dois ficariam iguais."""
    donos: dict[str, list[Path]] = {}
    for rel, n in nomes.items():
        donos.setdefault(n, []).append(rel)
    return {rel: f'o nome "{n}" é também o de {", ".join(str(o) for o in donos[n] if o != rel)}'
            for rel, n in nomes.items() if len(donos[n]) > 1}


def lugar(rel: Path) -> str | None:
    """Erro de pasta ou de nome, ou None. Formatos: <pasta>/<nome>/<nome>.md, e normas/federais/<nome>.md."""
    partes = rel.parts
    if partes[0] not in PASTAS:
        return f'fora das pastas {", ".join(PASTAS)}'
    if not NOME.match(rel.stem):
        return f'nome "{rel.stem}" não é minúsculo-com-hífens'
    if federal(rel) and len(partes) == 3:
        return None
    dentro = partes[2:] if federal(rel) else partes[1:]
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
    elif not ROTULO.match(campos['description']):
        erros.append('description começa pelo nome do documento, até 40 caracteres, e dois-pontos ("Res. CONSU 009/2019: …"): é o nome no site e na busca')
    elif rel.parts[0] == 'normas' and not federal(rel) and NORMA.match(n := nome(campos['description'])) and not NORMA_CANONICA.match(n):
        erros.append(f'o nome "{n}" foge do padrão das normas: "Res. CEPE 609/2023", "Res. CONSU 435-A/2024", "IN PRPG 01/2026"')
    origem = campos.get('origin')
    if not isinstance(origem, str) or not origem.startswith(('https://', 'http://')):
        erros.append('origin tem de ser o link oficial (https://...) do original')
    data = campos.get('origin_checked')
    if not isinstance(data, str) or not DATA.match(data):
        erros.append('origin_checked tem de ser AAAA-MM-DD')
    elif datetime.date.fromisoformat(data) > hoje:
        erros.append('origin_checked está no futuro')
    for n, linha in enumerate(texto.splitlines(), 1):
        if (m := ESTRANHO.search(linha)):
            erros.append(f'linha {n}: caractere estranho "{m.group()}" (lixo de OCR? apague ou transcreva)')
    sha = campos.get('sha256')
    if sha is None:
        if not federal(rel):
            avisos.append('sem sha256: o mantenedor completa antes do merge')
    elif not isinstance(sha, str) or not HASH.match(sha):
        erros.append('sha256 tem de ter 64 caracteres hexadecimais')
    return erros, avisos, campos


def baixar_hash(url: str) -> str:
    return hashlib.sha256(rede.baixar(url)).hexdigest()


def documentos(nomes: list[str]) -> list[Path]:
    if nomes:
        caminhos = [Path(n) for n in nomes]
    else:
        caminhos = [p.relative_to(RAIZ) for p in RAIZ.rglob('*.md') if '.git' not in p.parts]
    return sorted(p for p in caminhos
                  if p.suffix == '.md' and p.name not in FORA and p.parts[0] != '.github' and (RAIZ / p).exists())


def federal(rel: Path) -> bool:
    return rel.parts[:2] == ('normas', 'federais')


def chave(url: str) -> str:
    """O mesmo arquivo, a mesma chave, codificado ou não, por http ou https (rede.baixar sobe um ao outro)."""
    return re.sub(r'^http://', 'https://', urllib.parse.unquote(url).strip())


URL_NA_NOTA = re.compile(r'http\S+')


def convertidos() -> set[str]:
    """As origens que já têm documento no acervo, e as que o `origin_note` diz que são o mesmo documento."""
    feitos = set()
    for rel in documentos([]):
        campos = cabecalho((RAIZ / rel).read_text(encoding='utf-8')) or {}
        if isinstance(campos.get('origin'), str):
            feitos.add(chave(campos['origin']))
        if isinstance(campos.get('origin_note'), str):
            feitos.update(chave(u.rstrip('.,;:)"\'')) for u in URL_NA_NOTA.findall(campos['origin_note']))
    return feitos


def ler_tsv(caminho: Path) -> list[dict]:
    if not caminho.exists():
        return []
    linhas = [l for l in caminho.read_text(encoding='utf-8').splitlines() if l.strip() and not l.startswith('#')]
    return list(csv.DictReader(linhas, delimiter='\t', quoting=csv.QUOTE_NONE))


def fora_do_censo(rel: Path, campos: dict, no_censo: set[str]) -> str | None:
    """Erro quando o original não tem linha no censo: o "N de M" do README não o contaria. Ato federal não é de setor."""
    origem = campos.get('origin')
    if federal(rel) or not isinstance(origem, str) or chave(origem) in no_censo:
        return None
    return 'origin sem linha no censo.tsv: ponha em fontes.tsv a página que publica o original e rode vigiar.py --gravar'


def fora_da_rota(rel: Path) -> str | None:
    """Erro quando o CONTEXT.md da pasta não lista o documento: a página da pasta no site é essa tabela."""
    pasta = next(p for p in rel.parents if (RAIZ / p / 'CONTEXT.md').exists())
    alvo = rel.relative_to(pasta).as_posix()
    if f']({alvo})' in (RAIZ / pasta / 'CONTEXT.md').read_text(encoding='utf-8'):
        return None
    return f'{pasta / "CONTEXT.md"} não o lista, e a página da pasta no site também não: rode core/hooks/routing/context_synchronizer.py {pasta}'


def pastas_fora_do_readme(readme: str) -> list[str]:
    """As pastas de documento que a tabela Organização do README não mostra."""
    organizacao = readme.partition('## Organização')[2].partition('\n## ')[0]
    return [p for p in PASTAS if f'[`{p}/`]' not in organizacao]


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('--online', action='store_true', help='baixa o original e compara o sha256')
    ap.add_argument('arquivos', nargs='*')
    args = ap.parse_args(argv)
    hoje, reprovados = datetime.date.today(), 0
    conferidos = {rel: conferir(rel, (RAIZ / rel).read_text(encoding='utf-8'), hoje) for rel in documentos(args.arquivos)}
    nomes = {rel: nome(c['description']) for rel, (_, _, c) in conferidos.items() if isinstance(c.get('description'), str)}
    duplicados = repetidos(nomes)
    no_censo = {chave(l['url']) for l in ler_tsv(CENSO)}
    for rel, (erros, avisos, campos) in conferidos.items():
        if rel in duplicados:
            erros.append(duplicados[rel])
        erros.extend(e for e in (fora_do_censo(rel, campos, no_censo), fora_da_rota(rel)) if e)
        if args.online and not erros and campos.get('sha256'):
            try:
                if baixar_hash(campos['origin']) != campos['sha256']:
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
    for pasta in pastas_fora_do_readme((RAIZ / 'README.md').read_text(encoding='utf-8')):
        print(f'ERRO  README.md: a tabela Organização não mostra a pasta {pasta}/')
        reprovados += 1
    print(f'\n{reprovados} documento(s) com erro')
    return 1 if reprovados else 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
