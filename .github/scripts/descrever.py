# descrever.py — reescreve só a linha `description` dos documentos do docs-ufrpe com uma descrição de uma linha escrita por um worker externo gratuito.
"""Uso: python .github/scripts/descrever.py [--setor PRPG] [--so-rascunho] [--limite N] [--seco] [arquivos.md ...]

Sem arquivos, pega todo o acervo. Um documento por chamada (isola a falha). O worker é o deepseek, por
`core/run tools/panel/ask --only deepseek`; se ele falhar, estourar o tempo ou responder fora do formato, o codex
(gpt-6-luna) tenta uma vez. Resposta inválida nos dois: o arquivo não muda e o documento entra na lista "para revisão".
--setor PRPG: só os documentos cuja descrição ainda é o rascunho do conversor, que termina em ` (PRPG).`
--so-rascunho: o mesmo sem nomear o setor, qualquer ` (Setor).` que abre com maiúscula.
--seco só mostra o que chamaria. Roda no workspace do mantenedor; ao worker vai apenas o texto do documento.
"""
from __future__ import annotations

import argparse
import datetime
import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Callable

import converter
import indexar
import verificar

RAIZ = verificar.RAIZ
CORPO_MAX = 6000   # com 2500 um modelo leu o calendário errado: o corte tem de pegar o documento quase todo
DESCRICAO_MAX = 180  # as do lote 1 têm mediana de 115; com 300, o deepseek escrevia 200 e o Nome virava seção do texto
TEMPO = 90         # segundos por chamada; medianas de 24/11/2026: deepseek 17 s, codex 53 s. Com 300, um deepseek pendurado custava 5 min por documento
CODEX = Path('/usr/lib/chatgpt/resources/codex')
MODELO_CODEX = 'gpt-6-luna'
PREFERIDOS = ('modelos/in-gr-01-2024-apendice-1-pda', 'normas/res-consu-434-2024-carga-horaria-docente',
              'orientacoes/oficio-circular-004-2024-progressao-docente')  # as descrições de referência; faltando uma, vale a primeira boa da pasta
RASCUNHO = re.compile(r' \(([A-Z][A-Za-z]+)\)\.$')  # o que converter.descricao grava: `Nome: resto (SETOR).`
NUMERACAO = re.compile(r'^(?:(?:\d+|N)[.)]|[-*•])\s*')
PREFIXO = re.compile(r'^description:\s*', re.I)
LINHA_DESCRICAO = re.compile(r'^description:[^\r\n]*', re.M)
INSTRUCAO = ('Escreva a linha `description` deste documento. Formato: `Nome: resto.` — Nome até 40 caracteres, sem dois-pontos, '
             'diz o que o documento é: o tipo e o número quando houver (Res. CEPE 123/2024, IN PRPG 01/2026, Formulário de …, '
             'Manual do …), nunca um programa, anexo ou seção de dentro dele; norma da UFRPE se abrevia sempre assim, '
             'sem "Resolução" nem "UFRPE" no nome: Res. CONSU 233/2022, Res. CURA 070/2023, IN PRPG 01/2026; depois, para que serve e quem usa, numa frase. '
             f'Tudo em até 140 caracteres (nunca mais de {DESCRICAO_MAX}). Sem inventar. Expanda sigla só se o texto a expandir. '
             'Responda só com essa linha, sem numeração nem aspas.')


def rascunho(descricao: str, setor: str | None = None) -> bool:
    """A descrição que o conversor deixou (`… (PRPG).`); com `setor`, só a desse setor."""
    achou = RASCUNHO.search(descricao)
    return bool(achou) and (setor is None or achou.group(1) == setor)


def corpo_limpo(texto: str) -> str:
    """O texto do documento para o worker: sem frontmatter, sem figuras (a imagem e a descrição dela), sem comentários, cortado em CORPO_MAX."""
    corpo = indexar.campos(texto)[1]
    for lixo in (indexar.FIGURA, indexar.COMENTARIO, indexar.IMAGEM):
        corpo = lixo.sub('', corpo)
    return re.sub(r'\n{3,}', '\n\n', corpo).strip()[:CORPO_MAX]


