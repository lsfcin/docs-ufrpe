# test_converter.py — o que o conversor do docs-ufrpe promete: só converte o `entra` que falta, cada formato pela sua rota, e o cabeçalho que ele grava passa no verificar.py.
"""Uso: python -m unittest discover .github/scripts. Só stdlib, sem rede e sem o workspace."""
from __future__ import annotations

import datetime
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import converter
import nomes
import verificar


def linha(url='https://prpg.ufrpe.br/files/RECEPE989.2026%20APROVA%20NORMAS%20POS-DOUTORADO.pdf', titulo='Resolução 989/2026',
          tipo='norma', motivo='norma', decisao='entra', setores='PRPG'):
    return {'url': url, 'setores': setores, 'tipo': tipo, 'decisao': decisao, 'motivo': motivo, 'titulo': titulo, 'data': '2026-11-23'}


class Fila(unittest.TestCase):
    def test_so_o_entra_do_setor_que_ainda_nao_tem_documento(self):
        feito = linha(url='https://x/feito%20j%C3%A1.pdf')
        linhas = [linha(), feito, linha(decisao='fora'), linha(setores='PREG,PRPG'), linha(tipo='modelo')]
        sobra = converter.faltantes(linhas, 'PRPG', 'norma', {verificar.chave('https://x/feito já.pdf')})
        self.assertEqual(sobra, [linhas[0]])

    def test_o_pdf_vai_com_o_perfil_de_figuras_do_acervo(self):
        with mock.patch.object(converter, 'rodar') as rodar:
            converter.por_pdf(Path('a.pdf'), linha(), 'desc')
        args = rodar.call_args.args
        self.assertEqual(args[args.index('--relevance') + 1], str(converter.FIGURAS))
        self.assertTrue((converter.FIGURAS / 'relevance.tsv').exists())

    def test_cada_formato_pela_sua_rota(self):
        self.assertEqual(converter.rota(linha()), ('pdf', ''))
        self.assertEqual(converter.rota(linha(url='https://x/a.DOCX'))[0], 'gdoc')
        self.assertEqual(converter.rota(linha(url='https://x/a.doc'))[0], 'gdoc')
        self.assertIsNone(converter.rota(linha(url='https://x/a.xls'))[0])
        self.assertIsNone(converter.rota(linha(motivo='federal'))[0])

    def test_fila_reescrita_sem_repetir_nem_guardar_o_resolvido(self):
        with tempfile.TemporaryDirectory() as tmp:
            fila = Path(tmp) / 'fila.tsv'
            fila.write_text('http://x/feito.pdf\tfalhou: ssl\nhttps://x/outro.pdf\tfalhou\nhttps://x/a.xls\t.xls\n', encoding='utf-8')
            with mock.patch.object(converter, 'FILA', fila):
                converter.gravar_fila([('https://x/a.xls', '.xls')], {verificar.chave('https://x/feito.pdf'), 'https://x/a.xls'})
            self.assertEqual(fila.read_text(encoding='utf-8'), 'https://x/outro.pdf\tfalhou\nhttps://x/a.xls\t.xls\n')


PDF_DS = 'https://prpg.ufrpe.br/sites/default/files/formularios/TermodeCompromissoDS-DeclaraodeAcmulos.pdf'
DOCX_DS = 'https://prpg.ufrpe.br/sites/default/files/formularios/TermodeCompromissoDS.docx'


