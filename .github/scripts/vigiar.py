# vigiar.py — o censo do docs-ufrpe: coleta os links de documento das páginas de cada setor, compara com censo.tsv e diz o que é novo, o que sumiu e qual original mudou.
"""Uso: python .github/scripts/vigiar.py [--gravar] [--se-passaram N] [--sem-sha] [--de-pasta DIR]

fontes.tsv diz quais páginas cada setor publica; censo.tsv guarda cada link achado e a decisão sobre ele
(entra, fora ou pendente). Um link novo recebe a decisão de regras.py, ou `pendente`; uma decisão já
gravada nunca é reescrita. Um link só conta como sumido quando todas as páginas dos seus setores foram lidas.
--gravar aplica a diferença ao censo.tsv e refaz a tabela do README. --se-passaram N só roda se a última coleta
completa tem N dias ou mais, e fica em silêncio quando não há novidade; uma coleta com falha avisa e não
avança a data. --de-pasta lê páginas salvas pelo navegador (pela <link rel="canonical">) em vez da rede.
Sai com 1 quando alguma página falhou. Só stdlib.
"""
from __future__ import annotations

import argparse
import csv
import datetime
import html.parser
import re
import sys
import urllib.parse
from collections import Counter
from pathlib import Path
from typing import Callable

import rede
import regras
import verificar