def exemplos_do_acervo(n: int = 3) -> list[str]:
    """Até `n` descrições boas do acervo, uma por pasta: as que já não são rascunho e passam na validação, as PREFERIDOS primeiro."""
    por_pasta: dict[str, str] = {}
    for rel in sorted(verificar.documentos([]), key=lambda r: (r.parent.as_posix() not in PREFERIDOS, r)):
        descricao = indexar.campos((RAIZ / rel).read_text(encoding='utf-8'))[0].get('description')
        if isinstance(descricao, str) and not rascunho(descricao) and not invalida(descricao):
            por_pasta.setdefault(rel.parts[0], descricao)
    return list(por_pasta.values())[:n]


def montar_prompt(texto: str, exemplos: list[str]) -> str:
    lista = '\n'.join(f'- {e}' for e in exemplos)
    return f'{INSTRUCAO}\n\nExemplos de boas linhas, já no acervo:\n{lista}\n\nDocumento:\n\n{corpo_limpo(texto)}\n'


def ler_resposta(bruto: str) -> str:
    """A primeira linha útil: sem o cabeçalho `<!-- panel -->`, sem numeração (`1.`, `N.`, `-`), sem `description:`, sem aspas nem crases."""
    for linha in indexar.COMENTARIO.sub('', bruto).splitlines():
        linha = PREFIXO.sub('', NUMERACAO.sub('', linha.strip())).strip(' \t"\'`“”')
        if linha:
            return linha
    return ''


def invalida(descricao: str) -> str:
    """Por que a descrição não serve ('' quando serve): as mesmas regras de verificar.py, mais ponto final e tamanho."""
    if not verificar.ROTULO.match(descricao):
        return 'não é `Nome: resto` (Nome de 2 a 40 caracteres, sem dois-pontos)'
    if not descricao.endswith('.'):
        return 'não termina em ponto'
    if len(descricao) > DESCRICAO_MAX:
        return f'passa de {DESCRICAO_MAX} caracteres'
    if verificar.ESTRANHO.search(descricao):
        return 'caractere estranho'
    return ''


def trocar_descricao(texto: str, descricao: str) -> str | None:
    """Troca só a linha `description:` do frontmatter, o resto byte a byte; None se o documento não tem."""
    if not texto.startswith('---\n') or (fim := texto.find('\n---\n', 4)) < 0:
        return None
    cabeca, resto = texto[:fim], texto[fim:]
    nova, trocas = LINHA_DESCRICAO.subn(lambda _: f'description: {json.dumps(descricao, ensure_ascii=False)}', cabeca, count=1)
    return nova + resto if trocas else None


def deepseek(prompt: str) -> str:
    """`core/run tools/panel/ask --only deepseek <prompt.md>`: a resposta vem em stdout, depois de um comentário `<!-- panel -->`."""
    with tempfile.TemporaryDirectory() as pasta:
        arquivo = Path(pasta) / 'prompt.md'
        arquivo.write_text(prompt, encoding='utf-8')
        return executar([str(converter.core_run()), 'tools/panel/ask', '--only', 'deepseek', str(arquivo)], pasta)


def codex(prompt: str) -> str:
    """`codex exec -s read-only -m gpt-6-luna … -o <saida> "<prompt>"`, numa pasta vazia: ele não enxerga o repo."""
    if not CODEX.is_file():
        raise OSError(f'sem {CODEX}')
    with tempfile.TemporaryDirectory() as pasta:
        saida = Path(pasta) / 'saida.txt'
        executar([str(CODEX), 'exec', '-s', 'read-only', '-m', MODELO_CODEX, '--ephemeral', '--skip-git-repo-check',
                  '-o', str(saida), prompt], pasta)
        return saida.read_text(encoding='utf-8')


def executar(comando: list[str], pasta: str) -> str:
    r = subprocess.run(comando, capture_output=True, text=True, timeout=TEMPO, cwd=pasta)
    if r.returncode:
        ultima = (r.stderr or r.stdout).strip().splitlines()
        raise OSError(ultima[-1] if ultima else 'falhou')
    return r.stdout


ESCRITORES = (deepseek, codex)


