# test_verificar.py — o que o verificar.py do docs-ufrpe promete sobre o nome: uma norma se chama no padrão do lote 1, e dois documentos nunca têm o mesmo nome.
"""Uso: python -m unittest discover .github/scripts. Só stdlib, sem rede."""
from __future__ import annotations

import datetime
import unittest
from pathlib import Path

import verificar

HOJE = datetime.date(2026, 11, 24)


def documento(descricao: str) -> str:
    return (f'---\ndescription: "{descricao}"\norigin: "https://prpg.ufrpe.br/a.pdf"\n'
            f'origin_checked: "2026-11-24"\nsha256: null\n---\n\nTexto.\n')


def erros(rel: str, descricao: str) -> list[str]:
    return verificar.conferir(Path(rel), documento(descricao), HOJE)[0]


class NomeDaNorma(unittest.TestCase):
    def test_o_padrao_do_lote_1_passa(self):
        for nome in ('Res. CEPE 609/2023', 'Res. CONSU 435-A/2024', 'Res. CEPE 1003/2026', 'IN PRPG 01/2026'):
            self.assertEqual(erros('normas/a/a.md', f'{nome}: algo.'), [], nome)

    def test_o_que_o_lote_prpg_trouxe_reprova(self):
        for nome in ('Res. CEPE/UFRPE 609/2023', 'Resolução CONSU 104/2021', 'Resolução 302/2023',
                     'IN UFRPE/PRPG 01/2022', 'Instrução Normativa 5/2014'):
            self.assertTrue(any('padrão das normas' in e for e in erros('normas/a/a.md', f'{nome}: algo.')), nome)

    def test_norma_sem_numero_e_outras_pastas_ficam_livres(self):
        self.assertEqual(erros('normas/a/a.md', 'Plano de Internacionalização 2025-2030: metas.'), [])
        self.assertEqual(erros('orientacoes/a/a.md', 'Resolução comentada: algo.'), [])


class NomeRepetido(unittest.TestCase):
    def test_cada_dono_do_nome_repetido_aponta_o_outro(self):
        a, b, c = Path('modelos/a/a.md'), Path('modelos/b/b.md'), Path('modelos/c/c.md')
        achados = verificar.repetidos({a: 'Solicitação de Empenho', b: 'Solicitação de Empenho', c: 'Termo'})
        self.assertEqual(set(achados), {a, b})
        self.assertIn(str(b), achados[a])

    def test_nome_e_o_que_vem_antes_dos_dois_pontos(self):
        self.assertEqual(verificar.nome('IN PRPG 01/2026: bolsas: regras.'), 'IN PRPG 01/2026')


if __name__ == '__main__':
    unittest.main()
