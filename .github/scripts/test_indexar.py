# test_indexar.py — o que os volumes do acervo prometem: cortados entre documentos, nenhum acima do teto, na ordem pasta → caminho, todos os documentos uma vez.
"""Uso: python -m unittest discover .github/scripts. Só stdlib, sem rede."""
from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import indexar


def acervo(raiz: Path, palavras: dict[str, int]) -> list[dict]:
    """Um .md por caminho, com N palavras de corpo; devolve o índice como indexar.indice o monta."""
    for doc, n in palavras.items():
        (raiz / doc).parent.mkdir(parents=True, exist_ok=True)
        (raiz / doc).write_text(f'---\ndescription: "X: y."\norigin: "https://x/{doc}"\n---\n' + 'palavra ' * n, encoding='utf-8')
    return [{'doc': doc, 'titulo': doc} for doc in reversed(list(palavras))]


class Volumes(unittest.TestCase):
    def test_corta_entre_documentos_sem_passar_do_teto(self):
        with tempfile.TemporaryDirectory() as tmp:
            raiz = Path(tmp)
            docs = acervo(raiz, {'normas/a/a.md': 600, 'normas/b/b.md': 300, 'orientacoes/c/c.md': 300, 'tabelas/d/d.md': 50})
            vols = indexar.volumes(raiz, docs, 'teste', limite=1000)
            self.assertEqual(len(vols), 2)
            self.assertTrue(all(len(v.split()) < 1300 for v in vols))  # o teto conta o corpo; o índice no topo é pequeno
            self.assertIn('# normas/b/b.md', vols[0])
            self.assertIn('# orientacoes/c/c.md', vols[1])
            self.assertIn('volume 2 de 2', vols[1])
            juntos = ''.join(vols)
            self.assertEqual(sum(juntos.count(f'\n# {d["doc"]}\n') for d in docs), 4)

    def test_documento_maior_que_o_teto_fica_sozinho(self):
        with tempfile.TemporaryDirectory() as tmp:
            raiz = Path(tmp)
            vols = indexar.volumes(raiz, acervo(raiz, {'normas/a/a.md': 50, 'normas/b/b.md': 5000}), 'teste', limite=1000)
            self.assertEqual(len(vols), 2)
            self.assertIn('# normas/b/b.md', vols[1])


if __name__ == '__main__':
    unittest.main()
