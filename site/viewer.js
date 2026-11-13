// viewer.js — mostra um .md do docs-ufrpe formatado: o cabeçalho vira o cartão do original oficial, e cada página leva ao GitHub para propor correção.
const REPO = 'https://github.com/lsfcin/docs-ufrpe';

// O frontmatter `chave: valor` do topo, no mesmo formato que .github/scripts/verificar.py lê.
function cabecalho(texto) {
  const m = texto.match(/^---\n([\s\S]*?)\n---\n/);
  if (!m) return { campos: {}, corpo: texto };
  const campos = {};
  for (const linha of m[1].split('\n')) {
    const i = linha.indexOf(':');
    if (i < 1 || linha.startsWith(' ')) continue;
    const valor = linha.slice(i + 1).trim();
    try { campos[linha.slice(0, i).trim()] = JSON.parse(valor); }
    catch { campos[linha.slice(0, i).trim()] = valor.replace(/^["']|["']$/g, ''); }
  }
  return { campos, corpo: texto.slice(m[0].length) };
}

const esc = (s) => String(s).replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
const data = (iso) => (/^\d{4}-\d{2}-\d{2}$/.test(iso || '') ? iso.split('-').reverse().join('/') : '');

function cartao(c) {
  if (!c.origin || !/^https?:/i.test(c.origin)) return '';
  const linhas = [];
  if (c.description) linhas.push(`<p class="desc">${esc(c.description)}</p>`);
  const conferido = data(c.origin_checked) ? ` · conferido em ${data(c.origin_checked)}` : '';
  linhas.push(`<p><a class="btn forte" href="${esc(c.origin)}" target="_blank" rel="noopener">Original oficial ↗</a><span class="meta">${conferido}</span></p>`);
  if (c.origin_note) linhas.push(`<p class="meta">${esc(c.origin_note)}</p>`);
  if (c.needs_review === true) linhas.push('<p class="aviso">Texto convertido automaticamente e ainda não revisado contra o original: na dúvida, vale o original.</p>');
  return `<aside class="cartao">${linhas.join('')}</aside>`;
}

function trilha(doc) {
  const partes = doc.split('/').slice(0, -1);
  let caminho = '';
  return partes.map((p) => { caminho += `${p}/`; return ` / <a href="?doc=${caminho}CONTEXT.md">${esc(p)}</a>`; }).join('');
}

// Links para .md do repositório abrem aqui; pastas abrem o CONTEXT.md delas; o resto vai para o GitHub.
function relink(raiz, doc) {
  const base = new URL(doc, 'https://x/');
  raiz.querySelectorAll('a[href]').forEach((a) => {
    const href = a.getAttribute('href');
    if (/^https?:/i.test(href)) { a.target = '_blank'; a.rel = 'noopener'; return; }
    if (href.startsWith('#')) return;
    if (/^[a-z]+:/i.test(href)) { a.removeAttribute('href'); return; }
    const alvo = new URL(href, base);
    let caminho = decodeURIComponent(alvo.pathname.slice(1));
    if (caminho.endsWith('/')) caminho += 'CONTEXT.md';
    a.href = caminho.endsWith('.md') ? `?doc=${encodeURIComponent(caminho)}${alvo.hash}` : `${REPO}/blob/main/${caminho}`;
  });
}

document.addEventListener('DOMContentLoaded', async () => {
  const app = document.getElementById('app');
  const doc = new URLSearchParams(location.search).get('doc') || 'README.md';
  if (!/^[\w./-]+\.md$/.test(doc) || doc.split('/').includes('..')) { app.textContent = 'Documento inválido.'; return; }
  try {
    const res = await fetch(doc);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const bruto = await res.text();
    const { campos, corpo } = cabecalho(bruto);
    const titulo = corpo.match(/^#\s+(.+)$/m);
    if (titulo) document.title = `${titulo[1]} · docs-ufrpe`;
    // Sem HTML vindo do texto (um PR de fora não injeta script); só <br>, que as tabelas convertidas usam.
    const limpo = corpo.replace(/<!--[\s\S]*?-->/g, '').replace(/<(?!br\s*\/?>)/gi, '&lt;');
    marked.setOptions({ gfm: true, breaks: false });
    const html = marked.parse(limpo).replace(/<table>/g, '<div class="tabela"><table>').replace(/<\/table>/g, '</table></div>');
    app.innerHTML = `
      <nav class="topo"><a href="./">docs-ufrpe</a>${trilha(doc)}</nav>
      ${cartao(campos)}
      <article class="markdown-body">${html}</article>
      <footer>
        <a class="btn" href="${REPO}/edit/main/${esc(doc)}" target="_blank" rel="noopener">propor correção</a>
        <button class="btn" id="copiar">copiar p/ IA</button>
        <a class="btn" href="${esc(doc)}" target="_blank" rel="noopener">texto puro</a>
        <a class="btn" href="${REPO}" target="_blank" rel="noopener">repositório</a>
      </footer>`;
    relink(app.querySelector('article'), doc);
    const copiar = document.getElementById('copiar');
    copiar.addEventListener('click', async () => {
      try { await navigator.clipboard.writeText(bruto); copiar.textContent = 'copiado!'; }
      catch { location.href = doc; }
      setTimeout(() => { copiar.textContent = 'copiar p/ IA'; }, 2000);
    });
  } catch (e) {
    app.innerHTML = `<p class="aviso">Não consegui abrir ${esc(doc)} (${esc(e.message)}). <a href="./">Voltar ao início</a>.</p>`;
  }
});
