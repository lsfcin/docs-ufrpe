# test_limpeza.py — o que limpeza.py promete: o corpo convertido sai sem imagem embutida e sem a caixa de seleção que o OCR lê como ideograma, e o frontmatter fica byte a byte.
"""Uso: python -m unittest discover .github/scripts. Só stdlib, sem rede e sem o workspace."""
from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import limpeza
import verificar


class Corpo(unittest.TestCase):
    def test_imagem_embutida_sai_e_o_texto_fica(self):
        corpo = '![][image1]\n\n# ANEXO I\n\n| A | B |\n\n[image1]: <data:image/png;base64,iVBORw0KGgo>\n'
        self.assertEqual(limpeza.sem_imagens(corpo).strip(), '# ANEXO I\n\n| A | B |')

    def test_caixa_de_selecao_do_ocr_vira_caixa_e_marcador_vira_bolinha(self):
        self.assertEqual(limpeza.caixas('口 Sim 日 Não 目 Talvez 品 Nunca\n item\n seta'), '☐ Sim ☐ Não ☐ Talvez ☐ Nunca\n• item\n➢ seta')

    def test_arquivo_limpo_passa_no_verificar_e_o_frontmatter_nao_muda(self):
        cabeca = verificar.frontmatter({'description': 'A: b (PRPG).', 'origin': 'https://x/a.pdf', 'origin_checked': '2026-11-23',
                                        'sha256': '0' * 64})
        with tempfile.TemporaryDirectory() as tmp:
            md = Path(tmp) / 'a.md'
            md.write_text(cabeca + '口 Sim\n', encoding='utf-8')
            limpeza.arquivo(md)
            texto = md.read_text(encoding='utf-8')
        self.assertEqual(texto, cabeca + '☐ Sim\n')
        self.assertIsNone(verificar.ESTRANHO.search(texto))


if __name__ == '__main__':
    unittest.main()
