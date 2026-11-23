# indexar.py — gera o busca.json do site do docs-ufrpe (título, descrição e texto puro de cada .md, para a caixa de busca) e o acervo.md (todos os documentos numa URL, para uma IA).
"""Uso: python .github/scripts/indexar.py <pasta> [--saida busca.json]

Lê todo .md sob <pasta> (a árvore do git archive no deploy, ou o próprio repositório no CI) e grava o índice
e, ao lado dele, o acervo.md.
O texto sai sem marcação Markdown, sem comentários e sem as descrições de figura, que só trariam ruído
("setas, eixos, painéis"). Sai com 1 se nenhum documento foi lido. Só stdlib.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import date
from pathlib import Path

# Uma descrição de figura vai do marcador até duas linhas em branco, o próximo marcador de página ou o fim; paginas.py usa a mesma regra.
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
        # O nome que o site mostra (paginas.py nome_pasta): a home é o Início, cada pasta com maiúscula e acento.
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


def arquivos(raiz: Path) -> list[Path]:
    return sorted(p for p in raiz.rglob('*.md') if '.github' not in p.parts and p.name not in ('ISSUES.md', 'acervo.md')
                  and p.relative_to(raiz).as_posix() != 'CONTEXT.md')


def indice(raiz: Path) -> list[dict]:
    return [documento(raiz, p) for p in arquivos(raiz)]


def acervo(raiz: Path, docs: list[dict], versao: str) -> str:
    """Um .md só com todos os documentos, cada um sob seu nome, com o link do original e o da página no site: uma fonte
    do NotebookLM lê uma URL. O topo diz de quando e de que commit é a cópia e lista o que ela contém."""
    docs = [d for d in docs if not d['doc'].endswith(('README.md', 'CONTEXT.md'))]
    partes = ['# Docs UFRPE — o acervo inteiro\n\nDocumentos oficiais da UFRPE em Markdown (https://ufrpe.pages.dev/docs/). '
              'Não é site oficial; em caso de divergência, prevalece o original de cada documento. "Conferido em" é a data em '
              'que o texto foi comparado com o original, não garantia de que o documento ainda vale.\n\n'
              f'Gerado em {date.today():%d/%m/%Y}, de {versao}. Uma cópia importada numa IA não se atualiza: '
              'importe de novo depois de uma mudança no site.\n\n## Índice\n\n'
              + ''.join(f"- {d['titulo']}\n" for d in docs)]
    for d in docs:
        meta, corpo = campos((raiz / d['doc']).read_text(encoding='utf-8'))
        origem = f"Original oficial: {meta['origin']} · conferido em {meta.get('origin_checked', '?')}\n" if meta.get('origin') else ''
        pagina = f"Página no site: https://ufrpe.pages.dev/docs/{d['doc'][:-3]}\n\n"
        partes.append(f"\n---\n\n# {d['titulo']}\n\n{origem}{pagina}{COMENTARIO.sub('', corpo).strip()}\n")
    return ''.join(partes)


def main() -> None:
    ap = argparse.ArgumentParser(description='gera o busca.json do site')
    ap.add_argument('pasta', type=Path)
    ap.add_argument('--saida', type=Path)
    ap.add_argument('--versao', default='uma cópia de trabalho', help='de onde vem a árvore, ex.: "main@3964f4a"')
    args = ap.parse_args()
    docs = indice(args.pasta.resolve())
    if not docs:
        sys.exit(f'nenhum .md em {args.pasta}')
    saida = args.saida or args.pasta / 'busca.json'
    saida.write_text(json.dumps(docs, ensure_ascii=False, separators=(',', ':')), encoding='utf-8')
    junto = saida.parent / 'acervo.md'
    junto.write_text(acervo(args.pasta.resolve(), docs, args.versao), encoding='utf-8', newline='\n')
    print(f'{len(docs)} documentos → {saida} ({saida.stat().st_size // 1024} KB), {junto} ({junto.stat().st_size // 1024} KB)')


if __name__ == '__main__':
    main()
