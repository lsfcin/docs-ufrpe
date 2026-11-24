# converter.py — o lote do docs-ufrpe: cada link `entra` do censo que ainda não tem .md vira documento, pelos motores do workspace.
"""Uso: python .github/scripts/converter.py --setor PRPG [--tipo norma] [--limite N] [--seco] [--refazer]

Só roda no workspace do mantenedor, porque chama três ferramentas dele por `core/run`: o PDF vai por
`tools/pdf/pymupdf`, e o DOC e o DOCX sobem ao Drive como Google Doc temporário e voltam por `tools/docs/gdocs
read`, o que mantém as tabelas em Markdown puro. O original fica ao lado da pasta e não entra no git.
Não convertem: federal (regra do espelho ctresb/leis), planilha e o que falhar. Esses vão para
.vigia/fila.tsv com o motivo. --seco só lista o que faria. --refazer converte de novo o que já tem documento
(cada um na pasta que já tem, e o motor sobrescreve). O mesmo formulário em PDF e em DOC/DOCX vira um documento só,
o do PDF, e o link do DOC/DOCX vai no `origin_note`.
"""
from __future__ import annotations

import argparse
import datetime
import hashlib
import json
import re
import subprocess
import sys
import urllib.parse
from pathlib import Path

import nomes
import rede
import regras
import verificar
import vigiar

RAIZ = verificar.RAIZ
FILA = RAIZ / '.vigia' / 'fila.tsv'
PASTA = {'modelo': 'modelos', 'norma': 'normas', 'orientacao': 'orientacoes', 'tabela': 'tabelas'}
ROTA = {'pdf': 'pdf', 'doc': 'gdoc', 'docx': 'gdoc'}
NOME_MAX = 40
FORMATO = r'word|pdf|docx?'  # o que o título diz do formato, e não do formulário
MOTOR_GDOC = 'Google Docs import + export (gdocs read)'
TEMPO = 900  # segundos por chamada; um manual só de capturas de tela pede --tempo maior (cada figura vai ao modelo de visão)


def chave(url: str) -> str:
    """O mesmo arquivo, a mesma chave, codificado ou não, por http ou https (rede.baixar sobe um ao outro)."""
    return re.sub(r'^http://', 'https://', urllib.parse.unquote(url).strip())


URL_NA_NOTA = re.compile(r'http\S+')


def cabecalhos() -> list[tuple[Path, dict]]:
    """Cada documento do acervo com o seu frontmatter."""
    return [(rel, verificar.cabecalho((RAIZ / rel).read_text(encoding='utf-8')) or {}) for rel in verificar.documentos([])]


def convertidos() -> set[str]:
    """As origens que já têm documento no acervo, e as que o `origin_note` diz que são o mesmo documento."""
    feitos = set()
    for _, campos in cabecalhos():
        if isinstance(campos.get('origin'), str):
            feitos.add(chave(campos['origin']))
        if isinstance(campos.get('origin_note'), str):
            feitos.update(chave(u.rstrip('.,;:)"\'')) for u in URL_NA_NOTA.findall(campos['origin_note']))
    return feitos


def pastas_existentes() -> dict[str, str]:
    """{origem: pasta que o documento já tem}, para o --refazer não criar `-2`."""
    return {chave(c['origin']): rel.parent.name for rel, c in cabecalhos() if isinstance(c.get('origin'), str) and len(rel.parts) == 3}


def mesmo_formulario(linha: dict) -> tuple[str, str]:
    """(tipo, título sem a marca de formato): `TERMO - DS (WORD)` e `TERMO - DS` são o mesmo formulário."""
    t = regras.simples(linha['titulo'])
    t = re.sub(rf'\(\s*(?:{FORMATO})\s*\)', ' ', t)
    return linha['tipo'], ' '.join(re.sub(rf'\s(?:{FORMATO})$', '', ' '.join(t.split())).split())


