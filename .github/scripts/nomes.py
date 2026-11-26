# nomes.py — o nome da pasta de cada documento do docs-ufrpe: o ato numerado (`res-cepe-989-2026`) e até quatro palavras de assunto.
from __future__ import annotations

import glob
import re
from pathlib import Path

import regras

PASTA_MAX = 60
ORGAOS = (('cepe', r'\bcepe\b|\brecepe'), ('consu', r'\bconsu\b|\brecu|\breconsu'), ('cura', r'\bcura\b'), ('prpg', r'\bprpg\b'),
          ('preg', r'\bpreg\b'), ('progepe', r'\bprogepe\b'), ('progesti', r'\bprogesti\b'))
# Palavras que não dizem o assunto: artigos, o tipo do ato, o órgão, meses, sobras do nome de arquivo.
VAZIAS = set('''a o as os e de da do das dos du no na nos nas n em para por com que ao aos sobre pela pelo pdf doc docx word
ufrpe ufrpe resolucao resolucoes res instrucao normativa in cepe consu cura prpg preg progepe progesti aprova altera
janeiro fevereiro marco abril maio junho julho agosto setembro outubro novembro dezembro assinado final atualizado
correto corrigido versao v copia anexo modelo arquivo recepe recu reconsu'''.split())
ANEXO = re.compile(r'\banexo ([ivxl]+|\d{1,2})\b')
COLADA = 19  # uma "palavra" maior que isto é nome de arquivo sem espaço (termodecompromissods, 20); internacionalizacao (19) é palavra


def palavras(texto: str) -> list[str]:
    return re.findall(r'[a-z0-9]+', regras.simples(texto))


def ato(texto: str) -> list[str]:
    """`res-cepe-989-2026` ou `in-prpg-01-2026` quando o título ou o arquivo diz que é um ato numerado; senão []."""
    s = ' '.join(palavras(texto))
    tipo = 'in' if re.search(r'\binstrucao normativa\b|\bin \d', s) else 'res' if re.search(r'\bres(olucao)?\b|\brecepe|\brecu|\breconsu', s) else ''
    numero = re.search(r'(?<![a-z0-9])(?:recepe|recu|reconsu|no|n)?\s?(\d{1,4})\s(?:de \d{1,2} de [a-z]+ de )?((?:19|20)\d\d)(?!\d)', s)
    if not tipo or not numero:
        return []
    prefixo = re.search(r'\b(recepe|recu|reconsu)\d', s)
    orgao = 'cepe' if prefixo and prefixo.group(1) == 'recepe' else 'consu' if prefixo else next((o for o, p in ORGAOS if re.search(p, s)), '')
    return [tipo, *([orgao] if orgao else []), numero.group(1).zfill(3 if tipo == 'res' else 2), numero.group(2)]


def anexo(texto: str) -> list[str]:
    """`anexo-iv` quando o título diz que é um anexo numerado; senão []."""
    achou = ANEXO.search(' '.join(palavras(texto)))
    return ['anexo', achou.group(1)] if achou else []


def sem_assunto(nome: str) -> bool:
    """O nome que o título deixou sem assunto (`anexo-v`, `documento`): espera o rótulo da descrição."""
    return bool(re.fullmatch(r'(?:anexo-[ivxl\d]+|documento)(?:-\d+)?', nome))


def pelo_rotulo(nome: str, descricao: str, usados: set[str]) -> str:
    """O nome sem assunto, completado pelo rótulo da descrição (`Mapa de visita domiciliar: …`)."""
    cabeca = anexo(nome.replace('-', ' '))
    return montar(cabeca, assunto(descricao.split(':', 1)[0], cabeca), usados)


def assunto(texto: str, cabeca: list[str]) -> list[str]:
    return [p for p in dict.fromkeys(palavras(texto)) if p not in VAZIAS and not re.search(r'\d', p) and p not in cabeca and len(p) <= COLADA]


def nome_da_pasta(linha: dict, usados: set[str]) -> str:
    """No padrão do acervo: o ato (ou o anexo) e até quatro palavras de assunto, do título e do nome do arquivo; `-2` se já existe."""
    texto = f'{linha["titulo"]} {Path(regras.arquivo(linha["url"])).stem}'
    cabeca = ato(texto) or anexo(texto)
    return montar(cabeca, assunto(texto, cabeca), usados)


def montar(cabeca: list[str], palavras_do_assunto: list[str], usados: set[str]) -> str:
    """A cabeça e o assunto (quatro palavras com cabeça, oito sem) até PASTA_MAX; `-2` se já existe."""
    partes = cabeca + palavras_do_assunto[:4 if cabeca else 8]
    nome = ''
    for p in partes:
        if len(nome) + len(p) + 1 > PASTA_MAX:
            break
        nome = f'{nome}-{p}' if nome else p
    nome = nome or 'documento'
    unico, n = nome, 2
    while unico in usados:
        unico, n = f'{nome}-{n}', n + 1
    usados.add(unico)
    return unico


def mover(md: Path, novo: str) -> Path:
    """Leva o documento para a pasta `novo`: a pasta, o .md, o original ao lado e o `source:` que aponta para ele."""
    pasta, velho = md.parent, md.parent.name
    destino = pasta.parent / novo
    if destino.exists():
        raise FileExistsError(destino)
    for original in pasta.parent.glob(f'{glob.escape(velho)}.*'):
        original.rename(original.with_name(novo + original.suffix))
    pasta.rename(destino)
    novo_md = (destino / md.name).rename(destino / f'{novo}.md')
    novo_md.write_text(novo_md.read_text(encoding='utf-8').replace(f'source: "../{velho}.', f'source: "../{novo}.', 1), encoding='utf-8')
    return novo_md
