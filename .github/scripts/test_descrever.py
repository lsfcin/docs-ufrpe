# test_descrever.py — o que o descrever.py do docs-ufrpe promete: o corpo limpo vai ao worker, a resposta é lida e validada, o segundo worker cobre o primeiro, e só a linha `description` muda.
"""Uso: python -m unittest discover .github/scripts. Só stdlib, sem rede, sem subprocesso e sem o workspace: o worker entra como função."""
from __future__ import annotations

import datetime
import json
import unittest
from pathlib import Path

import descrever
import verificar

REL = Path('modelos/a/a.md')
ANTES = '---\ndescription: "FORMULÁRIO: bolsa (PRPG)."\norigin: "https://prpg.ufrpe.br/a.pdf"\norigin_checked: "2026-11-23"\nsha256: null\n---\n'
CORPO = ('\n<!-- page 1 -->\n\n# Termo de compromisso\n\n![p01-fig1](img/p01-fig1.jpg)\n\n'
         '<!-- figure p01-fig1 | described_by: agy -->\n### 1. Tipo de figura\nUm brasão azul.\n\n---\n\nSetas e eixos.\n\n\n'
         'O bolsista se compromete a entregar o relatório.\n')
TEXTO = ANTES + CORPO
BOA = 'Termo de compromisso: o bolsista se compromete a entregar o relatório; assinam bolsista e orientador.'
EXEMPLOS = ['Res. CONSU 434/2024: a carga horária docente em vigor.']


def escritor(*respostas, nome='escritor'):
    """Um worker de mentira: devolve as respostas em ordem (uma exceção é lançada) e guarda os prompts que recebeu."""
    chamadas = []

    def escrever(prompt):
        chamadas.append(prompt)
        r = respostas[min(len(chamadas), len(respostas)) - 1]
        if isinstance(r, Exception):
            raise r
        return r
    escrever.__name__ = nome
    escrever.chamadas = chamadas
    return escrever


class Corpo(unittest.TestCase):
    def test_sem_frontmatter_figura_e_comentario(self):
        corpo = descrever.corpo_limpo(TEXTO)
        for lixo in ('origin', 'img/', '<!--', 'brasão', 'Setas'):
            self.assertNotIn(lixo, corpo)
        self.assertIn('# Termo de compromisso', corpo)
        self.assertIn('entregar o relatório', corpo)

    def test_corta_no_limite(self):
        corpo = descrever.corpo_limpo(ANTES + 'palavra ' * 2000)
        self.assertEqual(len(corpo), descrever.CORPO_MAX)
        self.assertEqual(descrever.CORPO_MAX, 6000)

    def test_prompt_traz_a_instrucao_os_exemplos_e_so_o_documento(self):
        prompt = descrever.montar_prompt(TEXTO, EXEMPLOS)
        self.assertIn('Escreva a linha `description`', prompt)
        self.assertIn(EXEMPLOS[0], prompt)
        self.assertIn('entregar o relatório', prompt)
        self.assertNotIn('prpg.ufrpe.br', prompt)


class Resposta(unittest.TestCase):
    def test_numeracao_aspas_e_cabecalho_do_painel_saem(self):
        for bruto in ('1. Nome: resto.', 'N. Nome: resto.', '- Nome: resto.', '"Nome: resto."', '`Nome: resto.`',
                      'description: "Nome: resto."', '\n\n  Nome: resto.\nOutra linha.',
                      '<!-- panel: deepseek v4 · 2026-11-23 10:00 -->\n1. Nome: resto.\n'):
            self.assertEqual(descrever.ler_resposta(bruto), 'Nome: resto.', bruto)

    def test_vazia(self):
        self.assertEqual(descrever.ler_resposta('<!-- panel: x -->\n\n'), '')

    def test_validacao(self):
        self.assertEqual(descrever.invalida(BOA), '')
        self.assertTrue(descrever.invalida('sem rótulo nenhum.'))
        self.assertTrue(descrever.invalida('N' * 41 + ': resto.'))
        self.assertTrue(descrever.invalida('Nome: sem ponto final'))
        self.assertTrue(descrever.invalida('Nome: ' + 'x' * 300 + '.'))
        self.assertTrue(descrever.invalida('Nome: resto 日本.'))

    def test_rascunho_do_conversor(self):
        self.assertTrue(descrever.rascunho('Nome: resto (PRPG).'))
        self.assertTrue(descrever.rascunho('Nome: resto (PRPG).', 'PRPG'))
        self.assertFalse(descrever.rascunho('Nome: resto (PRPG).', 'PREG'))
        self.assertFalse(descrever.rascunho('Nome: resto (prpg).'))
        self.assertTrue(descrever.rascunho('Nome: resto (Reitoria).', 'Reitoria'))
        self.assertFalse(descrever.rascunho('Res. CONSU 434/2024: a carga horária docente.'))


