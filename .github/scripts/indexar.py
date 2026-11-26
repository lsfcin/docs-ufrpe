# indexar.py — gera o busca.json do site do docs-ufrpe (título, descrição e texto puro de cada .md, para a caixa de busca) e o acervo.md (todos os documentos numa URL, para uma IA).
"""Uso: python .github/scripts/indexar.py <pasta> [--saida busca.json]

Lê todo .md sob <pasta> (a árvore do git archive no deploy, ou o próprio repositório no CI) e grava o índice
e, ao lado dele, o acervo.md e os volumes acervo-1.md…acervo-N.md (até PALAVRAS palavras cada, para o NotebookLM).
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

# As listas do mantenedor na raiz: não são documentos do acervo (verificar.py usa a mesma).
MANUTENCAO = ('ISSUES.md', 'ROADMAP.md')
# Uma descrição de figura vai do marcador até duas linhas em branco, o próximo marcador de página ou o fim; paginas.py usa a mesma regra.
FIGURA = re.compile(r'<!-- figure [^>]*-->\n[\s\S]*?(?=\n[ \t]*\n[ \t]*\n|<!-- page|$(?![\s\S]))')
COMENTARIO = re.compile(r'<!--[\s\S]*?-->')
# Teto de um volume do acervo: o NotebookLM recusa uma fonte de 500 mil palavras, e conta palavras do seu jeito.
PALAVRAS = 400_000
IMAGEM = re.compile(r'!\[[^\]]*\]\([^)]*\)')
ETIQUETA = re.compile(r'</?[a-zA-Z][^>]*>')
LINK = re.compile(r'\[([^\]]*)\]\([^)]*\)')
MARCAS = re.compile(r'(^|\n)[ \t]*(?:#{1,6}[ \t]+|>[ \t]?|[-*+][ \t]+(?=\S))|[*_`|]|<\/?(?:details|summary|br)\s*\/?>|^-{3,}$', re.M)
PASTAS = {'calendarios': 'Calendários', 'orientacoes': 'Orientações'}
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


def oculto(rel: Path) -> bool:
    return any(parte.startswith('.') for parte in rel.parts)


def arquivos(raiz: Path) -> list[Path]:
    """Os .md publicados; pasta oculta (.github, .pytest_cache, .vigia) não, porque o deploy só vê o que o git carrega."""
    return sorted(p for p in raiz.rglob('*.md') if not oculto(p.relative_to(raiz)) and p.name not in (*MANUTENCAO, 'acervo.md')
                  and p.relative_to(raiz).as_posix() != 'CONTEXT.md')


def indice(raiz: Path) -> list[dict]:
    return [documento(raiz, p) for p in arquivos(raiz)]


def cabeca(titulo: str, versao: str, docs: list[dict], aviso: str = '') -> str:
    """O topo de cada arquivo para IA: o que é, de quando e de que commit é a cópia, e o índice do que ele contém."""
    return (f'# Docs UFRPE — {titulo}\n\nDocumentos oficiais da UFRPE em Markdown (https://ufrpe.pages.dev/docs/). '
            'Não é site oficial; em caso de divergência, prevalece o original de cada documento. "Conferido em" é a data em '
            'que o texto foi comparado com o original, não garantia de que o documento ainda vale.\n\n'
            f'Gerado em {date.today():%d/%m/%Y}, de {versao}. Uma cópia importada numa IA não se atualiza: '
            f'importe de novo depois de uma mudança no site.{aviso}\n\n## Índice\n\n' + ''.join(f"- {d['titulo']}\n" for d in docs))


def bloco(raiz: Path, d: dict) -> str:
    """Um documento sob seu nome, com o link do original e o da página no site."""
    meta, corpo = campos((raiz / d['doc']).read_text(encoding='utf-8'))
    origem = f"Original oficial: {meta['origin']} · conferido em {meta.get('origin_checked', '?')}\n" if meta.get('origin') else ''
    pagina = f"Página no site: https://ufrpe.pages.dev/docs/{d['doc'][:-3]}\n\n"
    return f"\n---\n\n# {d['titulo']}\n\n{origem}{pagina}{COMENTARIO.sub('', corpo).strip()}\n"


def do_acervo(docs: list[dict]) -> list[dict]:
    """Os documentos, sem as páginas de pasta, na ordem pasta → caminho."""
    return sorted((d for d in docs if not d['doc'].endswith(('README.md', 'CONTEXT.md'))), key=lambda d: d['doc'])


def acervo(raiz: Path, docs: list[dict], versao: str) -> str:
    """Um .md só com todos os documentos: uma IA lê o acervo inteiro numa URL."""
    docs = do_acervo(docs)
    return cabeca('o acervo inteiro', versao, docs) + ''.join(bloco(raiz, d) for d in docs)


def volumes(raiz: Path, docs: list[dict], versao: str, limite: int = PALAVRAS) -> list[str]:
    """O acervo em volumes de até `limite` palavras, cortados entre documentos, para a fonte do NotebookLM, que recusa
    500 mil palavras. Na ordem pasta → caminho, um documento novo só desloca os volumes depois do seu. Um documento
    maior que o limite fica sozinho num volume."""
    grupos: list[list[tuple[dict, str]]] = [[]]
    soma = 0
    for d in do_acervo(docs):
        texto = bloco(raiz, d)
        n = len(texto.split())
        if grupos[-1] and soma + n > limite:
            grupos.append([])
            soma = 0
        grupos[-1].append((d, texto))
        soma += n
    total = len(grupos)
    aviso = (f' Este é um dos {total} volumes do acervo (o NotebookLM recusa uma fonte de 500 mil palavras): '
             'importe todos, um por fonte; a lista está em https://ufrpe.pages.dev/docs/todos.')
    return [cabeca(f'acervo, volume {i} de {total}', versao, [d for d, _ in g], aviso) + ''.join(t for _, t in g)
            for i, g in enumerate(grupos, 1)]


def main() -> None:
    ap = argparse.ArgumentParser(description='gera o busca.json do site')
    ap.add_argument('pasta', type=Path)
    ap.add_argument('--saida', type=Path)
    ap.add_argument('--versao', default='uma cópia de trabalho', help='de onde vem a árvore, ex.: "main@3964f4a"')
    args = ap.parse_args()
    raiz = args.pasta.resolve()
    docs = indice(raiz)
    if not docs:
        sys.exit(f'nenhum .md em {args.pasta}')
    saida = args.saida or args.pasta / 'busca.json'
    saida.write_text(json.dumps(docs, ensure_ascii=False, separators=(',', ':')), encoding='utf-8')
    junto = saida.parent / 'acervo.md'
    junto.write_text(acervo(raiz, docs, args.versao), encoding='utf-8', newline='\n')
    for velho in saida.parent.glob('acervo-*.md'):
        velho.unlink()
    partes = volumes(raiz, docs, args.versao)
    for i, texto in enumerate(partes, 1):
        (saida.parent / f'acervo-{i}.md').write_text(texto, encoding='utf-8', newline='\n')
    print(f'{len(docs)} documentos → {saida} ({saida.stat().st_size // 1024} KB), {junto} ({junto.stat().st_size // 1024} KB), '
          f'{len(partes)} volumes acervo-N.md')


if __name__ == '__main__':
    main()
