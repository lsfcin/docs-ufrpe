# test_duplicatas.py — o que duplicatas.py promete: a cópia byte a byte vira nota no documento que já existe, o mesmo ato noutro arquivo vai para a revisão, e a nota passa no verificar.py.
"""Uso: python -m unittest discover .github/scripts. Só stdlib, sem rede e sem o workspace."""
from __future__ import annotations

import hashlib
import tempfile
import unittest
from pathlib import Path

import duplicatas
import verificar

PDF = 'https://prpg.ufrpe.br/files/reconsu_294_2008_0.pdf'
COPIA = 'https://preg.ufrpe.br/files/Resolu%C3%A7%C3%A3o%20294_2008.pdf'
DADOS = b'%PDF-1.4 res 294'


def cabeca(**extra) -> dict:
    return {'description': 'Res. CONSU 294/2008: consulta (PRPG).', 'origin': PDF, 'origin_checked': '2026-11-23',
            **extra, 'sha256': hashlib.sha256(DADOS).hexdigest()}


def linha(url=COPIA, titulo='Resolução 294/2008 consulta para escolha'):
    return {'url': url, 'titulo': titulo, 'setores': 'PREG'}


ACERVO = [(Path('normas/res-consu-294-2008/res-consu-294-2008.md'), cabeca())]


class NoAcervo(unittest.TestCase):
    def test_mesmo_arquivo_e_copia_do_documento_que_ja_existe(self):
        self.assertEqual(duplicatas.no_acervo(linha(), DADOS, ACERVO), ('copia', ACERVO[0][0]))

    def test_mesmo_ato_com_outro_arquivo_vai_para_revisao(self):
        self.assertEqual(duplicatas.no_acervo(linha(), b'outro', ACERVO), ('ato', ACERVO[0][0]))

    def test_no_refazer_o_documento_nao_e_copia_dele_mesmo(self):
        self.assertIsNone(duplicatas.no_acervo(linha(url=PDF, titulo='Resolução CONSU 294/2008'), DADOS, ACERVO))

    def test_orgao_ausente_num_lado_ainda_e_o_mesmo_ato(self):
        semorgao = [(Path('normas/res-029-2020/res-029-2020.md'), {})]
        self.assertEqual(duplicatas.no_acervo(linha(titulo='Resolução CONSU 029/2020'), b'x', semorgao)[0], 'ato')

    def test_orgao_diferente_ou_numero_diferente_e_outro_ato(self):
        self.assertIsNone(duplicatas.no_acervo(linha(titulo='Resolução CEPE 294/2008'), b'x', ACERVO))
        self.assertIsNone(duplicatas.no_acervo(linha(titulo='Resolução 295/2008'), b'x', ACERVO))
        self.assertIsNone(duplicatas.no_acervo(linha(url='https://x/manual.pdf', titulo='Manual do SIGA'), b'x', ACERVO))


class Nota(unittest.TestCase):
    def escrever(self, pasta: str, **extra) -> Path:
        md = Path(pasta) / 'a.md'
        md.write_text(verificar.frontmatter(cabeca(**extra)) + 'corpo\n', encoding='utf-8')
        return md

    def test_sem_nota_entra_depois_do_origin_checked_e_passa_no_verificar(self):
        with tempfile.TemporaryDirectory() as tmp:
            md = self.escrever(tmp)
            duplicatas.copia(md, COPIA)
            campos = verificar.cabecalho(md.read_text(encoding='utf-8'))
        self.assertEqual(list(campos), ['description', 'origin', 'origin_checked', 'origin_note', 'sha256'])
        self.assertEqual(campos['origin_note'], f'o mesmo arquivo circula também em: {COPIA}')
        self.assertIn(verificar.chave(COPIA), verificar.origens(campos))

    def test_com_nota_a_frase_nova_vem_depois_da_antiga(self):
        with tempfile.TemporaryDirectory() as tmp:
            md = self.escrever(tmp, origin_note='publicação original no DOU.')
            duplicatas.copia(md, COPIA)
            nota = verificar.cabecalho(md.read_text(encoding='utf-8'))['origin_note']
        self.assertEqual(nota, f'publicação original no DOU; o mesmo arquivo circula também em: {COPIA}')

    def test_gemeo_docx_do_mesmo_formulario(self):
        with tempfile.TemporaryDirectory() as tmp:
            md = self.escrever(tmp)
            duplicatas.gemeos(md, ['https://x/a.docx', 'https://x/a.doc'])
            nota = verificar.cabecalho(md.read_text(encoding='utf-8'))['origin_note']
        self.assertEqual(nota, 'o mesmo formulário circula também em DOCX/DOC: https://x/a.docx, https://x/a.doc')


if __name__ == '__main__':
    unittest.main()