class Reescrita(unittest.TestCase):
    def test_troca_so_a_linha_description_e_o_resto_fica_igual(self):
        novo, porque = descrever.descrever(TEXTO, escritor('1. ' + BOA), EXEMPLOS, REL)
        self.assertEqual(porque, '')
        self.assertEqual(novo, TEXTO.replace('"FORMULÁRIO: bolsa (PRPG)."', json.dumps(BOA, ensure_ascii=False)))
        self.assertEqual(novo.splitlines()[2:], TEXTO.splitlines()[2:])

    def test_o_arquivo_novo_passa_no_verificar(self):
        novo, _ = descrever.descrever(TEXTO, escritor(BOA), EXEMPLOS, REL)
        erros, _, campos = verificar.conferir(REL, novo, datetime.date(2026, 11, 23))
        self.assertEqual(erros, [])
        self.assertEqual(campos['description'], BOA)

    def test_segundo_worker_quando_a_resposta_do_primeiro_e_invalida(self):
        primeiro, segundo = escritor('resposta sem rótulo', nome='deepseek'), escritor(BOA, nome='codex')
        novo, porque = descrever.descrever(TEXTO, (primeiro, segundo), EXEMPLOS, REL)
        self.assertIn(BOA, novo)
        self.assertEqual((len(primeiro.chamadas), len(segundo.chamadas)), (1, 1))

    def test_segundo_worker_quando_o_primeiro_falha(self):
        primeiro, segundo = escritor(OSError('sem rede'), nome='deepseek'), escritor(BOA, nome='codex')
        self.assertIsNotNone(descrever.descrever(TEXTO, (primeiro, segundo), EXEMPLOS, REL)[0])

    def test_primeiro_que_serve_dispensa_o_segundo(self):
        primeiro, segundo = escritor(BOA), escritor(BOA)
        descrever.descrever(TEXTO, (primeiro, segundo), EXEMPLOS, REL)
        self.assertEqual(segundo.chamadas, [])

    def test_os_dois_falham_o_arquivo_fica_e_o_motivo_vai_para_revisao(self):
        primeiro, segundo = escritor('1. sem rótulo', nome='deepseek'), escritor('Nome: sem ponto', nome='codex')
        novo, porque = descrever.descrever(TEXTO, (primeiro, segundo), EXEMPLOS, REL)
        self.assertIsNone(novo)
        self.assertIn('deepseek:', porque)
        self.assertIn('codex: não termina em ponto', porque)

    def test_documento_sem_description_nao_e_tocado(self):
        sem = TEXTO.replace('description: "FORMULÁRIO: bolsa (PRPG)."\n', '')
        self.assertIsNone(descrever.descrever(sem, escritor(BOA), EXEMPLOS, REL)[0])

    def test_corpo_vazio_nao_vai_ao_worker(self):
        """Só comentário de página e figura não é texto: o worker inventaria uma descrição para o nada."""
        chamado = escritor(BOA)
        novo, porque = descrever.descrever(ANTES + '\n<!-- page 1 -->\n\n![p01-fig1](img/p01-fig1.jpg)\n', chamado, EXEMPLOS, REL)
        self.assertEqual((novo, chamado.chamadas), (None, []))
        self.assertIn('corpo vazio', porque)


if __name__ == '__main__':
    unittest.main()
