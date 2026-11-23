# paginas.py — gera o HTML pronto de cada .md do site do docs-ufrpe: faixa, cartão do original, texto e rodapé, sem JavaScript para ler. O JS do site só busca e destaca.
"""Uso: python .github/scripts/paginas.py <pasta>

Roda no deploy, depois do indexar.py, sobre a árvore do git archive: grava ao lado de cada .md a página dele
(README.md → index.html, <pasta>/CONTEXT.md → <pasta>/index.html, a/b.md → a/b.html, servido em /docs/a/b),
mais a do acervo e a lista de todos os documentos. Precisa de markdown-it-py (o venv do workspace).
"""
from __future__ import annotations

import argparse
import html
import json
import posixpath
import re
import sys
from pathlib import Path

from markdown_it import MarkdownIt

sys.path.insert(0, str(Path(__file__).resolve().parent))
from indexar import COMENTARIO, FIGURA, PASTAS, arquivos, campos  # noqa: E402

REPO = 'https://github.com/lsfcin/docs-ufrpe'
# O caderno público do NotebookLM: /docs/notebook/ é um redirect (site/_redirects), então recriar o caderno não toca aqui.
CADERNO = 'notebook/'
TRAD = {'Subdirectory': 'Pasta', 'File': 'Documento', 'Description': 'Descrição', 'Routing': 'Nesta seção'}
# Sem HTML vindo do texto (um PR de fora não injeta script): passam só <br>, <details> e <summary>, sem atributos.
ETIQUETA_SOLTA = re.compile(r'<(?!br\s*/?>|/?details>|/?summary>)', re.I)
IMAGEM_LOCAL = re.compile(r'!\[[^\]]*\]\((?!https?:)[^)]*\)')
URL_NUA = re.compile(r'(?<![(<\]"\'=])\bhttps?://[^\s<>()\[\]]+[^\s<>()\[\].,;:!?\'"]')
TABELA = re.compile(r'<table>[\s\S]*?</table>')
LINHA = re.compile(r'<tr>([\s\S]*?)</tr>')
CELULA = re.compile(r'<t[dh][^>]*>([\s\S]*?)</t[dh]>')
SO_LINK = re.compile(r'^\s*<a href="([^"]*)"[^>]*>([\s\S]*?)</a>\s*$')
SEM_TAG = re.compile(r'<[^>]+>')
# Os .md que ganham página (main preenche): um link para outro .md, como o CONTEXT.md e o ISSUES.md da raiz, vai ao GitHub.
PAGINAS: set[str] = set()
MD = MarkdownIt('commonmark', {'html': True}).enable(['table', 'strikethrough'])

esc = html.escape


def nome_pasta(p: str) -> str:
    return PASTAS.get(p, p[:1].upper() + p[1:])


def texto_de(trecho: str) -> str:
    return html.unescape(SEM_TAG.sub('', trecho)).strip()


def pagina(doc: str) -> str:
    """Onde a página de um .md é servida, relativa à raiz do site: '' (início), 'pasta/' ou 'a/b'."""
    if doc == 'README.md':
        return ''
    return doc[:-len('CONTEXT.md')] if doc.endswith('/CONTEXT.md') else doc[:-3]


def arquivo_html(doc: str) -> str:
    alvo = pagina(doc)
    return 'index.html' if not alvo else f'{alvo}index.html' if alvo.endswith('/') else f'{alvo}.html'


def relativo(de: str, alvo: str) -> str:
    """O href que leva da página de `de` ao caminho `alvo` (relativo à raiz); toda página resolve a partir da pasta do seu .md."""
    rel = posixpath.relpath('/' + alvo.rstrip('/'), '/' + posixpath.dirname(de))
    pasta = alvo.endswith('/') or not alvo
    return './' if rel == '.' else rel + '/' if pasta else rel


