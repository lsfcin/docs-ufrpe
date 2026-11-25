# tabela_censo.py — a tabela do censo no README do docs-ufrpe: por setor, quantos links entram, quantos já viraram documento, e os de fora e os pendentes por motivo.
"""Funções puras sobre as linhas de censo.tsv e fontes.tsv; quem lê os arquivos e grava o README é o vigiar.py. Só stdlib."""
from __future__ import annotations

import datetime
import re
import urllib.parse
from collections import Counter

import verificar

TIPOS = tuple(verificar.PASTA)
NOMES = {'calendario': 'calendários', 'modelo': 'formulários', 'norma': 'normas', 'orientacao': 'orientações', 'tabela': 'tabelas'}
MARCAS = ('<!-- censo:start -->', '<!-- censo:end -->')
CONTADO = re.compile(r'Contado em (\d\d)/(\d\d)/(\d{4})')


def contagem(linhas: list[dict], convertidos: set[str]) -> tuple[str, str, str, str]:
    """As quatro células de um setor: quantos entram por tipo, quantos deles já viraram .md, e os de fora e os pendentes por motivo.

    Um ato federal entra, mas não é do setor: fica fora do "N de M", porque o texto vem do espelho ou de normas/federais/."""
    entram = [l for l in linhas if l['decisao'] == 'entra']
    por_tipo = Counter(l['tipo'] for l in entram)
    federais = sum(1 for l in entram if l['motivo'] == 'federal')
    plural = f'{federais} federa' + ('l' if federais == 1 else 'is')
    partes = [f'{NOMES[t]} ({por_tipo[t]}' + (f', {plural})' if t == 'norma' and federais else ')') for t in TIPOS if por_tipo[t]]
    do_setor = [l['url'] for l in entram if l['motivo'] != 'federal']
    feitos = f'{sum(verificar.chave(u) in convertidos for u in do_setor)} de {len(do_setor)}' if do_setor else '—'
    def motivos(decisao: str) -> str:
        n = Counter(l['motivo'] or 'sem motivo' for l in linhas if l['decisao'] == decisao)
        return ', '.join(f'{m} ({k})' for m, k in n.most_common()) or '—'
    return ', '.join(partes) or '—', feitos, motivos('fora'), motivos('pendente')


def totais(linhas: list[dict]) -> tuple[str, str, str]:
    """Quantos entram, ficam de fora e estão pendentes: só o número, para a tabela caber na página."""
    n = Counter(l['decisao'] for l in linhas)
    return tuple(str(n[d]) if n[d] else '—' for d in ('entra', 'fora', 'pendente'))


def fontes_do_setor(paginas: list[str]) -> str:
    """Onde o setor lista seus documentos: até três links, e a partir daí o site e o fontes.tsv."""
    if len(paginas) > 3:
        site = urllib.parse.urlsplit(paginas[0])
        return f'[{site.netloc}]({site.scheme}://{site.netloc}/), {len(paginas)} páginas ([fontes.tsv](fontes.tsv))'
    return ', '.join(f'[{urllib.parse.unquote(urllib.parse.urlsplit(p).path).rstrip("/") or "/"}]({p})' for p in paginas)


def detalhe(setor: str, linhas: list[dict], convertidos: set[str], paginas: list[str]) -> str:
    """O que a tabela deixa de fora, recolhido: as fontes e, por tipo e por motivo, o que entra, fica fora ou está pendente."""
    entram, _, fora, pendentes = contagem(linhas, convertidos)
    itens = [('Fonte', fontes_do_setor(paginas)), ('Entram', entram), ('Ficam de fora', fora), ('Pendentes', pendentes)]
    corpo = '\n'.join(f'- **{nome}:** {texto}' for nome, texto in itens if texto != '—')
    return f'<details>\n<summary>{setor}: fontes e motivos</summary>\n\n{corpo}\n\n</details>'


def tabela(censo: dict[str, dict], fontes: list[dict], hoje: str, convertidos: set[str]) -> str:
    data = datetime.date.fromisoformat(hoje).strftime('%d/%m/%Y')
    linhas = [f'Contado em {data} por [vigiar.py](.github/scripts/vigiar.py), um link por arquivo; '
              'um arquivo publicado por dois setores conta no primeiro deles. '
              '"Convertidos" conta os que já estão no acervo, fora os atos federais; "Entram" os conta. '
              'As fontes e o motivo de cada exclusão estão em cada setor, logo abaixo da tabela.', '',
              '| Setor | Convertidos | Entram | Fora | Pendentes |', '|---|---|---|---|---|']
    detalhes: list[str] = []
    vistos: set[str] = set()
    for setor in dict.fromkeys(f['setor'] for f in fontes):
        meus = [l for u, l in censo.items() if setor in l['setores'].split(',') and u not in vistos]
        vistos |= {l['url'] for l in meus}
        feitos = contagem(meus, convertidos)[1]
        linhas.append(f'| {setor} | {feitos} | ' + ' | '.join(totais(meus)) + ' |')
        detalhes.append(detalhe(setor, meus, convertidos, [f['pagina'] for f in fontes if f['setor'] == setor]))
    return '\n'.join(linhas + [''] + detalhes)


def com_tabela(texto: str, texto_tabela: str) -> str:
    """O README com o bloco entre as MARCAS trocado pela tabela."""
    ini, fim = texto.index(MARCAS[0]) + len(MARCAS[0]), texto.index(MARCAS[1])
    return texto[:ini] + '\n' + texto_tabela + '\n' + texto[fim:]


def data_contada(texto: str) -> str:
    """A data da última coleta completa, lida do próprio bloco do README (AAAA-MM-DD)."""
    dia, mes, ano = CONTADO.search(texto).groups()
    return f'{ano}-{mes}-{dia}'
