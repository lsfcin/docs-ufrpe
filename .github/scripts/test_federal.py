# test_federal.py — o que federal.py promete: a lei fica no espelho, o resto do federal vai para a pasta certa, e a nota diz até onde o texto compilado vai.
"""Uso: python -m unittest discover .github/scripts. Só stdlib, sem rede e sem o workspace."""
from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import federal
import verificar


def linha(titulo='Decreto 1590', tipo='norma', motivo='federal'):
    return {'url': 'https://x/a.pdf', 'setores': 'PROGEPE', 'tipo': tipo, 'decisao': 'entra', 'motivo': motivo, 'titulo': titulo}


class Federal(unittest.TestCase):
    def test_so_a_lei_fica_no_espelho(self):
        self.assertTrue(federal.no_espelho(linha('LEI Nº 14.965, DE 9 DE SETEMBRO DE 2024')))
        self.assertFalse(federal.no_espelho(linha('DECRETO Nº 7.485, DE 18 DE MAIO DE 2011')))
        self.assertFalse(federal.no_espelho(linha('Lei interna', motivo='norma')))

    def test_nome_pelo_numero_e_ano(self):
        self.assertEqual(federal.nome(linha('DECRETO Nº 7.485, DE 18 DE MAIO DE 2011')), 'decreto-7485-2011')
        self.assertEqual(federal.nome(linha('Decreto 1.867-1996')), 'decreto-1867-1996')
        self.assertEqual(federal.nome(linha('Decreto 1590')), 'decreto-1590')
        self.assertEqual(federal.nome(linha('D12246 dispensa para a realização de exames')), 'decreto-12246')
        self.assertEqual(federal.nome(linha('Portaria 658 2026 MEC RSC')), 'portaria-658-2026')
        self.assertIsNone(federal.nome(linha('Manual', tipo='orientacao')))

    def test_pasta_pelo_tipo(self):
        self.assertEqual(federal.pasta(linha(), verificar.PASTA), 'normas/federais')
        self.assertEqual(federal.pasta(linha(tipo='orientacao'), verificar.PASTA), 'orientacoes')
        self.assertEqual(federal.pasta(linha(motivo='norma'), verificar.PASTA), 'normas')

    def test_ultima_alteracao_e_a_mais_recente(self):
        texto = ('Art. 1º ... (Redação dada pelo Decreto nº 5.707, de 2006)\n'
                 'Art. 2º ... (Incluído pela Lei nº 13.000, de 25 de junho de 2014)\n'
                 '§ 1º (Revogado pelo Decreto nº 9.991, de 2019)')
        self.assertEqual(federal.ultima_alteracao(texto), 'Decreto nº 9.991, de 2019')
        self.assertIsNone(federal.ultima_alteracao('Art. 1º Sem alteração.'))

    def test_anotar_grava_no_origin_note(self):
        with tempfile.TemporaryDirectory() as tmp:
            doc = Path(tmp) / 'd.md'
            doc.write_text('---\norigin: "https://x/a.pdf"\norigin_checked: "2026-11-26"\n---\n(Vide Decreto nº 7.000, de 2009)\n', encoding='utf-8')
            federal.anotar(doc, 'PROGEPE')
            nota = verificar.cabecalho(doc.read_text(encoding='utf-8'))['origin_note']
            self.assertIn('Cópia hospedada pela PROGEPE', nota)
            self.assertIn('Decreto nº 7.000, de 2009', nota)


if __name__ == '__main__':
    unittest.main()