def religar(doc: str, href: str) -> str:
    """Um link do texto: externo abre em outra aba, .md vira a página dele, o resto aponta para o arquivo no GitHub."""
    href = html.unescape(href)
    if re.match(r'^https?:', href, re.I):
        return f'href="{esc(href)}" target="_blank" rel="noopener"'
    if href.startswith('#'):
        return f'href="{esc(href)}"'
    if re.match(r'^[a-z]+:', href, re.I):
        return ''
    caminho, _, ancora = href.partition('#')
    alvo = posixpath.normpath(posixpath.join(posixpath.dirname(doc), caminho)) + ('/' if caminho.endswith('/') else '')
    if alvo.endswith('/'):
        alvo += 'CONTEXT.md'
    if alvo in PAGINAS:
        return f'href="{esc(relativo(doc, pagina(alvo)))}{"#" + esc(ancora) if ancora else ""}"'
    return f'href="{REPO}/blob/main/{esc(alvo)}" target="_blank" rel="noopener"'


def figuras(md: str) -> str:
    """As figuras não entram no git; a descrição delas fica recolhida (a mesma fronteira do indexar.py)."""
    def recolhe(m: re.Match) -> str:
        bloco = m.group()[m.group().index('-->\n') + 4:]
        tipo = re.search(r'Tipo de figura:\*\*\s*([^\n.(]+)', bloco)
        resumo = f'Figura: {tipo.group(1).strip()}'.replace('<', '').replace('>', '') if tipo else 'Descrição da figura'
        return f'\n<details>\n<summary>\n{resumo}\n</summary>\n\n{bloco}\n</details>\n\n' if bloco.strip() else ''
    return FIGURA.sub(recolhe, md)


def rotulo(nome: str, desc: str) -> tuple[str, str]:
    if nome.endswith('/'):
        return nome_pasta(nome[:-1].split('/')[-1]), desc
    m = re.match(r'^([^:]{2,40}):\s*(.+)$', desc)
    return (m.group(1), m.group(2)[:1].upper() + m.group(2)[1:]) if m else (nome.split('/')[-1].removesuffix('.md'), desc)


def tabela(t: str) -> str:
    """Uma tabela cuja 1ª coluna é só link vira lista: nome legível à esquerda, descrição à direita."""
    linhas = [CELULA.findall(r) for r in LINHA.findall(t)]
    cabeca, corpo = linhas[0], linhas[1:]
    links = [SO_LINK.match(c[0]) for c in corpo]
    if not corpo or not all(links):
        t = re.sub(r'<th([^>]*)>([^<]*)</th>', lambda m: f'<th{m.group(1)}>{TRAD.get(m.group(2).strip(), m.group(2))}</th>', t)
        return f'<div class="tabela">{t}</div>'
    pasta = bool(re.search('Subdirectory|Pasta', texto_de(cabeca[0])))
    itens = []
    for celulas, a in zip(corpo, links):
        nome, desc = rotulo(texto_de(a.group(2)), texto_de(celulas[-1]))
        itens.append(f'<tr><td class="acao"><a class="pill" href="{a.group(1)}">{esc(nome)}</a></td><td>{esc(desc)}</td></tr>')
    return (f'<div class="tabela"><table class="entradas"><thead><tr><th>{"Pastas" if pasta else "Documentos"}</th>'
            f'<th>Descrição</th></tr></thead><tbody>{"".join(itens)}</tbody></table></div>')


def corpo_html(doc: str, md: str) -> str:
    md = ETIQUETA_SOLTA.sub('&lt;', IMAGEM_LOCAL.sub('', COMENTARIO.sub('', figuras(md))))
    md = URL_NUA.sub(lambda m: f'<{m.group()}>', md)
    if re.search(r'(^|/)(README|CONTEXT)\.md$', doc):
        # O resumo de uma linha sob o título (e o `> spec:`) é para o GitHub e o agente; a página não o mostra.
        md = re.sub(r'^(# .+\n)(?:>.*\n)+', r'\1', md, count=1, flags=re.M)
    feito = MD.render(md)
    feito = re.sub(r'<a href="([^"]*)"', lambda m: f'<a {religar(doc, m.group(1))}', feito)
    feito = TABELA.sub(lambda m: tabela(m.group()), feito)
    feito = re.sub(r'<h2>([^<]+)</h2>', lambda m: f'<h2>{TRAD.get(m.group(1).strip(), m.group(1))}</h2>', feito)
    if (pasta := re.search(r'([\w-]+)/CONTEXT\.md$', doc)):
        feito = feito.replace(f'<h1>{pasta.group(1)}</h1>', f'<h1>{esc(nome_pasta(pasta.group(1)))}</h1>', 1)
    return feito


