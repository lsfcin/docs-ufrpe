# federal.py — o ato federal que um setor da UFRPE hospeda: a lei fica no espelho, o resto entra pela cópia do setor, com a nota que diz de onde o texto veio.
"""O PDF que o setor hospeda é, em geral, o texto compilado do Planalto (Lucas e o painel, 26/11/2026): entra por ele,
e o `origin_note` diz que é cópia e qual a última alteração que o próprio texto mostra. O `sha256` só prova que o
setor não trocou o arquivo, não que o ato segue igual: a nota dá a quem lê a data até onde o texto vai."""
from __future__ import annotations

import re
from pathlib import Path

import duplicatas
import regras

ESPELHO = re.compile(r'\blei\b')  # sobre o título simples; a lei inteira já está no ctresb/leis
FEDERAIS = 'normas/federais'
ALTERACAO = re.compile(
    r'\((?:reda[cç][aã]o dada|inclu[ií]d[oa]|revogad[oa]|acrescid[oa]|acrescentad[oa]|renumerad[oa]|vide)(?:\s+pel[oa]s?)?\s+'
    r'((?:decreto|lei|medida provis[oó]ria)(?: complementar)?\s+n[º°o.]*\s*[\d.]+)\s*,?\s*de\s+(?:\d{1,2}\.?º?\s+de\s+\w+\s+de\s+)?(\d{4})',
    re.I)


ATO = re.compile(r'\b(decreto|portaria|d(?=\d{4,5}\b))\D{0,12}?(\d{1,2}\.?\d{3}|\d{3,5})')
ANO = re.compile(r'(?<!\d)((?:19|20)\d\d)(?!\d)')


def nome(linha: dict) -> str | None:
    """`decreto-7485-2011`, `portaria-658-2026`: o ato federal pelo número e pelo ano, que o título do setor
    quase sempre traz; None quando o título não diz o número (o nome vem então do padrão do acervo)."""
    if linha['motivo'] != 'federal' or linha['tipo'] != 'norma':
        return None
    titulo = regras.simples(linha['titulo'])
    achado = ATO.search(titulo)
    if not achado:
        return None
    tipo, numero = achado.groups()
    ano = ANO.search(titulo[achado.end():achado.end() + 30])
    return '-'.join(p for p in ('decreto' if tipo == 'd' else tipo, numero.replace('.', ''), ano and ano.group(1)) if p)


def no_espelho(linha: dict) -> bool:
    """A lei federal não ganha documento: só uma linha com o link, na página de normas/federais."""
    return linha['motivo'] == 'federal' and bool(ESPELHO.search(regras.simples(linha['titulo'])))


def pasta(linha: dict, pastas: dict[str, str]) -> str:
    """O decreto, a portaria e a IN federais vão para normas/federais; a orientação federal fica em orientacoes."""
    return FEDERAIS if linha['motivo'] == 'federal' and linha['tipo'] == 'norma' else pastas[linha['tipo']]


def ultima_alteracao(texto: str) -> str | None:
    """`Decreto nº 11.072, de 2022`: o ato mais recente que o texto compilado diz ter alterado algum dispositivo."""
    achados = [(int(ano), ' '.join(ato.split())) for ato, ano in ALTERACAO.findall(texto)]
    if not achados:
        return None
    ano, ato = max(achados)
    return f'{ato[0].upper()}{ato[1:]}, de {ano}'


def anotar(destino: Path, setor: str) -> None:
    """Grava no `origin_note` que o texto é a cópia do setor e até onde ele vai."""
    ultima = ultima_alteracao(destino.read_text(encoding='utf-8'))
    ate = f'a última alteração que o texto mostra é a do {ultima}' if ultima else 'o texto não mostra alteração posterior'
    duplicatas.nota(destino, f'Cópia hospedada pela {setor}, não a publicação do órgão que editou o ato; {ate}.')
