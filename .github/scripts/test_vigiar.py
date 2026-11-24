# test_vigiar.py — o que o vigia do docs-ufrpe promete: achar todo link de documento, triar pelas regras e só dar por sumido o que uma coleta completa não viu.
"""Uso: python -m unittest discover .github/scripts. Só stdlib, sem rede."""
from __future__ import annotations

import ssl
import unittest

import rede
import regras
import tabela_censo
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

    def test_titulo_generico_vira_nome_do_arquivo_nunca_a_secao(self):
        url = 'https://x/files/2021-08/Requerimento%20Licen%C3%A7a%20Gestante_0.docx.pdf'
        self.assertEqual(regras.titulo('Baixar', url), 'Requerimento Licença Gestante')
        self.assertEqual(regras.titulo('', 'https://x/a/termo_de_opcao%20(1).pdf'), 'termo de opcao')
        self.assertEqual(regras.titulo('- PAVI Relatório', url), 'PAVI Relatório')
        self.assertEqual(regras.titulo('recepe_049.pdf', 'https://x/recepe_049.pdf', 'Resolução 049/2008 (Substituída)'),
                         'Resolução 049/2008 (Substituída)')
        self.assertEqual(regras.nome_do_arquivo('https://x/recepe_049.pdf'), 'recepe 049')

    def test_cabecalho_de_grupo_nao_vira_titulo(self):
        pagina = '<strong>Contato</strong><a href="/a.pdf">a.pdf</a><a href="/b.pdf">b.pdf</a><strong>Res. 1/2020</strong><a href="/c.pdf">c.pdf</a>'
        achados, _ = vigiar.coletar([{'setor': 'S', 'pagina': 'https://x.ufrpe.br/p'}], lambda _: pagina.encode())
        self.assertEqual(sorted(a['titulo'] for a in achados.values()), ['Res. 1/2020', 'a', 'b'])

    def test_titulo_refeito_decisao_mantida(self):
        censo = {'u': {'url': 'u', 'setores': 'PROGEPE', 'tipo': 'modelo', 'decisao': 'entra', 'motivo': 'formulário',
                       'titulo': 'Contato', 'data': '2026-11-23'}}
        achados = {'u': {'setores': {'PROGEPE'}, 'paginas': {'p'}, 'titulo': 'Requerimento', 'secao': 'Contato'}}
        vigiar.aplicar(censo, achados, [], [], [], '2026-11-24')
        self.assertEqual((censo['u']['titulo'], censo['u']['decisao'], censo['u']['data']), ('Requerimento', 'entra', '2026-11-23'))

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


class Tabela(unittest.TestCase):
    def linha(self, url, decisao='entra', motivo='norma', tipo='norma'):
        return {'url': url, 'setores': 'PRPG', 'tipo': tipo, 'decisao': decisao, 'motivo': motivo}

    def test_convertidos_contam_so_os_do_setor(self):
        linhas = [self.linha('a'), self.linha('b'), self.linha('lei', motivo='federal'), self.linha('r', 'fora', 'revogada', '')]
        entram, feitos, fora, pendentes = tabela_censo.contagem(linhas, {'a', 'lei'})
        self.assertEqual((entram, feitos, fora, pendentes), ('normas (3, 1 federal)', '1 de 2', 'revogada (1)', '—'))

    def test_a_data_sai_do_proprio_bloco(self):
        self.assertEqual(tabela_censo.data_contada('<!-- censo:start -->\nContado em 23/11/2026 por x'), '2026-11-23')

    def test_o_readme_do_repo_esta_em_dia(self):
        self.assertEqual(vigiar.tabela_offline('conferir'), 0, 'rode vigiar.py --tabela gravar')


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
        self.assertEqual(self.caso('1244.26-GR-DESIGNAR_Comisso_de_RSC_dos_TAEs.pdf')[2], 'ato sobre pessoas')
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
        self.assertEqual(self.caso('CALENDÁRIO GRADUAÇÃO 2024 e 2025.pdf')[1:], ('fora', 'versão superada'))
        self.assertEqual(self.caso('Calendario cursos presenciais 2025 final.pdf')[1:], ('fora', 'versão superada'))
        self.assertEqual(self.caso('CALENDÁRIO_GRADUAÇÃO_2026.pdf')[1], 'entra')

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