def cartao(c: dict, botao: str) -> str:
    if not re.match(r'^https?:', str(c.get('origin', '')), re.I):
        return ''
    dia = str(c.get('origin_checked', ''))
    conferido = f' · conferido em {"/".join(reversed(dia.split("-")))}' if re.match(r'^\d{4}-\d{2}-\d{2}$', dia) else ''
    desc = f'<p class="desc">{esc(str(c["description"]))}</p>' if c.get('description') else ''
    aviso = ('<p class="aviso">Texto convertido automaticamente, ainda não revisado. Em caso de divergência, prevalece o original.</p>'
             if c.get('needs_review') is True else '')
    return (f'<aside class="cartao">{desc}<p><a class="btn forte" href="{esc(c["origin"])}" target="_blank" rel="noopener">'
            f'Original oficial ↗</a>{botao}<span class="meta">{conferido}</span></p>{aviso}</aside>')


def inicio(art: str, botao: str) -> str:
    """Na home, o título e o aviso "prevalece o original" saem (a faixa já os dá); o parágrafo "Pergunte a uma IA" vira cartão."""
    art = re.sub(r'<h1>[\s\S]*?</h1>\s*', '', art, count=1)
    art = re.sub(r'<p>(?:(?!</p>)[\s\S])*?prevalece o original[\s\S]*?</p>\s*', '', art, count=1)
    forte = botao.replace('class="btn"', 'class="btn forte"')
    return re.sub(rf'<p>(?:(?!</p>)[\s\S])*?/docs/{CADERNO}"[\s\S]*?</p>', lambda m: (
        f'<aside class="cartao"><p>{forte}<span class="meta">requer conta Google</span></p>{m.group()}</aside>'), art, count=1)


def trilha(doc: str) -> str:
    partes = doc.split('/')[:-1][:2 if doc.startswith('normas/federais/') else 1]
    return ''.join(f' / <a href="{relativo(doc, "/".join(partes[:i + 1]) + "/")}">{esc(nome_pasta(p))}</a>' for i, p in enumerate(partes))


CABECA = '''<!doctype html>
<html lang="pt-BR">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{titulo}</title>
  <meta name="description" content="{descricao}">
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Work+Sans:ital,wght@0,400;0,600;0,700;1,400&display=swap">
  <link rel="stylesheet" href="{raiz}viewer.css">
  <link rel="alternate" type="text/markdown" href="{fonte}">
  <script src="{raiz}busca.js" defer></script>
  <script src="{raiz}viewer.js" defer></script>
</head>
<body data-raiz="{raiz}" data-doc="{doc}">
<header class="cabeca"><div class="dentro">
  <a class="marca" href="{raiz}"><img src="{raiz}brasao-negativo.png" alt="Universidade Federal Rural de Pernambuco"></a>
  <a class="marca texto" href="{raiz}"><b>Docs<br>UFRPE</b></a>
  <p class="explica">Documentos oficiais da Universidade Federal Rural de Pernambuco (UFRPE), reproduzidos em Markdown para leitura no celular, busca e citação. Este site não é oficial da UFRPE. Em caso de divergência, prevalece o documento original.</p>
  <p class="autoria">Iniciativa pessoal de Lucas Silva Figueiredo, professor do Departamento de Computação da UFRPE.</p>
  <form class="busca" role="search"><label for="q">Buscar nos documentos</label>
    <input id="q" type="search" autocomplete="off" enterkeyhint="search" placeholder="interstício, RSC, acerto financeiro…"></form>
</div></header>'''

