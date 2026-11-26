# converter.py — o lote do docs-ufrpe: cada link `entra` do censo que ainda não tem .md vira documento, pelos motores do workspace.
"""Uso: python .github/scripts/converter.py --setor PRPG [--tipo norma] [--federal] [--limite N] [--seco] [--refazer]

Só roda no workspace do mantenedor, porque chama três ferramentas dele por `core/run`: o PDF vai por
`tools/pdf/pymupdf`, e o DOC e o DOCX sobem ao Drive como Google Doc temporário e voltam por `tools/docs/gdocs
read`, o que mantém as tabelas em Markdown puro. O original fica ao lado da pasta e não entra no git.
Não convertem: lei federal (regra do espelho ctresb/leis), planilha e o que falhar; o resto do federal entra pela cópia
do setor, com a nota de federal.py. Esses vão para
.vigia/fila.tsv com o motivo. --seco só lista o que faria. --refazer converte de novo o que já tem documento
(cada um na pasta que já tem, e o motor sobrescreve), menos o que tem `reviewed_by`: correção à mão não se refaz. O mesmo formulário em PDF e em DOC/DOCX vira um documento só,
o do PDF, e o link do DOC/DOCX vai no `origin_note`. O arquivo que o acervo já tem byte a byte também vai só
para o `origin_note` do documento; o mesmo ato noutro arquivo vai para a fila, à revisão (duplicatas.py).
"""
from __future__ import annotations

import argparse
import datetime
import hashlib
import re
import subprocess
import sys
from pathlib import Path

import duplicatas
import federal
import limpeza
import nomes
import rede
import regras
import verificar

RAIZ = verificar.RAIZ
FILA = RAIZ / '.vigia' / 'fila.tsv'
FIGURAS = RAIZ / '.github' / 'figuras'  # o perfil de relevância de figura deste acervo (.github/figuras/CONTEXT.md)
PASTA = verificar.PASTA
ROTA = {'pdf': 'pdf', 'doc': 'gdoc', 'docx': 'gdoc'}
NOME_MAX = 40
FORMATO = r'word|pdf|docx?'  # o que o título diz do formato, e não do formulário
MOTOR_GDOC = 'Google Docs import + export (gdocs read)'
TEMPO = 900  # segundos por chamada; um manual só de capturas de tela pede --tempo maior (cada figura vai ao modelo de visão)


def cabecalhos() -> list[tuple[Path, dict]]:
    """Cada documento do acervo com o seu frontmatter."""
    return [(rel, verificar.cabecalho((RAIZ / rel).read_text(encoding='utf-8')) or {}) for rel in verificar.documentos([])]


def pastas_existentes() -> dict[str, str]:
    """{origem: pasta que o documento já tem}, para o --refazer não criar `-2`."""
    return {verificar.chave(c['origin']): rel.parent.name for rel, c in cabecalhos() if isinstance(c.get('origin'), str) and len(rel.parts) == 3}


def ja_feitos(refazer: bool) -> set[str]:
    """O que a rodada não converte: tudo o que tem documento, ou, no --refazer, só o que tem correção à mão (`reviewed_by`)."""
    return verificar.convertidos(so_revisados=refazer)


def mesmo_formulario(linha: dict) -> tuple[str, str]:
    """(tipo, título sem a marca de formato): `TERMO - DS (WORD)` e `TERMO - DS` são o mesmo formulário."""
    t = regras.simples(linha['titulo'])
    t = re.sub(rf'\(\s*(?:{FORMATO})\s*\)', ' ', t)
    return linha['tipo'], ' '.join(re.sub(rf'\s(?:{FORMATO})$', '', ' '.join(t.split())).split())


def faltantes(linhas: list[dict], setor: str, tipo: str | None, feitos: set[str]) -> list[dict]:
    """Os `entra` do setor (o primeiro da coluna setores, como na tabela do README) sem documento. O DOC/DOCX do mesmo
    formulário que um PDF não é convertido: o link dele vai na `duplicatas` da linha do PDF."""
    fila = [l for l in linhas if l['decisao'] == 'entra' and l['setores'].split(',')[0] == setor
            and (tipo is None or l['tipo'] == tipo) and verificar.chave(l['url']) not in feitos]
    pdf = {}
    for l in fila:
        if regras.extensao(l['url']) == 'pdf':
            pdf.setdefault(mesmo_formulario(l), l)
    gemeas = {id(l): [] for l in pdf.values()}
    for l in fila:
        alvo = pdf.get(mesmo_formulario(l))
        if alvo and regras.extensao(l['url']) in ('doc', 'docx'):
            gemeas[id(alvo)].append(l['url'])
    return [{**l, 'duplicatas': gemeas[id(l)]} if gemeas.get(id(l)) else l for l in fila
            if not (regras.extensao(l['url']) in ('doc', 'docx') and mesmo_formulario(l) in pdf)]