def descrever(texto: str, escrever: Callable[[str], str] | tuple[Callable[[str], str], ...] = ESCRITORES,
              exemplos: list[str] | None = None, rel: Path = Path('modelos/a/a.md')) -> tuple[str | None, str]:
    """(texto com a descrição nova, '') ou (None, por que nenhum escritor serviu). Os escritores vão em ordem; o seguinte só
    entra quando o anterior falha, estoura o tempo ou responde fora do formato. A troca ainda passa por verificar.conferir:
    não pode criar erro que o documento não tinha."""
    escritores = (escrever,) if callable(escrever) else escrever
    if not corpo_limpo(texto):
        return None, 'corpo vazio: sem texto, o worker inventaria a descrição (reconverta o documento)'
    prompt = montar_prompt(texto, exemplos if exemplos is not None else exemplos_do_acervo())
    motivos = []
    for escritor in escritores:
        try:
            descricao = ler_resposta(escritor(prompt))
        except (OSError, subprocess.SubprocessError) as e:
            motivos.append(f'{escritor.__name__}: falhou ({e})')
            continue
        if (porque := invalida(descricao) or ('' if descricao else 'resposta vazia')):
            motivos.append(f'{escritor.__name__}: {porque}')
            continue
        novo = trocar_descricao(texto, descricao)
        if novo is None:
            return None, 'o documento não tem `description` no frontmatter'
        hoje = datetime.date.today()
        if (novos := set(verificar.conferir(rel, novo, hoje)[0]) - set(verificar.conferir(rel, texto, hoje)[0])):
            motivos.append(f'{escritor.__name__}: "{descricao}" reprova no verificar.py ({"; ".join(sorted(novos))})')
            continue
        return novo, ''
    return None, '; '.join(motivos)


def escolher(setor: str | None, so_rascunho: bool, nomes: list[str]) -> list[Path]:
    """Os documentos pedidos (ou todos) cuja descrição atual é um rascunho, quando um dos filtros foi dado."""
    docs = verificar.documentos(nomes)
    if setor is None and not so_rascunho:
        return docs
    return [d for d in docs if rascunho(str(indexar.campos((RAIZ / d).read_text(encoding='utf-8'))[0].get('description', '')), setor)]


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description='Reescreve a linha `description` dos documentos com um worker gratuito (deepseek, depois codex).')
    ap.add_argument('--setor', help='só os documentos cuja descrição ainda é o rascunho do conversor, que termina em " (SETOR)." (ex.: PRPG)')
    ap.add_argument('--so-rascunho', action='store_true', help='o mesmo sem nomear o setor: só as descrições que terminam em " (Setor)." com maiúscula')
    ap.add_argument('--limite', type=int, help='no máximo N documentos')
    ap.add_argument('--seco', action='store_true', help='monta o prompt e mostra o que chamaria, sem chamar worker nem gravar')
    ap.add_argument('arquivos', nargs='*', help='documentos .md; sem eles, todo o acervo')
    args = ap.parse_args(argv)
    sys.stdout.reconfigure(line_buffering=True)
    fila = escolher(args.setor, args.so_rascunho, args.arquivos)[:args.limite]
    exemplos = exemplos_do_acervo()
    if not args.seco:
        converter.core_run()  # sem workspace não há deepseek: pare antes da primeira chamada
    revisao, feitos = [], 0
    for rel in fila:
        texto = (RAIZ / rel).read_bytes().decode('utf-8')
        velha = indexar.campos(texto)[0].get('description')
        if args.seco:
            prompt = montar_prompt(texto, exemplos)
            print(f'{rel}: {velha}\n  prompt {len(prompt)} caracteres\n  1) core/run tools/panel/ask --only deepseek <prompt.md>\n'
                  f'  2) {CODEX} exec -s read-only -m {MODELO_CODEX} --ephemeral --skip-git-repo-check -o <saida.txt> "<prompt>"')
            continue
        novo, porque = descrever(texto, ESCRITORES, exemplos, rel)
        if novo is None:
            revisao.append((rel, porque))
            print(f'{rel}: PARA REVISÃO ({porque})')
            continue
        (RAIZ / rel).write_bytes(novo.encode('utf-8'))
        feitos += 1
        print(f'{rel}: {velha} -> {indexar.campos(novo)[0]["description"]}')
    for rel, porque in revisao:
        print(f'para revisão  {rel}  {porque}')
    print(f'\n{len(fila)} na fila · {feitos} reescritos · {len(revisao)} para revisão')
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
