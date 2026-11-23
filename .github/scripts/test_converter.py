# test_converter.py — o que o conversor do docs-ufrpe promete: só converte o `entra` que falta, cada formato pela sua rota, e o cabeçalho que ele grava passa no verificar.py.
"""Uso: python -m unittest discover .github/scripts. Só stdlib, sem rede e sem o workspace."""
from __future__ import annotations

import datetime
import unittest
from pathlib import Path

import converter
import verificar


def linha(url='https://prpg.ufrpe.br/files/RECEPE989.2026%20APROVA%20NORMAS%20POS-DOUTORADO.pdf', titulo='Resolução 989/2026',
          tipo='norma', motivo='norma', decisao='entra', setores='PRPG'):
    return {'url': url, 'setores': setores, 'tipo': tipo, 'decisao': decisao, 'motivo': motivo, 'titulo': titulo, 'data': '2026-11-23'}


class Fila(unittest.TestCase):
    def test_so_o_entra_do_setor_que_ainda_nao_tem_documento(self):
        feito = linha(url='https://x/feito%20j%C3%A1.pdf')
        linhas = [linha(), feito, linha(decisao='fora'), linha(setores='PREG,PRPG'), linha(tipo='modelo')]
        sobra = converter.faltantes(linhas, 'PRPG', 'norma', {converter.chave('https://x/feito já.pdf')})
        self.assertEqual(sobra, [linhas[0]])

    def test_cada_formato_pela_sua_rota(self):
        self.assertEqual(converter.rota(linha()), ('pdf', ''))
        self.assertEqual(converter.rota(linha(url='https://x/a.DOCX'))[0], 'gdoc')
        self.assertEqual(converter.rota(linha(url='https://x/a.doc'))[0], 'gdoc')
        self.assertIsNone(converter.rota(linha(url='https://x/a.xls'))[0])
        self.assertIsNone(converter.rota(linha(motivo='federal'))[0])


class Nomes(unittest.TestCase):
    def test_titulo_curto_ganha_o_nome_do_arquivo_e_nunca_repete(self):
        usados = set()
        primeiro = converter.nome_da_pasta(linha(), usados)
        self.assertEqual(primeiro, 'res-cepe-989-2026-normas-pos-doutorado')
        self.assertEqual(converter.nome_da_pasta(linha(), usados), primeiro + '-2')
        self.assertTrue(verificar.NOME.match(primeiro))
        self.assertLessEqual(len(primeiro), converter.PASTA_MAX)

    def test_ato_numerado_no_padrao_do_acervo(self):
        self.assertEqual(converter.ato('Resolução CEPE/UFRPE Nº 926, de 19 de agosto de 2025'), ['res', 'cepe', '926', '2025'])
        self.assertEqual(converter.ato('Instrução Normativa UFRPE/PRPG Nº 01/2026'), ['in', 'prpg', '01', '2026'])
        self.assertEqual(converter.ato('reconsu_294_2008_0'), ['res', 'consu', '294', '2008'])
        self.assertEqual(converter.ato('recu104.2021_homologao_res._230.21_cepe'), ['res', 'consu', '104', '2021'])
        self.assertEqual(converter.ato('Manual PROAP 2023'), [])

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
