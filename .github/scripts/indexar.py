# indexar.py — gera o busca.json do site do docs-ufrpe: título, descrição e texto puro de cada .md, para a caixa de busca.
"""Uso: python .github/scripts/indexar.py <pasta> [--saida busca.json]

Lê todo .md sob <pasta> (a árvore do git archive no deploy, ou o próprio repositório no CI) e grava o índice.
O texto sai sem marcação Markdown, sem comentários e sem as descrições de figura, que só trariam ruído
("setas, eixos, painéis"). Sai com 1 se nenhum documento foi lido. Só stdlib.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

# Uma descrição de figura vai do marcador até duas linhas em branco, o próximo marcador de página ou o fim; viewer.js usa a mesma regra.
FIGURA = re.compile(r'<!-- figure [^>]*-->\n[\s\S]*?(?=\n[ \t]*\n[ \t]*\n|<!-- page|$(?![\s\S]))')
COMENTARIO = re.compile(r'<!--[\s\S]*?-->')
IMAGEM = re.compile(r'!\[[^\]]*\]\([^)]*\)')
ETIQUETA = re.compile(r'</?[a-zA-Z][^>]*>')
LINK = re.compile(r'\[([^\]]*)\]\([^)]*\)')
MARCAS = re.compile(r'(^|\n)[ \t]*(?:#{1,6}[ \t]+|>[ \t]?|[-*+][ \t]+(?=\S))|[*_`|]|<\/?(?:details|summary|br)\s*\/?>|^-{3,}$', re.M)
PASTAS = {'orientacoes': 'Orientações'}
ESPACO = re.compile(r'[ \t]*\n[ \t\n]*|[ \t]{2,}')


def campos(texto: str) -> tuple[dict, str]:
    """O frontmatter `chave: valor` do topo, com o mesmo critério de verificar.py, e o corpo depois dele."""
    if not texto.startswith('---\n') or (fim := texto.find('\n---\n', 4)) < 0:
        return {}, texto
    lidos = {}
    for linha in texto[4:fim].splitlines():
        chave, sep, valor = linha.partition(':')
        if not sep or linha.startswith((' ', '#')):
            continue
        try:
            lidos[chave.strip()] = json.loads(valor.strip())
        except ValueError:
            lidos[chave.strip()] = valor.strip().strip('"\'')
    return lidos, texto[fim + 5:]


def puro(md: str) -> str:
    """O texto que um leitor vê, sem a marcação: é nele que a busca procura e de onde tira o trecho."""
    md = COMENTARIO.sub('', FIGURA.sub('', md))
    md = LINK.sub(r'\1', IMAGEM.sub('', md))
    md = ETIQUETA.sub('', MARCAS.sub(r'\1', md))
    return ESPACO.sub(lambda m: '\n' if '\n' in m.group() else ' ', md).strip()


def documento(raiz: Path, arquivo: Path) -> dict:
    meta, corpo = campos(arquivo.read_text(encoding='utf-8'))
    descricao = str(meta.get('description', ''))
    if arquivo.name in ('CONTEXT.md', 'README.md'):
        # O nome que o site mostra (viewer.js nomePasta): a home é o Início, cada pasta com maiúscula e acento.
        pasta = arquivo.parent.name if arquivo.name == 'CONTEXT.md' else ''
        titulo = PASTAS.get(pasta, pasta[:1].upper() + pasta[1:]) if pasta else 'Início'
        corpo = re.sub(r'^# .+\n(?:> .*\n)?', '', corpo.split('<!-- routing:start -->')[0], count=1, flags=re.M)
    else:
        # O mesmo rótulo da lista no site: o que vem antes dos dois-pontos da descrição ("Res. CONSU 009/2019").
        # Sem rótulo, vale o primeiro título do documento; sem título, a própria descrição.
        rotulo = re.match(r'^([^:]{2,40}):\s*(.+)$', descricao)
        h1 = re.search(r'^# (.+)$', corpo, re.M)
        h1 = re.sub(r'[*_]|\s+', lambda m: ' ' if m.group().isspace() else '', h1.group(1)).strip() if h1 else ''
        if rotulo:
            titulo, descricao = rotulo.group(1), rotulo.group(2)
        elif h1 and len(h1) <= 90:
            titulo = h1
        else:
            titulo, descricao = descricao or arquivo.stem, ''
    return {'doc': arquivo.relative_to(raiz).as_posix(), 'titulo': titulo, 'descricao': descricao, 'texto': puro(corpo)}


def indice(raiz: Path) -> list[dict]:
    arquivos = sorted(p for p in raiz.rglob('*.md') if '.github' not in p.parts and p.name != 'ISSUES.md'
                      and p.relative_to(raiz).as_posix() != 'CONTEXT.md')
    return [documento(raiz, p) for p in arquivos]


def main() -> None:
    ap = argparse.ArgumentParser(description='gera o busca.json do site')
    ap.add_argument('pasta', type=Path)
    ap.add_argument('--saida', type=Path)
    args = ap.parse_args()
    docs = indice(args.pasta.resolve())
    if not docs:
        sys.exit(f'nenhum .md em {args.pasta}')
    saida = args.saida or args.pasta / 'busca.json'
    saida.write_text(json.dumps(docs, ensure_ascii=False, separators=(',', ':')), encoding='utf-8')
    print(f'{len(docs)} documentos → {saida} ({saida.stat().st_size // 1024} KB)')


if __name__ == '__main__':
    main()