def rota(linha: dict) -> tuple[str | None, str]:
    """('pdf' | 'gdoc', '') ou (None, por que não converte)."""
    if federal.no_espelho(linha):
        return None, 'lei federal: uma linha com o link do espelho ctresb/leis, à mão'
    ext = regras.extensao(linha['url'])
    return (ROTA[ext], '') if ext in ROTA else (None, f'.{ext}: sem rota automática')


def pasta_do(linha: dict, usados: set[str], existentes: dict[str, str] | None = None) -> str:
    """No --refazer, quem já tem pasta fica com ela (`existentes`); o ato federal, pelo número e ano; senão, o nome do padrão do acervo."""
    if ja := (existentes or {}).get(verificar.chave(linha['url'])):
        return ja
    if (ato := federal.nome(linha)) and ato not in usados:
        usados.add(ato)
        return ato
    return nomes.nome_da_pasta(linha, usados)


def descricao(linha: dict) -> str:
    """`Nome: resto`, como verificar.py exige: o nome é o título até 40 caracteres, o resto diz de onde veio."""
    titulo = ' '.join(linha['titulo'].replace(':', ' -').split()) or 'Documento'
    nome = titulo if len(titulo) <= NOME_MAX else titulo[:NOME_MAX].rsplit(' ', 1)[0]
    arquivo = Path(regras.arquivo(linha['url'])).stem.replace('_', ' ')
    resto = titulo if nome != titulo else ' '.join(arquivo.replace(':', ' -').split())
    return f'{nome}: {resto} ({linha["setores"].split(",")[0]}).'


def core_run() -> Path:
    """O `core/run` do workspace que contém este repo."""
    for pai in RAIZ.parents:
        if (pai / 'core' / 'run').is_file():
            return pai / 'core' / 'run'
    raise SystemExit('converter.py só roda dentro do workspace do mantenedor (não achei core/run).')


def rodar(*args: str, tempo: int = TEMPO) -> str:
    r = subprocess.run([str(core_run()), *args], capture_output=True, text=True, timeout=tempo)
    if r.returncode:
        raise OSError((r.stderr or r.stdout).strip().splitlines()[-1:] or ['falhou'])
    return r.stdout


def por_pdf(original: Path, linha: dict, desc: str, refazer: bool = False, tempo: int = TEMPO) -> None:
    rodar('tools/pdf/pymupdf', str(original), '--origin', linha['url'], '--description', desc, '--relevance', str(FIGURAS),
          *(['--force'] if refazer else []), tempo=tempo)


def por_gdoc(original: Path, linha: dict, desc: str, dados: bytes, destino: Path) -> None:
    subiu = rodar('tools/files/gdrive', 'put', '--gdoc', '--name', f'tmp-docs-ufrpe-{original.stem}', str(original))
    doc = re.search(r'id:(\S+)', subiu)
    if not doc:
        raise OSError('o Drive não devolveu o id')
    try:
        corpo = rodar('tools/docs/gdocs', 'read', doc.group(1))
    finally:
        rodar('tools/files/gdrive', 'rm', doc.group(1))
    destino.parent.mkdir(parents=True, exist_ok=True)
    destino.write_text(verificar.frontmatter({
        'description': desc, 'source': f'../{original.name}', 'origin': linha['url'], 'origin_checked': datetime.date.today().isoformat(),
        'sha256': hashlib.sha256(dados).hexdigest(), 'engine': MOTOR_GDOC}) + limpeza.sem_imagens(corpo).strip() + '\n', encoding='utf-8')