def faltantes(linhas: list[dict], setor: str, tipo: str | None, feitos: set[str]) -> list[dict]:
    """Os `entra` do setor (o primeiro da coluna setores, como na tabela do README) sem documento. O DOC/DOCX do mesmo
    formulário que um PDF não é convertido: o link dele vai na `duplicatas` da linha do PDF."""
    fila = [l for l in linhas if l['decisao'] == 'entra' and l['setores'].split(',')[0] == setor
            and (tipo is None or l['tipo'] == tipo) and chave(l['url']) not in feitos]
    pdf = {}
    for l in fila:
        if extensao(l['url']) == 'pdf':
            pdf.setdefault(mesmo_formulario(l), l)
    gemeas = {id(l): [] for l in pdf.values()}
    for l in fila:
        alvo = pdf.get(mesmo_formulario(l))
        if alvo and extensao(l['url']) in ('doc', 'docx'):
            gemeas[id(alvo)].append(l['url'])
    return [{**l, 'duplicatas': gemeas[id(l)]} if gemeas.get(id(l)) else l for l in fila
            if not (extensao(l['url']) in ('doc', 'docx') and mesmo_formulario(l) in pdf)]


def extensao(url: str) -> str:
    return Path(urllib.parse.urlsplit(url).path).suffix.lower().lstrip('.')


def rota(linha: dict) -> tuple[str | None, str]:
    """('pdf' | 'gdoc', '') ou (None, por que não converte)."""
    if linha['motivo'] == 'federal':
        return None, 'federal: aponta para o espelho ctresb/leis, à mão'
    ext = extensao(linha['url'])
    return (ROTA[ext], '') if ext in ROTA else (None, f'.{ext}: sem rota automática')


def pasta_do(linha: dict, usados: set[str], existentes: dict[str, str] | None = None) -> str:
    """No --refazer, quem já tem pasta fica com ela (`existentes`); senão, o nome do padrão do acervo."""
    return (existentes or {}).get(chave(linha['url'])) or nomes.nome_da_pasta(linha, usados)


def descricao(linha: dict) -> str:
    """`Nome: resto`, como verificar.py exige: o nome é o título até 40 caracteres, o resto diz de onde veio."""
    titulo = ' '.join(linha['titulo'].replace(':', ' -').split()) or 'Documento'
    nome = titulo if len(titulo) <= NOME_MAX else titulo[:NOME_MAX].rsplit(' ', 1)[0]
    arquivo = urllib.parse.unquote(Path(urllib.parse.urlsplit(linha['url']).path).stem).replace('_', ' ')
    resto = titulo if nome != titulo else ' '.join(arquivo.replace(':', ' -').split())
    return f'{nome}: {resto} ({linha["setores"].split(",")[0]}).'


def campo(nome: str, valor: str) -> str:
    return f'{nome}: {json.dumps(valor, ensure_ascii=False)}\n'


def frontmatter(campos: dict) -> str:
    return '---\n' + ''.join(campo(k, v) for k, v in campos.items()) + '---\n\n'


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
    rodar('tools/pdf/pymupdf', str(original), '--origin', linha['url'], '--description', desc, *(['--force'] if refazer else []), tempo=tempo)


def anotar(destino: Path, duplicatas: list[str]) -> None:
    """Põe o `origin_note` logo depois do `origin_checked`, o que o motor de PDF não sabe escrever."""
    formatos = '/'.join(dict.fromkeys(extensao(u).upper() for u in duplicatas))
    nota = campo('origin_note', f'o mesmo formulário circula também em {formatos}: {", ".join(duplicatas)}')
    texto, n = re.subn(r'^origin_checked:.*\n', lambda m: m.group(0) + nota, destino.read_text(encoding='utf-8'), count=1, flags=re.M)
    if not n or not verificar.cabecalho(texto):
        raise OSError(f'sem origin_checked para anotar em {destino.name}')
    destino.write_text(texto, encoding='utf-8')


