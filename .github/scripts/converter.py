# converter.py — o lote do docs-ufrpe: cada link `entra` do censo que ainda não tem .md vira documento, pelos motores do workspace.
"""Uso: python .github/scripts/converter.py --setor PRPG [--tipo norma] [--limite N] [--seco]

Só roda no workspace do mantenedor, porque chama três ferramentas dele por `core/run`: o PDF vai por
`tools/pdf/pymupdf`, e o DOC e o DOCX sobem ao Drive como Google Doc temporário e voltam por `tools/docs/gdocs
read`, o que mantém as tabelas em Markdown puro. O original fica ao lado da pasta e não entra no git.
Não convertem: federal (regra do espelho ctresb/leis), planilha e o que falhar. Esses vão para
.vigia/fila.tsv com o motivo. --seco só lista o que faria.
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

import rede
import regras
import verificar
import vigiar

RAIZ = verificar.RAIZ
FILA = RAIZ / '.vigia' / 'fila.tsv'
PASTA = {'modelo': 'modelos', 'norma': 'normas', 'orientacao': 'orientacoes', 'tabela': 'tabelas'}
ROTA = {'pdf': 'pdf', 'doc': 'gdoc', 'docx': 'gdoc'}
NOME_MAX, PASTA_MAX = 40, 60
ORGAOS = (('cepe', r'\bcepe\b|\brecepe'), ('consu', r'\bconsu\b|\brecu|\breconsu'), ('cura', r'\bcura\b'), ('prpg', r'\bprpg\b'),
          ('preg', r'\bpreg\b'), ('progepe', r'\bprogepe\b'), ('progesti', r'\bprogesti\b'))
# Palavras que não dizem o assunto: artigos, o tipo do ato, o órgão, meses, sobras do nome de arquivo.
VAZIAS = set('''a o as os e de da do das dos du no na nos nas n em para por com que ao aos sobre pela pelo pdf doc docx word
ufrpe ufrpe resolucao resolucoes res instrucao normativa in cepe consu cura prpg preg progepe progesti aprova altera
janeiro fevereiro marco abril maio junho julho agosto setembro outubro novembro dezembro assinado final atualizado
correto corrigido versao v copia anexo modelo arquivo recepe recu reconsu'''.split())
COLADA = 16  # uma "palavra" maior que isto é nome de arquivo sem espaço (termodecompromissods)
MOTOR_GDOC = 'Google Docs import + export (gdocs read)'


def chave(url: str) -> str:
    """O mesmo arquivo, a mesma chave, codificado ou não."""
    return urllib.parse.unquote(url).strip()


def convertidos() -> set[str]:
    """As origens que já têm documento no acervo."""
    feitos = set()
    for rel in verificar.documentos([]):
        campos = verificar.cabecalho((RAIZ / rel).read_text(encoding='utf-8')) or {}
        if isinstance(campos.get('origin'), str):
            feitos.add(chave(campos['origin']))
    return feitos


def faltantes(linhas: list[dict], setor: str, tipo: str | None, feitos: set[str]) -> list[dict]:
    """Os `entra` do setor (o primeiro da coluna setores, como na tabela do README) sem documento."""
    return [l for l in linhas if l['decisao'] == 'entra' and l['setores'].split(',')[0] == setor
            and (tipo is None or l['tipo'] == tipo) and chave(l['url']) not in feitos]


def extensao(url: str) -> str:
    return Path(urllib.parse.urlsplit(url).path).suffix.lower().lstrip('.')


def rota(linha: dict) -> tuple[str | None, str]:
    """('pdf' | 'gdoc', '') ou (None, por que não converte)."""
    if linha['motivo'] == 'federal':
        return None, 'federal: aponta para o espelho ctresb/leis, à mão'
    ext = extensao(linha['url'])
    return (ROTA[ext], '') if ext in ROTA else (None, f'.{ext}: sem rota automática')


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


def nome_da_pasta(linha: dict, usados: set[str]) -> str:
    """No padrão do acervo: o ato (`res-cepe-989-2026`) e até quatro palavras de assunto, do título e do nome do arquivo."""
    arquivo = urllib.parse.unquote(Path(urllib.parse.urlsplit(linha['url']).path).stem)
    texto = f'{linha["titulo"]} {arquivo}'
    cabeca = ato(texto)
    assunto = [p for p in dict.fromkeys(palavras(texto)) if p not in VAZIAS and not re.search(r'\d', p) and p not in cabeca and len(p) <= COLADA]
    partes = cabeca + assunto[:4 if cabeca else 8]
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


def descricao(linha: dict) -> str:
    """`Nome: resto`, como verificar.py exige: o nome é o título até 40 caracteres, o resto diz de onde veio."""
    titulo = ' '.join(linha['titulo'].replace(':', ' -').split()) or 'Documento'
    nome = titulo if len(titulo) <= NOME_MAX else titulo[:NOME_MAX].rsplit(' ', 1)[0]
    arquivo = urllib.parse.unquote(Path(urllib.parse.urlsplit(linha['url']).path).stem).replace('_', ' ')
    resto = titulo if nome != titulo else ' '.join(arquivo.replace(':', ' -').split())
    return f'{nome}: {resto} ({linha["setores"].split(",")[0]}).'


def frontmatter(campos: dict) -> str:
    return '---\n' + ''.join(f'{k}: {json.dumps(v, ensure_ascii=False)}\n' for k, v in campos.items()) + '---\n\n'


def core_run() -> Path:
    """O `core/run` do workspace que contém este repo."""
    for pai in RAIZ.parents:
        if (pai / 'core' / 'run').is_file():
            return pai / 'core' / 'run'
    raise SystemExit('converter.py só roda dentro do workspace do mantenedor (não achei core/run).')


def rodar(*args: str) -> str:
    r = subprocess.run([str(core_run()), *args], capture_output=True, text=True, timeout=900)
    if r.returncode:
        raise OSError((r.stderr or r.stdout).strip().splitlines()[-1:] or ['falhou'])
    return r.stdout


def por_pdf(original: Path, linha: dict, desc: str) -> None:
    rodar('tools/pdf/pymupdf', str(original), '--origin', linha['url'], '--description', desc)


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


def converter(linha: dict, caminho: str, nome: str) -> Path:
    """Baixa, guarda o original ao lado e converte; devolve o .md."""
    pasta = RAIZ / PASTA[linha['tipo']]
    original = pasta / f'{nome}.{extensao(linha["url"])}'
    destino = pasta / nome / f'{nome}.md'
    dados = rede.baixar(linha['url'])
    original.write_bytes(dados)
    desc = descricao(linha)
    if caminho == 'pdf':
        por_pdf(original, linha, desc)
    else:
        por_gdoc(original, linha, desc, dados, destino)
    return destino


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('--setor', required=True)
    ap.add_argument('--tipo', choices=sorted(PASTA))
    ap.add_argument('--limite', type=int)
    ap.add_argument('--seco', action='store_true')
    args = ap.parse_args(argv)
    sys.stdout.reconfigure(line_buffering=True)  # o lote leva horas: o log tem de andar junto
    fila = faltantes(vigiar.ler_tsv(vigiar.CENSO), args.setor, args.tipo, convertidos())[:args.limite]
    usados = {p.name for d in PASTA.values() for p in (RAIZ / d).iterdir() if p.is_dir()}
    pendentes, feitos = [], 0
    for linha in fila:
        caminho, porque = rota(linha)
        nome = nome_da_pasta(linha, usados)
        if caminho is None:
            pendentes.append((linha['url'], porque))
            continue
        print(f'{caminho:4}  {PASTA[linha["tipo"]]}/{nome}')
        if args.seco:
            continue
        try:
            print(f'      ok {converter(linha, caminho, nome).relative_to(RAIZ)}')
            feitos += 1
        except (OSError, subprocess.TimeoutExpired) as e:
            pendentes.append((linha['url'], f'falhou: {e}'))
            print(f'      FALHOU {e}')
    if pendentes and not args.seco:
        FILA.parent.mkdir(exist_ok=True)
        with FILA.open('a', encoding='utf-8') as f:
            f.writelines(f'{u}\t{m}\n' for u, m in pendentes)
    for u, m in pendentes:
        print(f'fila  {m}  {u}')
    print(f'\n{len(fila)} na fila · {feitos} convertidos · {len(pendentes)} para o mantenedor')
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
