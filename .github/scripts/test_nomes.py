# test_nomes.py — o que nomes.py promete: o nome da pasta tem o ato ou o anexo e o assunto, nunca repete, e o que o título não diz vem do rótulo da descrição.
"""Uso: python -m unittest discover .github/scripts. Só stdlib, sem rede e sem o workspace."""
from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import nomes
import verificar


def linha(url='https://prpg.ufrpe.br/files/RECEPE989.2026%20APROVA%20NORMAS%20POS-DOUTORADO.pdf', titulo='Resolução 989/2026'):
    return {'url': url, 'titulo': titulo}


PROGESTI = 'https://www.progesti.ufrpe.br/sites/www.progesti.ufrpe.br/files/'


class Pasta(unittest.TestCase):
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

    def test_ato_numerado_no_padrao_do_acervo(self):
        self.assertEqual(nomes.ato('Resolução CEPE/UFRPE Nº 926, de 19 de agosto de 2025'), ['res', 'cepe', '926', '2025'])
        self.assertEqual(nomes.ato('Instrução Normativa UFRPE/PRPG Nº 01/2026'), ['in', 'prpg', '01', '2026'])
        self.assertEqual(nomes.ato('reconsu_294_2008_0'), ['res', 'consu', '294', '2008'])
        self.assertEqual(nomes.ato('recu104.2021_homologao_res._230.21_cepe'), ['res', 'consu', '104', '2021'])
        self.assertEqual(nomes.ato('Manual PROAP 2023'), [])


class Anexo(unittest.TestCase):
    def test_anexo_numerado_fica_no_nome_antes_do_assunto(self):
        relato = linha(url=PROGESTI + 'ANEXO%20IV%20-%20RELATO%20FAMILIAR%20(1).pdf', titulo='ANEXO IV - RELATO FAMILIAR')
        self.assertEqual(nomes.nome_da_pasta(relato, set()), 'anexo-iv-relato-familiar')

    def test_anexo_sem_assunto_espera_a_descricao(self):
        so = nomes.nome_da_pasta(linha(url=PROGESTI + 'Anexo%20V.pdf', titulo='Anexo V'), set())
        self.assertEqual(so, 'anexo-v')
        self.assertTrue(nomes.sem_assunto(so))
        self.assertTrue(nomes.sem_assunto('documento'))
        self.assertFalse(nomes.sem_assunto('anexo-iv-relato-familiar'))
        self.assertFalse(nomes.sem_assunto('res-consu-294-2008'))

    def test_o_rotulo_da_descricao_da_o_assunto(self):
        descricao = 'Mapa de visita domiciliar: espaço do candidato para detalhar o percurso.'
        self.assertEqual(nomes.pelo_rotulo('anexo-v', descricao, set()), 'anexo-v-mapa-visita-domiciliar')
        self.assertEqual(nomes.pelo_rotulo('documento', descricao, {'mapa-visita-domiciliar'}), 'mapa-visita-domiciliar-2')
        self.assertEqual(nomes.pelo_rotulo('anexo-i-2', 'Formulário do grupo familiar e saúde: declara.', set()), 'anexo-i-formulario-grupo-familiar-saude')


class Mover(unittest.TestCase):
    def test_pasta_md_original_e_source_vao_juntos(self):
        with tempfile.TemporaryDirectory() as tmp:
            modelos = Path(tmp) / 'modelos'
            (modelos / 'anexo-v' / 'img').mkdir(parents=True)
            (modelos / 'anexo-v.pdf').write_bytes(b'pdf')
            (modelos / 'anexo-v' / 'anexo-v.md').write_text('---\nsource: "../anexo-v.pdf"\n---\n\n![f](img/f.png)\n', encoding='utf-8')
            md = nomes.mover(modelos / 'anexo-v' / 'anexo-v.md', 'anexo-v-mapa')
            self.assertEqual(md, modelos / 'anexo-v-mapa' / 'anexo-v-mapa.md')
            self.assertEqual(md.read_text(encoding='utf-8'), '---\nsource: "../anexo-v-mapa.pdf"\n---\n\n![f](img/f.png)\n')
            self.assertEqual(sorted(p.name for p in modelos.iterdir()), ['anexo-v-mapa', 'anexo-v-mapa.pdf'])
            self.assertTrue((md.parent / 'img').is_dir())

    def test_nao_sobrescreve_pasta_que_existe(self):
        with tempfile.TemporaryDirectory() as tmp:
            for nome in ('a', 'b'):
                (Path(tmp) / nome).mkdir()
                (Path(tmp) / nome / f'{nome}.md').write_text('x', encoding='utf-8')
            with self.assertRaises(FileExistsError):
                nomes.mover(Path(tmp) / 'a' / 'a.md', 'b')


if __name__ == '__main__':
    unittest.main()