RAIZ = verificar.RAIZ
FONTES = RAIZ / 'fontes.tsv'
CENSO = RAIZ / 'censo.tsv'
README = RAIZ / 'README.md'
ESTADO = RAIZ / '.vigia' / 'ultima.txt'
COLUNAS = ('url', 'setores', 'tipo', 'decisao', 'motivo', 'titulo', 'data')
TIPOS = tuple(verificar.PASTA)
NOMES = {'calendario': 'calendários', 'modelo': 'formulários', 'norma': 'normas', 'orientacao': 'orientações', 'tabela': 'tabelas'}
DOCUMENTO = re.compile(r'\.(pdf|docx?|odt|ods|odp|rtf|xlsx?|pptx?|zip)$', re.I)
TITULOS = {'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'strong', 'b', 'summary', 'button', 'dt'}
MARCAS = ('<!-- censo:start -->', '<!-- censo:end -->')

class Links(html.parser.HTMLParser):
    """Cada <a> que aponta para um arquivo de documento, com o texto do link e o último título visto antes dele."""

    def __init__(self, base: str):
        super().__init__(convert_charrefs=True)
        self.base, self.achados, self.secao = base, [], ''
        self._link: str | None = None
        self._texto: list[str] = []
        self._titulo: list[str] | None = None

    def handle_starttag(self, tag, attrs):
        if tag == 'a' and (h := dict(attrs).get('href')):
            url = rede.normalizar(h, self.base)
            if DOCUMENTO.search(urllib.parse.urlsplit(url).path):
                self._link, self._texto = url, []
        elif tag in TITULOS and self._link is None:
            self._titulo = []

    def handle_endtag(self, tag):
        if tag == 'a' and self._link:
            self.achados.append((self._link, ' '.join(''.join(self._texto).split()), self.secao))
            self._link = None
        elif tag in TITULOS and self._titulo is not None:
            if (t := ' '.join(''.join(self._titulo).split())):
                self.secao = t[:120]
            self._titulo = None

    def handle_data(self, data):
        if self._link is not None:
            self._texto.append(data)
        elif self._titulo is not None:
            self._titulo.append(data)


def links(pagina: str, base: str) -> list[tuple[str, str, str]]:
    leitor = Links(base)
    leitor.feed(pagina)
    return leitor.achados


def ler_tsv(caminho: Path) -> list[dict]:
    if not caminho.exists():
        return []
    linhas = [l for l in caminho.read_text(encoding='utf-8').splitlines() if l.strip() and not l.startswith('#')]
    return list(csv.DictReader(linhas, delimiter='\t', quoting=csv.QUOTE_NONE))


def gravar_censo(censo: dict[str, dict]) -> None:
    corpo = ['\t'.join(COLUNAS)] + ['\t'.join(censo[u].get(c, '') for c in COLUNAS) for u in sorted(censo)]
    cabeca = '# censo.tsv — cada link de documento que os setores da UFRPE publicam e a decisão sobre ele; mantido por .github/scripts/vigiar.py --gravar.\n'
    CENSO.write_text(cabeca + '\n'.join(corpo) + '\n', encoding='utf-8')


def coletar(fontes: list[dict], ler: Callable[[str], bytes]) -> tuple[dict[str, dict], dict[str, list[str]]]:
    """Os links achados (url → setores, título, seção) e, por setor, as páginas que falharam."""
    achados: dict[str, dict] = {}
    falhas: dict[str, list[str]] = {}
    for fonte in fontes:
        setor, pagina = fonte['setor'], fonte['pagina']
        try:
            texto = ler(pagina).decode('utf-8', 'replace')
        except (OSError, ValueError) as e:
            falhas.setdefault(setor, []).append(f'{pagina}: {e}')
            continue
        for url, texto_link, secao in links(texto, pagina):
            titulo = regras.titulo(texto_link, secao)
            item = achados.setdefault(url, {'setores': set(), 'paginas': set(), 'titulo': titulo, 'secao': secao})
            item['setores'].add(setor)
            item['paginas'].add(pagina)
            if len(titulo) > len(item['titulo']):
                item['titulo'] = titulo
    return achados, falhas


def comparar(censo: dict[str, dict], achados: dict[str, dict], falhas: dict[str, list[str]]) -> tuple[list[str], list[str]]:
    novos = sorted(u for u in achados if u not in censo)
    sumidos = sorted(u for u, linha in censo.items() if u not in achados
                     and not set(linha['setores'].split(',')) & set(falhas))
    return novos, sumidos


def aplicar(censo: dict[str, dict], achados: dict[str, dict], novos: list[str], sumidos: list[str], fontes: list[dict], hoje: str) -> None:
    """Grava os novos com a triagem de regras.py; a regra de página só vale se todas as páginas do link a têm."""
    da_pagina = {f['pagina']: regras.regra_da_pagina(f.get('regra') or '') for f in fontes}
    for u in novos:
        a = achados[u]
        pagina = {da_pagina[p] for p in a['paginas']}
        tipo, decisao, motivo = regras.classificar(u, a['titulo'], a['secao'], pagina.pop() if len(pagina) == 1 else None,
                                                   datetime.date.fromisoformat(hoje).year)
        titulo = (a['titulo'] or a['secao']).replace('\t', ' ')
        censo[u] = {'url': u, 'setores': '', 'tipo': tipo, 'decisao': decisao, 'motivo': motivo, 'titulo': titulo, 'data': hoje}
    for u, a in achados.items():
        censo[u]['setores'] = ','.join(sorted(set(filter(None, censo[u]['setores'].split(','))) | a['setores']))
    for u in sumidos:
        del censo[u]


def contagem(linhas: list[dict]) -> tuple[str, str, str]:
    """As três células de um setor: quantos entram por tipo, e os de fora e os pendentes por motivo."""
    entram = Counter(l['tipo'] for l in linhas if l['decisao'] == 'entra')
    federais = sum(1 for l in linhas if l['decisao'] == 'entra' and l['motivo'] == 'federal')
    partes = [f'{NOMES[t]} ({entram[t]}' + (f', {federais} federais)' if t == 'norma' and federais else ')') for t in TIPOS if entram[t]]
    def motivos(decisao: str) -> str:
        n = Counter(l['motivo'] or 'sem motivo' for l in linhas if l['decisao'] == decisao)
        return ', '.join(f'{m} ({k})' for m, k in n.most_common()) or '—'
    return ', '.join(partes) or '—', motivos('fora'), motivos('pendente')


def tabela(censo: dict[str, dict], fontes: list[dict], hoje: str) -> str:
    data = datetime.date.fromisoformat(hoje).strftime('%d/%m/%Y')
    linhas = [f'Contado em {data} por [vigiar.py](.github/scripts/vigiar.py), um link por arquivo; '
              'um arquivo publicado por dois setores conta no primeiro deles.', '',
              '| Setor | Fonte | Entram | Ficam de fora | Pendentes |', '|---|---|---|---|---|']
    vistos: set[str] = set()
    for setor in dict.fromkeys(f['setor'] for f in fontes):
        meus = [l for u, l in censo.items() if setor in l['setores'].split(',') and u not in vistos]
        vistos |= {l['url'] for l in meus}
        meus_links = [f['pagina'] for f in fontes if f['setor'] == setor]
        paginas = ', '.join(f'[{urllib.parse.unquote(urllib.parse.urlsplit(p).path).rstrip("/") or "/"}]({p})' for p in meus_links)
        if len(meus_links) > 3:
            site = urllib.parse.urlsplit(meus_links[0])
            paginas = f'[{site.netloc}]({site.scheme}://{site.netloc}/), {len(meus_links)} páginas ([fontes.tsv](fontes.tsv))'
        entram, fora, pendentes = contagem(meus)
        linhas.append(f'| {setor} | {paginas} | {entram} | {fora} | {pendentes} |')
    return '\n'.join(linhas)


def refazer_readme(texto_tabela: str) -> None:
    texto = README.read_text(encoding='utf-8')
    ini, fim = texto.index(MARCAS[0]) + len(MARCAS[0]), texto.index(MARCAS[1])
    README.write_text(texto[:ini] + '\n' + texto_tabela + '\n' + texto[fim:], encoding='utf-8')


def shas_mudados() -> list[str]:
    """Os .md do acervo cujo original não tem mais o sha256 gravado, ou não baixou."""
    avisos = []
    for rel in verificar.documentos([]):
        campos = verificar.cabecalho((RAIZ / rel).read_text(encoding='utf-8')) or {}
        if not campos.get('sha256'):
            continue
        try:
            if verificar.baixar_hash(campos['origin']) != campos['sha256']:
                avisos.append(f'MUDOU  {rel}: o original em origin não tem mais o sha256 gravado')
        except OSError as e:
            avisos.append(f'FALHOU {rel}: {e}')
    return avisos


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('--gravar', action='store_true', help='aplica a diferença ao censo.tsv e refaz a tabela do README')
    ap.add_argument('--se-passaram', type=int, metavar='N', help='só roda se a última coleta completa tem N dias ou mais')
    ap.add_argument('--sem-sha', action='store_true', help='não baixa os originais do acervo')
    ap.add_argument('--de-pasta', type=Path, help='lê páginas salvas em vez da rede')
    args = ap.parse_args(argv)
    hoje = datetime.date.today()
    if args.se_passaram is not None and ESTADO.exists():
        if (hoje - datetime.date.fromisoformat(ESTADO.read_text().strip())).days < args.se_passaram:
            return 0
    fontes = ler_tsv(FONTES)
    censo = {l['url']: l for l in ler_tsv(CENSO)}
    achados, falhas = coletar(fontes, rede.salvas(args.de_pasta) if args.de_pasta else rede.baixar)
    novos, sumidos = comparar(censo, achados, falhas)
    mudados = [] if args.sem_sha or args.de_pasta else shas_mudados()
    saida = [f'NOVO   {u}  ({", ".join(sorted(achados[u]["setores"]))}) {achados[u]["titulo"]}' for u in novos]
    saida += [f'SUMIU  {u}  ({censo[u]["setores"]})' for u in sumidos] + mudados
    saida += [f'FALHOU {setor}: {f}' for setor, fs in falhas.items() for f in fs]
    if saida or args.se_passaram is None:
        print('\n'.join(saida) or 'nada novo')
        print(f'\n{len(achados)} links lidos · {len(novos)} novos · {len(sumidos)} sumidos · '
              f'{len(mudados)} originais mudados ou fora · {sum(map(len, falhas.values()))} páginas com falha')
        if args.se_passaram is not None:
            print('Para gravar: python code/docs-ufrpe/.github/scripts/vigiar.py --gravar')
    if args.gravar:
        aplicar(censo, achados, novos, sumidos, fontes, hoje.isoformat())
        gravar_censo(censo)
        if falhas:
            print('README não refeito: a tabela só sai de uma coleta completa.')
        else:
            refazer_readme(tabela(censo, fontes, hoje.isoformat()))
    if not falhas and not args.de_pasta:
        ESTADO.parent.mkdir(exist_ok=True)
        ESTADO.write_text(hoje.isoformat() + '\n')
    return 1 if falhas else 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