class Duplicatas(unittest.TestCase):
    def test_pdf_e_docx_do_mesmo_formulario_viram_um_so_com_o_link_do_docx(self):
        pdf = linha(url=PDF_DS, titulo='TERMO DE COMPROMISSO - DS', tipo='modelo')
        docx = linha(url=DOCX_DS, titulo='TERMO DE COMPROMISSO - DS (WORD)', tipo='modelo')
        outro = linha(titulo='Resolução 989/2026')
        sobra = converter.faltantes([docx, outro, pdf], 'PRPG', None, set())
        self.assertEqual(sobra, [outro, {**pdf, 'duplicatas': [DOCX_DS]}])

    def test_dois_docx_ou_tipos_diferentes_ficam_como_estao(self):
        a = linha(url='https://x/a.docx', titulo='Termo (WORD)', tipo='modelo')
        b = linha(url='https://x/b.docx', titulo='Termo DOCX', tipo='modelo')
        c = linha(url='https://x/c.pdf', titulo='Termo', tipo='norma')
        self.assertEqual(converter.faltantes([a, b, c], 'PRPG', None, set()), [a, b, c])

    def test_nota_do_origin_entra_depois_do_origin_checked_e_passa_no_verificar(self):
        with tempfile.TemporaryDirectory() as tmp:
            md = Path(tmp) / 'a.md'
            md.write_text(converter.frontmatter({'description': 'A: b (PRPG).', 'origin': PDF_DS, 'origin_checked': '2026-11-23',
                                                 'sha256': '0' * 64}) + 'corpo\n', encoding='utf-8')
            converter.anotar(md, [DOCX_DS])
            campos = verificar.cabecalho(md.read_text(encoding='utf-8'))
        self.assertEqual(list(campos), ['description', 'origin', 'origin_checked', 'origin_note', 'sha256'])
        self.assertIn(DOCX_DS, campos['origin_note'])

    def test_convertidos_ve_a_url_dentro_do_origin_note(self):
        with tempfile.TemporaryDirectory() as tmp:
            raiz = Path(tmp)
            (raiz / 'modelos' / 'a').mkdir(parents=True)
            (raiz / 'modelos' / 'a' / 'a.md').write_text(converter.frontmatter({
                'description': 'A: b (PRPG).', 'origin': PDF_DS, 'origin_checked': '2026-11-23',
                'origin_note': f'o mesmo formulário circula também em DOCX: {DOCX_DS.replace("Termo", "Termo%20")}, https://x/b.doc.',
                'sha256': '0' * 64}) + 'corpo\n', encoding='utf-8')
            with mock.patch.object(converter, 'RAIZ', raiz), mock.patch.object(verificar, 'RAIZ', raiz):
                feitos = verificar.convertidos()
        self.assertEqual(feitos, {PDF_DS, DOCX_DS.replace('Termo', 'Termo '), 'https://x/b.doc'})

    def test_refazer_pula_o_documento_corrigido_a_mao(self):
        """`reviewed_by` preenchido protege o documento e o gêmeo do origin_note; `null` não protege."""
        with tempfile.TemporaryDirectory() as tmp:
            raiz = Path(tmp)
            for nome, origem, revisor in (('a', PDF_DS, 'claude 2026-11-24'), ('b', 'https://x/b.pdf', None)):
                (raiz / 'normas' / nome).mkdir(parents=True)
                (raiz / 'normas' / nome / f'{nome}.md').write_text(converter.frontmatter({
                    'description': f'{nome.upper()}: c (PRPG).', 'origin': origem, 'origin_checked': '2026-11-23',
                    'origin_note': 'o mesmo formulário circula também em DOC: https://x/a.doc' if nome == 'a' else '',
                    'sha256': '0' * 64, 'reviewed_by': revisor}) + 'corpo\n', encoding='utf-8')
            with mock.patch.object(converter, 'RAIZ', raiz), mock.patch.object(verificar, 'RAIZ', raiz):
                self.assertEqual(converter.ja_feitos(refazer=True), {PDF_DS, 'https://x/a.doc'})
                self.assertEqual(converter.ja_feitos(refazer=False), {PDF_DS, 'https://x/a.doc', 'https://x/b.pdf'})


