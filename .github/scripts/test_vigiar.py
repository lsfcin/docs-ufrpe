# test_vigiar.py — o que o vigia do docs-ufrpe promete: achar todo link de documento, triar pelas regras e só dar por sumido o que uma coleta completa não viu.
"""Uso: python -m unittest discover .github/scripts. Só stdlib, sem rede."""
from __future__ import annotations

import ssl
import unittest

import rede
import regras
import vigiar

PAGINA = '''<html><body><h2>Resoluções</h2>
<a href="/sites/files/RECEPE%20744.2024%20RGG.pdf ">Regulamento Geral</a>
<a href="https://x.ufrpe.br/sites/files/RECEPE 744.2024 RGG.pdf#p2">mesmo arquivo</a>
<strong>Formulários</strong><a href="/f/requerimento_geral.docx">Baixar</a>
<a href="/noticias">não é documento</a><img src="/logo.png"></body></html>'''


class Coleta(unittest.TestCase):
    def test_um_link_por_arquivo_com_espaco_e_fragmento(self):
        achados = vigiar.links(PAGINA, 'https://x.ufrpe.br/br/resolucoes')
        self.assertEqual({u for u, _, _ in achados}, {
            'https://x.ufrpe.br/sites/files/RECEPE%20744.2024%20RGG.pdf', 'https://x.ufrpe.br/f/requerimento_geral.docx'})

    def test_titulo_generico_vira_secao(self):
        self.assertEqual(regras.titulo('Baixar', 'Formulários'), 'Formulários')
        self.assertEqual(regras.titulo('- PAVI Relatório', 'Requerimentos'), 'PAVI Relatório')

    def test_sumido_so_quando_o_setor_foi_lido(self):
        censo = {'a': {'setores': 'PREG'}, 'b': {'setores': 'PRPG'}}
        novos, sumidos = vigiar.comparar(censo, {'c': {}}, {'PRPG': ['falhou']})
        self.assertEqual((novos, sumidos), (['c'], ['a']))

    def test_pagina_salva_pela_canonical(self):
        import tempfile
        from pathlib import Path
        with tempfile.TemporaryDirectory() as pasta:
            Path(pasta, 'p.html').write_text('<link rel="canonical" href="https://x.ufrpe.br/br/in%C3%ADcio">')
            self.assertIn(b'canonical', rede.salvas(Path(pasta))('https://x.ufrpe.br/br/início'))


class Triagem(unittest.TestCase):
    def caso(self, nome, titulo='', secao='', pagina=None):
        return regras.classificar(f'https://x/{nome}', titulo, secao, pagina, 2026)

    def test_regras(self):
        self.assertEqual(self.caso('recepe049.pdf', 'Resolução 049/2008 (Substituída pela 444)')[1:], ('fora', 'revogada'))
        self.assertEqual(self.caso('proap_-_portaria_156_2014_capes.pdf')[2], 'federal')
        self.assertEqual(self.caso('portaria_123_2025.pdf')[2], 'ato sobre pessoas')
        self.assertEqual(self.caso('estatuto-ufrpe.pdf', 'Estatuto', 'Documentos e Relatórios UFRPE')[0], 'norma')
        self.assertEqual(self.caso('relatorio_viagem_discente.doc', 'RELATÓRIO DE VIAGEM')[0], 'modelo')
        self.assertEqual(self.caso('relatorio_gestao_ufrpe_2010.pdf')[2], 'relatório')
        self.assertEqual(self.caso('MODELO HISTÓRICOS CNE.docx')[0], 'modelo')
        # 23/11/2026: o que a PROGEPE publica sem palavra-chave das regras antigas.
        self.assertEqual(self.caso('768.26-GR-ALTERAR_PORT._682.2026-GR.pdf')[2], 'ato sobre pessoas')
        self.assertEqual(self.caso('Processo 322032 2023.pdf', 'Resolução 458/2023')[2], 'norma')
        self.assertEqual(self.caso('D12246_dispensa para exames.pdf')[2], 'federal')
        self.assertEqual(self.caso('Tabela Carreira EBTT - 01MAI2023.pdf')[0], 'tabela')
        self.assertEqual(self.caso('tabela de horas extras.docx')[0], 'modelo')
        # 24/11/2026: calendário tem pasta própria, e só o vigente entra.
        self.assertEqual(self.caso('CALENDÁRIO PRPG 2026-03-05.pdf'), ('calendario', 'entra', 'calendário'))
        self.assertEqual(self.caso('CALENDARIO 2016.pdf')[1:], ('fora', 'versão superada'))

    def test_so_a_versao_vigente(self):
        self.assertEqual(self.caso('pdi_ufrpe_2013-2020.pdf', 'PDI 2013-2020')[1:], ('fora', 'versão superada'))
        self.assertEqual(self.caso('PDI-UFRPE-2021-2030.pdf')[1], 'entra')
        self.assertEqual(self.caso('Plano de Integridade - 2018-12-10.pdf')[1], 'entra')
        self.assertEqual(self.caso('Calendário 2014.pdf')[1:], ('fora', 'versão superada'))

    def test_regra_da_pagina(self):
        revogada = regras.regra_da_pagina('!norma:fora:revogada')
        self.assertEqual(self.caso('recepe280.2021.pdf', 'Resolução 280/2021', '', revogada)[1], 'fora')
        self.assertEqual(self.caso('x.pdf', 'Política de evasão', '', regras.regra_da_pagina('norma:entra:norma'))[0], 'norma')
        self.assertEqual(self.caso('x.pdf', 'Catálogo')[1], 'pendente')


class Rede(unittest.TestCase):
    def test_aia_acha_caissuers_e_ignora_ocsp_e_crl(self):
        der = b'\x30..http://ocsp.x.com/..http://crl.x.com/a.crl..http://secure.x.com/cacert/ca2025.crt\x30'
        self.assertEqual(rede.AIA.findall(der), [b'http://secure.x.com/cacert/ca2025.crt'])

    def test_contexto_verifica(self):
        rede._contextos['exemplo.invalid'] = ssl.create_default_context()
        self.assertEqual(rede.contexto('exemplo.invalid').verify_mode, ssl.CERT_REQUIRED)


if __name__ == '__main__':
    unittest.main()