def converter(linha: dict, caminho: str, nome: str, docs: list[tuple[Path, dict]], refazer: bool = False,
              tempo: int = TEMPO, apesar_do_nome: bool = False) -> tuple[str, Path]:
    """Baixa e, se o acervo ainda não tem o arquivo, guarda o original ao lado e converte. ('copia', .md que já existe e
    ganhou a nota) ou ('ok', .md novo, que entra em `docs`). O mesmo ato noutro arquivo levanta MesmoAto, salvo `apesar_do_nome`."""
    dados = rede.baixar(linha['url'])
    if (achado := duplicatas.no_acervo(linha, dados, docs)) and achado[0] == 'copia':
        duplicatas.copia(RAIZ / achado[1], linha['url'])
        return 'copia', RAIZ / achado[1]
    if achado and not apesar_do_nome:
        raise duplicatas.MesmoAto(f'mesmo ato que {achado[1].parent}, noutro arquivo: dobre à mão ou rode --apesar-do-nome')
    pasta = RAIZ / federal.pasta(linha, PASTA)
    original, destino = pasta / f'{nome}.{regras.extensao(linha["url"])}', pasta / nome / f'{nome}.md'
    original.write_bytes(dados)
    if caminho == 'pdf':
        por_pdf(original, linha, descricao(linha), refazer, tempo)
    else:
        por_gdoc(original, linha, descricao(linha), dados, destino)
    if not limpeza.arquivo(destino).strip():
        destino.unlink()
        raise OSError('o motor devolveu o corpo vazio')
    if linha.get('duplicatas'):
        duplicatas.gemeos(destino, linha['duplicatas'])
    if linha['motivo'] == 'federal':
        federal.anotar(destino, linha['setores'].split(',')[0])
    docs.append((destino.relative_to(RAIZ), verificar.cabecalho(destino.read_text(encoding='utf-8')) or {}))
    return 'ok', destino


def gravar_fila(pendentes: list[tuple[str, str]], resolvidos: set[str]) -> None:
    """Reescreve a fila: sai o que esta rodada tentou ou o acervo já tem, entra o que ficou pendente; o resto fica."""
    antigas = [l.split('\t', 1) for l in FILA.read_text(encoding='utf-8').splitlines() if '\t' in l] if FILA.exists() else []
    linhas = dict((u, m) for u, m in antigas if verificar.chave(u) not in resolvidos)
    linhas.update(pendentes)
    FILA.parent.mkdir(exist_ok=True)
    FILA.write_text(''.join(f'{u}\t{m}\n' for u, m in linhas.items()), encoding='utf-8')


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('--setor', required=True)
    ap.add_argument('--tipo', choices=sorted(PASTA))
    ap.add_argument('--limite', type=int)
    ap.add_argument('--seco', action='store_true')
    ap.add_argument('--refazer', action='store_true', help='converte de novo o que já tem documento, na mesma pasta, menos o que tem reviewed_by')
    ap.add_argument('--tempo', type=int, default=TEMPO, help='segundos por PDF antes de desistir')
    ap.add_argument('--apesar-do-nome', action='store_true', help='converte o que tem o nome de um ato do acervo e outro arquivo (já revisado à mão)')
    ap.add_argument('--federal', action='store_true', help='só os atos federais que o setor hospeda')
    args = ap.parse_args(argv)
    sys.stdout.reconfigure(line_buffering=True)  # o lote leva horas: o log tem de andar junto
    fila = faltantes(verificar.ler_tsv(verificar.CENSO), args.setor, args.tipo, ja_feitos(args.refazer))
    fila = [l for l in fila if l['motivo'] == 'federal' or not args.federal][:args.limite]
    usados = {p.name for d in (*PASTA.values(), federal.FEDERAIS) for p in (RAIZ / d).iterdir() if p.is_dir()}
    existentes = pastas_existentes() if args.refazer else None
    pendentes, feitos, docs = [], 0, cabecalhos()
    for linha in fila:
        caminho, porque = rota(linha)
        nome = pasta_do(linha, usados, existentes)
        if caminho is None:
            pendentes.append((linha['url'], porque))
            continue
        print(f'{caminho:4}  {federal.pasta(linha, PASTA)}/{nome}')
        for u in linha.get('duplicatas', []):
            print(f'      duplicata: {u}')
        if args.seco:
            continue
        try:
            como, destino = converter(linha, caminho, nome, docs, args.refazer, args.tempo, args.apesar_do_nome)
            print(f'      {como} {destino.relative_to(RAIZ)}')
            feitos += como == 'ok'
        except duplicatas.MesmoAto as e:
            pendentes.append((linha['url'], str(e)))
            print(f'      REVISAR {e}')
        except (OSError, subprocess.TimeoutExpired) as e:
            pendentes.append((linha['url'], f'falhou: {e}'))
            print(f'      FALHOU {e}')
    if not args.seco:
        gravar_fila(pendentes, {verificar.chave(l['url']) for l in fila} | verificar.convertidos())
    for u, m in pendentes:
        print(f'fila  {m}  {u}')
    print(f'\n{len(fila)} na fila · {feitos} convertidos · {len(pendentes)} para o mantenedor')
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