class Nomes(unittest.TestCase):
    def test_titulo_curto_ganha_o_nome_do_arquivo_e_nunca_repete(self):
        usados = set()
        primeiro = nomes.nome_da_pasta(linha(), usados)
        self.assertEqual(primeiro, 'res-cepe-989-2026-normas-pos-doutorado')
        self.assertEqual(nomes.nome_da_pasta(linha(), usados), primeiro + '-2')
        self.assertTrue(verificar.NOME.match(primeiro))
        self.assertLessEqual(len(primeiro), nomes.PASTA_MAX)

    def test_palavra_longa_do_titulo_fica_e_o_nome_colado_do_arquivo_sai(self):
        plano = linha(url='https://x/Plano%20Internacionaliza%C3%A7%C3%A3o%202025%20-%202030%20da%20UFRPE.pdf',
                      titulo='Plano de Internacionalização 2025-2030')
        self.assertEqual(nomes.nome_da_pasta(plano, set()), 'plano-internacionalizacao')
        colado = linha(url='https://x/TermodeCompromissoDS.pdf', titulo='TERMO DE COMPROMISSO - DS')
        self.assertEqual(nomes.nome_da_pasta(colado, set()), 'termo-compromisso-ds')

    def test_refazer_reaproveita_a_pasta_que_o_documento_ja_tem(self):
        usados = {'res-cepe-989-2026-normas-pos-doutorado'}
        existentes = {verificar.chave(linha()['url']): 'res-cepe-989-2026-normas-pos-doutorado'}
        self.assertEqual(converter.pasta_do(linha(), usados, existentes), 'res-cepe-989-2026-normas-pos-doutorado')
        novo = linha(url='https://x/res-cepe-989-2026-normas-pos-doutorado.pdf')
        self.assertEqual(converter.pasta_do(novo, usados, existentes), 'res-cepe-989-2026-normas-pos-doutorado-2')

    def test_ato_numerado_no_padrao_do_acervo(self):
        self.assertEqual(nomes.ato('Resolução CEPE/UFRPE Nº 926, de 19 de agosto de 2025'), ['res', 'cepe', '926', '2025'])
        self.assertEqual(nomes.ato('Instrução Normativa UFRPE/PRPG Nº 01/2026'), ['in', 'prpg', '01', '2026'])
        self.assertEqual(nomes.ato('reconsu_294_2008_0'), ['res', 'consu', '294', '2008'])
        self.assertEqual(nomes.ato('recu104.2021_homologao_res._230.21_cepe'), ['res', 'consu', '104', '2021'])
        self.assertEqual(nomes.ato('Manual PROAP 2023'), [])

    def test_descricao_tem_o_rotulo_que_o_site_usa(self):
        for t in ('Resolução 989/2026', 'FORMULÁRIO PARA INSCRIÇÃO EM PROGRAMAS DE PÓS-GRADUAÇÃO ALUNO ESPECIAL', 'IN: 01/2026'):
            self.assertRegex(converter.descricao(linha(titulo=t)), verificar.ROTULO)


class Corpo(unittest.TestCase):
    def test_imagem_embutida_sai_e_o_texto_fica(self):
        corpo = '![][image1]\n\n# ANEXO I\n\n| A | B |\n\n[image1]: <data:image/png;base64,iVBORw0KGgo>\n'
        self.assertEqual(converter.sem_imagens(corpo).strip(), '# ANEXO I\n\n| A | B |')


class Cabecalho(unittest.TestCase):
    def test_o_que_o_conversor_grava_passa_no_verificar(self):
        texto = converter.frontmatter({'description': converter.descricao(linha()), 'origin': linha()['url'],
                                       'origin_checked': '2026-11-23', 'sha256': '0' * 64, 'engine': converter.MOTOR_GDOC}) + 'corpo\n'
        erros, _, campos = verificar.conferir(Path('modelos/a/a.md'), texto, datetime.date(2026, 11, 23))
        self.assertEqual(erros, [])
        self.assertEqual(campos['origin'], linha()['url'])


if __name__ == '__main__':
    unittest.main()