RODAPE = '''<footer>
  <a class="btn" href="{repo}/edit/main/{doc}" target="_blank" rel="noopener">Propor correção</a>
  <button class="btn" id="copiar" hidden>Copiar texto para IA</button>
  <a class="btn" href="{fonte}" target="_blank" rel="noopener">Texto em Markdown</a>
  <a class="btn" href="{raiz}todos">Todos os documentos</a>
  <a class="btn" href="{repo}" target="_blank" rel="noopener">Repositório no GitHub</a>
</footer></div>
</body>
</html>
'''


def montar(doc: str, bruto: str) -> str:
    raiz = relativo(doc, '')
    botao = f'<a class="btn" href="{raiz}{CADERNO}" target="_blank" rel="noopener">Perguntar ao NotebookLM ↗</a>'
    meta, md = campos(bruto)
    art = corpo_html(doc, md)
    if doc == 'README.md':
        art = inicio(art, botao)
    # A aba leva o mesmo nome que a busca: o rótulo da description; o h1 de um PDF convertido pode ser lixo de OCR.
    h1 = re.search(r'<h1>([\s\S]*?)</h1>', art)
    rot = re.match(r'^([^:]{2,40}):', str(meta.get('description', '')))
    nome = rot.group(1) if rot else texto_de(h1.group(1)) if h1 else ''
    campos_cabeca = {
        'titulo': esc(f'{nome} · Docs UFRPE' if nome and doc != 'README.md' else 'Docs UFRPE'),
        'descricao': esc(str(meta.get('description') or 'Documentos oficiais da UFRPE em Markdown, cada um com o link para o original.')),
        'raiz': raiz, 'fonte': esc(posixpath.basename(doc)), 'doc': esc(doc), 'repo': REPO}
    nav = '' if doc == 'README.md' else f'<nav class="topo"><a href="{raiz}">Início</a>{trilha(doc)}</nav>'
    return (CABECA.format(**campos_cabeca) + f'{nav}<section id="resultados" class="container" aria-live="polite" hidden></section>\n'
            f'<div class="container">{cartao(meta, botao)}\n<article class="markdown-body">{art}</article>\n'
            + RODAPE.format(**campos_cabeca))


def todos(docs: list[dict]) -> str:
    """Uma página com um link por documento: por onde um agente que só recebeu a raiz chega a cada texto."""
    linhas = ''.join(f"- [{d['titulo']}]({d['doc']}){': ' + d['descricao'] if d['descricao'] else ''}\n"
                     for d in docs if not d['doc'].endswith(('README.md', 'CONTEXT.md')))
    return ('# Todos os documentos\n\nCada documento do acervo, com o nome e o assunto. O acervo inteiro num texto só, '
            'para importar numa IA: [acervo](acervo.md).\n\n' + linhas)


def main() -> None:
    ap = argparse.ArgumentParser(description='gera o HTML pronto de cada .md do site')
    ap.add_argument('pasta', type=Path)
    args = ap.parse_args()
    raiz = args.pasta.resolve()
    indice = raiz / 'busca.json'
    docs = json.loads(indice.read_text(encoding='utf-8'))
    for d in docs:
        d['pagina'] = pagina(d['doc'])
    indice.write_text(json.dumps(docs, ensure_ascii=False, separators=(',', ':')), encoding='utf-8')
    (raiz / 'todos.md').write_text(todos(docs), encoding='utf-8', newline='\n')
    PAGINAS.update(fontes := [p.relative_to(raiz).as_posix() for p in arquivos(raiz) if p.name != 'todos.md'] + ['acervo.md', 'todos.md'])
    for doc in fontes:
        destino = raiz / arquivo_html(doc)
        destino.parent.mkdir(parents=True, exist_ok=True)
        destino.write_text(montar(doc, (raiz / doc).read_text(encoding='utf-8')), encoding='utf-8', newline='\n')
    print(f'{len(fontes)} páginas em {raiz}')


if __name__ == '__main__':
    main()
