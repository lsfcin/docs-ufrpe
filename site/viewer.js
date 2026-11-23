// viewer.js — realça a página pronta do docs-ufrpe (gerada no deploy por .github/scripts/paginas.py): liga a busca, o botão de copiar o texto para IA e o destaque do termo buscado; um link antigo ?doc= vai para a página nova.

// Os links de antes (?doc=normas/x.md) foram compartilhados; levam à página que hoje é a do documento,
// cujo endereço o busca.json traz (paginas.py `pagina`, a regra só mora lá).
function antigo(raiz) {
  const busca = new URLSearchParams(location.search);
  const doc = busca.get('doc');
  if (!doc) return false;
  busca.delete('doc');
  const resto = busca.toString();
  carregar(raiz).then((docs) => {
    const achado = docs.find((d) => d.doc === doc);
    if (achado) location.replace(`${raiz}${achado.pagina}${resto ? `?${resto}` : ''}${location.hash}`);
  }).catch(() => {});
  return true;
}

function copiar(fonte) {
  const botao = document.getElementById('copiar');
  if (!botao || !fonte) return;
  botao.hidden = false;
  botao.addEventListener('click', async () => {
    try {
      const res = await fetch(fonte.getAttribute('href'));
      await navigator.clipboard.writeText(await res.text());
      botao.textContent = 'Copiado';
    } catch { location.href = fonte.getAttribute('href'); }
    setTimeout(() => { botao.textContent = 'Copiar texto para IA'; }, 2000);
  });
}

document.addEventListener('DOMContentLoaded', () => {
  const raiz = document.body.dataset.raiz || './';
  if (antigo(raiz)) return;
  // A caixa da faixa azul procura em todo o acervo (busca.js); os resultados tomam o lugar da página enquanto há busca.
  caixa(document.querySelector('form.busca'), document.getElementById('resultados'),
    document.querySelector('.container:not(#resultados)'), document.body.dataset.doc, raiz);
  copiar(document.querySelector('link[rel="alternate"][type="text/markdown"]'));
  const q = new URLSearchParams(location.search).get('q');
  if (q) destacar(document.querySelector('article'), q);
});
