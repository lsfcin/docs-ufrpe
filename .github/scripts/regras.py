# regras.py — a triagem do censo do docs-ufrpe: dado o nome, o título e a seção de um link, diz o tipo e se ele entra, fica fora ou espera o mantenedor.
"""O critério é o do CONTEXT.md (19/11/2026) mais as regras de 21/11/2026: só a versão vigente entra; relatórios,
atos sobre pessoas e procedimentos específicos ficam fora; federais entram apontando para o espelho.
A primeira regra que casa vale; depois, a regra da página (fontes.tsv); senão, `pendente`. Só stdlib.
"""
from __future__ import annotations

import re
import unicodedata
import urllib.parse

GENERICO = re.compile(r'^(baixar|download|documento:?|clique aqui|aqui|acesse|link|pdf)$|\.(pdf|docx?)$', re.I)
ANO = re.compile(r'(?<!\d)(19[89]\d|20[0-4]\d)(?!\d)')
EXTENSAO = re.compile(r'(\.(pdf|docx?|odt|ods|odp|rtf|xlsx?|pptx?|zip))+$', re.I)
COPIA = re.compile(r'(\s*\(\d\)|_\d)+$')
PERIODO = re.compile(r'(?<!\d)(?:19|20)\d\d\s*(?:-|–|_|\.|/| a )\s*((?:19|20)\d\d)(?!\d)')

# (regex sobre "nome do arquivo, título, seção", sem acento e minúsculo; tipo; decisão; motivo).
REGRAS: list[tuple[re.Pattern, str, str, str]] = [(re.compile(p), t, d, m) for p, t, d, m in (
    (r'revogad|substituid', 'norma', 'fora', 'revogada'),
    (r'\blei\b ?(n|\d)|decreto|\bd\d{5}\b|portaria.*\b(mec|capes|cnpq)\b|\b(mec|capes)\b.*portaria|(resolucao|parecer) cne|rces\d|portaria n ?0?92 ?2011|arquivo nacional',
     'norma', 'entra', 'federal'),
    (r'\bedita(l|is)\b|resultado|convocac|classificac|selec(ao|oes)\b|chamada publica', '', 'fora', 'procedimento específico'),
    (r'\bportaria\b|\bport\b|nomeac|designac|\bprocesso ?\d{15}','', 'fora', 'ato sobre pessoas'),
    (r'relatorio (de )?(gestao|atividades|(parcial |integral )?(de )?auto ?avaliacao|parcial|integral|auditoria|cpa)|relato institucional'
     r'|em numeros|auditoria|dirigente .*controle interno|contr interno', '', 'fora', 'relatório'),
    (r'memoria|reuniao do dia', '', 'fora', 'memória de reunião'),
    (r'vencimento|remunerac|correlac|tabela salarial', 'tabela', 'entra', 'tabela'),
    (r'calendario', 'calendario', 'entra', 'calendário'),
    (r'manual|tutorial|cartilha|\bguia\b|passo a passo|perguntas (frequentes|e respostas?)|\bfaq\b|mapeamento|mapa de processos'
     r'|processos mapeados|identidade visual',
     'orientacao', 'entra', 'orientação'),
    (r'formulario|requerimento|ficha|termo de|declarac|solicitac|folha de ponto|requisicao|cancelamento|dados bancarios'
     r'|avaliacao professor|\bmodelo\b|plano de (estudo|ensino|pratica|atividade)', 'modelo', 'entra', 'formulário'),
    (r'instrucao normativa|\bin\b ?\d|resoluc|\bres\b|recepe|recu ?\d|reconsu|regimento|regulamento|estatuto|normas? gera', 'norma', 'entra', 'norma'),
    (r'oficio|circular|parecer|nota (tecnica|informativa)|orientac|fluxo|comunicado|documentacao necessaria|situacoes'
     r'|vacancia|custeio|exames e documentos|novas regras', 'orientacao', 'entra', 'orientação'),
    (r'\.(docx?|odt|xlsx?|ods)\b', 'modelo', 'entra', 'formulário'),
    (r'\btabelas?\b|plano de carreira', 'tabela', 'entra', 'tabela'),
    (r'\bpdi\b|plano de (desenvolvimento|integridade|internacionalizacao)', 'norma', 'entra', 'plano'),
)]


def simples(texto: str) -> str:
    return unicodedata.normalize('NFKD', texto).encode('ascii', 'ignore').decode().lower()


def nome_do_arquivo(url: str) -> str:
    """O nome do arquivo do link, legível: sem extensão, sem o sufixo de cópia (_0, (1)) e com espaços."""
    nome = urllib.parse.unquote(urllib.parse.urlsplit(url).path.rsplit('/', 1)[-1])
    nome = unicodedata.normalize('NFC', EXTENSAO.sub('', nome))
    return ' '.join(COPIA.sub('', nome).replace('_', ' ').split())


def titulo(texto_do_link: str, url: str, titulo_proprio: str = '') -> str:
    """O texto do link; quando ele não diz nada ("Baixar", "arquivo.pdf"), o título que só este link tem, e senão o nome do arquivo.

    Um título que abre vários links é cabeçalho de grupo ("Contato", "Público-alvo"), nunca o nome de um deles."""
    texto = texto_do_link.strip(' -–')
    if texto and not GENERICO.search(texto):
        return texto
    proprio = titulo_proprio.strip()
    return proprio if proprio and not GENERICO.search(proprio) else nome_do_arquivo(url)


def regra_da_pagina(campo: str) -> tuple[bool, tuple[str, str, str]] | None:
    """`tipo:decisao:motivo` da coluna regra de fontes.tsv; com `!` na frente, vale antes das REGRAS."""
    if not campo.strip():
        return None
    forca = campo.startswith('!')
    tipo, decisao, motivo = campo.lstrip('!').split(':')
    return forca, (tipo, decisao, motivo)


def classificar(url: str, nome_titulo: str, secao: str, pagina: tuple[bool, tuple[str, str, str]] | None = None,
                ano: int = 9999) -> tuple[str, str, str]:
    if pagina and pagina[0]:
        return pagina[1]
    nome = urllib.parse.unquote(urllib.parse.urlsplit(url).path.rsplit('/', 1)[-1])
    alvo = simples(f'{nome} {nome_titulo} {secao}').replace('_', ' ').replace('-', ' ')
    for regra, tipo, decisao, motivo in REGRAS:
        if regra.search(alvo):
            proprio = simples(f'{nome} {nome_titulo}')
            anos, fins = [int(a) for a in ANO.findall(proprio)], [int(a) for a in PERIODO.findall(proprio)]
            if motivo == 'plano' and fins and max(fins) < ano:
                return tipo, 'fora', 'versão superada'
            if motivo == 'calendário' and anos and max(anos) < ano - 1:
                return tipo, 'fora', 'versão superada'
            return tipo, decisao, motivo
    return pagina[1] if pagina else ('', 'pendente', '')
