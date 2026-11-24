# test_verificar.py — o que o verificar.py do docs-ufrpe promete: uma norma se chama no padrão do lote 1, dois documentos nunca têm o mesmo nome, e todo documento está no censo, na rota da pasta e no README.
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


class Acervo(unittest.TestCase):
    """O que liga um documento ao resto: a linha no censo, a rota da pasta e a pasta no README."""

    def test_fora_do_censo_so_reprova_o_que_nao_e_federal(self):
        campos = {'origin': 'http://prpg.ufrpe.br/a%20b.pdf'}
        self.assertIsNone(verificar.fora_do_censo(Path('normas/a/a.md'), campos, {'https://prpg.ufrpe.br/a b.pdf'}))
        self.assertIn('fontes.tsv', verificar.fora_do_censo(Path('normas/a/a.md'), campos, set()))
        self.assertIsNone(verificar.fora_do_censo(Path('normas/federais/lei.md'), campos, set()))

    def test_fora_da_rota_acha_o_context_mais_proximo(self):
        import tempfile
        from unittest import mock
        with tempfile.TemporaryDirectory() as tmp:
            raiz = Path(tmp)
            (raiz / 'modelos' / 'a').mkdir(parents=True)
            (raiz / 'modelos' / 'CONTEXT.md').write_text('| [`a/a.md`](a/a.md) | A |\n', encoding='utf-8')
            with mock.patch.object(verificar, 'RAIZ', raiz):
                self.assertIsNone(verificar.fora_da_rota(Path('modelos/a/a.md')))
                self.assertIn('context_synchronizer', verificar.fora_da_rota(Path('modelos/b/b.md')))

    def test_pasta_oculta_nao_e_acervo(self):
        import indexar
        self.assertTrue(indexar.oculto(Path('.pytest_cache/README.md')))
        self.assertFalse(indexar.oculto(Path('normas/a/a.md')))

    def test_pasta_fora_do_readme(self):
        readme = '## Organização\n\n' + ''.join(f'| [`{p}/`]({p}/CONTEXT.md) | x |\n' for p in verificar.PASTAS[1:]) + '\n## Outra\n[`calendarios/`]'
        self.assertEqual(verificar.pastas_fora_do_readme(readme), [verificar.PASTAS[0]])


if __name__ == '__main__':
    unittest.main()