def sem_imagens(corpo: str) -> str:
    """Tira a imagem que o Google Docs embute em base64 (`[image1]: <data:…>` e o `![][image1]` que a usa): é brasão,
    não texto, e sozinha estoura o limite de tamanho do arquivo."""
    corpo = re.sub(r'^\[image\d+\]: <data:[^>]*>\s*$', '', corpo, flags=re.M)
    return re.sub(r'!\[[^\]]*\]\[image\d+\]', '', corpo)


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
    destino.write_text(frontmatter({
        'description': desc, 'origin': linha['url'], 'origin_checked': datetime.date.today().isoformat(),
        'sha256': hashlib.sha256(dados).hexdigest(), 'engine': MOTOR_GDOC}) + sem_imagens(corpo).strip() + '\n', encoding='utf-8')


def converter(linha: dict, caminho: str, nome: str, refazer: bool = False, tempo: int = TEMPO) -> Path:
    """Baixa, guarda o original ao lado e converte; devolve o .md."""
    pasta = RAIZ / PASTA[linha['tipo']]
    original = pasta / f'{nome}.{extensao(linha["url"])}'
    destino = pasta / nome / f'{nome}.md'
    dados = rede.baixar(linha['url'])
    original.write_bytes(dados)
    desc = descricao(linha)
    if caminho == 'pdf':
        por_pdf(original, linha, desc, refazer, tempo)
    else:
        por_gdoc(original, linha, desc, dados, destino)
    if linha.get('duplicatas'):
        anotar(destino, linha['duplicatas'])
    return destino


def gravar_fila(pendentes: list[tuple[str, str]], resolvidos: set[str]) -> None:
    """Reescreve a fila: sai o que esta rodada tentou ou o acervo já tem, entra o que ficou pendente; o resto fica."""
    antigas = [l.split('\t', 1) for l in FILA.read_text(encoding='utf-8').splitlines() if '\t' in l] if FILA.exists() else []
    linhas = dict((u, m) for u, m in antigas if chave(u) not in resolvidos)
    linhas.update(pendentes)
    FILA.parent.mkdir(exist_ok=True)
    FILA.write_text(''.join(f'{u}\t{m}\n' for u, m in linhas.items()), encoding='utf-8')


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('--setor', required=True)
    ap.add_argument('--tipo', choices=sorted(PASTA))
    ap.add_argument('--limite', type=int)
    ap.add_argument('--seco', action='store_true')
    ap.add_argument('--refazer', action='store_true', help='converte de novo o que já tem documento, na mesma pasta')
    ap.add_argument('--tempo', type=int, default=TEMPO, help='segundos por PDF antes de desistir')
    args = ap.parse_args(argv)
    sys.stdout.reconfigure(line_buffering=True)  # o lote leva horas: o log tem de andar junto
    fila = faltantes(vigiar.ler_tsv(vigiar.CENSO), args.setor, args.tipo, set() if args.refazer else convertidos())[:args.limite]
    usados = {p.name for d in PASTA.values() for p in (RAIZ / d).iterdir() if p.is_dir()}
    existentes = pastas_existentes() if args.refazer else None
    pendentes, feitos = [], 0
    for linha in fila:
        caminho, porque = rota(linha)
        nome = pasta_do(linha, usados, existentes)
        if caminho is None:
            pendentes.append((linha['url'], porque))
            continue
        print(f'{caminho:4}  {PASTA[linha["tipo"]]}/{nome}')
        for u in linha.get('duplicatas', []):
            print(f'      duplicata: {u}')
        if args.seco:
            continue
        try:
            print(f'      ok {converter(linha, caminho, nome, args.refazer, args.tempo).relative_to(RAIZ)}')
            feitos += 1
        except (OSError, subprocess.TimeoutExpired) as e:
            pendentes.append((linha['url'], f'falhou: {e}'))
            print(f'      FALHOU {e}')
    if not args.seco:
        gravar_fila(pendentes, {chave(l['url']) for l in fila} | convertidos())
    for u, m in pendentes:
        print(f'fila  {m}  {u}')
    print(f'\n{len(fila)} na fila · {feitos} convertidos · {len(pendentes)} para o mantenedor')
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
