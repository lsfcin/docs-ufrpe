// viewer.js — mostra um .md do docs-ufrpe formatado: faixa com o brasão em negativo, cartão do original oficial, listas legíveis e o caminho para propor correção no GitHub.
const REPO = 'https://github.com/lsfcin/docs-ufrpe';
const PASTAS = { orientacoes: 'Orientações' };
const TRAD = { Subdirectory: 'Pasta', File: 'Documento', Description: 'Descrição', Routing: 'Nesta seção' };

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
const nomePasta = (p) => PASTAS[p] || p[0].toUpperCase() + p.slice(1);

// As figuras não entram no git; a descrição delas fica recolhida. Ela vai do marcador até duas linhas em branco,
// o próximo marcador de página ou o fim: a mesma regra de .github/scripts/indexar.py.
function figuras(md) {
  return md.replace(/<!-- figure [^>]*-->\n([\s\S]*?)(?=\n[ \t]*\n[ \t]*\n|<!-- page|$(?![\s\S]))/g, (_, bloco) => {
    const tipo = bloco.match(/Tipo de figura:\*\*\s*([^\n.(]+)/);
    const resumo = tipo ? `Figura: ${tipo[1].trim().replace(/[<>]/g, '')}` : 'Descrição da figura';
    return bloco.trim() ? `\n<details>\n<summary>\n${resumo}\n</summary>\n\n${bloco}\n</details>\n\n` : '';
  });
}

function cartao(c) {
  if (!c.origin || !/^https?:/i.test(c.origin)) return '';
  const conferido = data(c.origin_checked) ? ` · conferido em ${data(c.origin_checked)}` : '';
  return `<aside class="cartao">${c.description ? `<p class="desc">${esc(c.description)}</p>` : ''}
    <p><a class="btn forte" href="${esc(c.origin)}" target="_blank" rel="noopener">Original oficial ↗</a><span class="meta">${conferido}</span></p>
    ${c.needs_review === true ? '<p class="aviso">Texto convertido automaticamente, ainda não revisado. Em caso de divergência, prevalece o original.</p>' : ''}</aside>`;
}

// Só as pastas de seção (as que têm CONTEXT.md); a pasta própria de cada documento não aparece.
function trilha(doc) {
  const partes = doc.split('/').slice(0, -1).slice(0, doc.startsWith('normas/federais/') ? 2 : 1);
  let caminho = '';
  return partes.map((p) => { caminho += `${p}/`; return ` / <a href="?doc=${encodeURIComponent(`${caminho}CONTEXT.md`)}">${esc(nomePasta(p))}</a>`; }).join('');
}

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

// Uma tabela cuja 1ª coluna é só link vira lista: nome legível à esquerda, descrição à direita.
function rotulo(a, desc) {
  const nome = a.textContent.trim();
  if (nome.endsWith('/')) return [nomePasta(nome.slice(0, -1).split('/').pop()), desc];
  const m = desc.match(/^([^:]{2,40}):\s*(.+)$/);
  return m ? [m[1], m[2][0].toUpperCase() + m[2].slice(1)] : [nome.split('/').pop().replace(/\.md$/, ''), desc];
}
function tabelas(raiz) {
  raiz.querySelectorAll('table').forEach((t) => {
    const linhas = [...t.querySelectorAll('tbody tr')];
    const soLink = (tr) => tr.cells[0].querySelector('a') && tr.cells[0].textContent.trim() === tr.cells[0].querySelector('a').textContent.trim();
    if (!linhas.length || !linhas.every(soLink)) {
      t.querySelectorAll('th').forEach((th) => { th.textContent = TRAD[th.textContent.trim()] || th.textContent; });
      return;
    }
    const pasta = /Subdirectory|Pasta/.test(t.querySelector('thead th')?.textContent || '');
    const corpo = linhas.map((tr) => {
      const a = tr.cells[0].querySelector('a');
      const [nome, desc] = rotulo(a, tr.cells[tr.cells.length - 1].textContent.trim());
      return `<tr><td class="acao"><a class="pill" href="${a.getAttribute('href')}">${esc(nome)}</a></td><td>${esc(desc)}</td></tr>`;
    }).join('');
    t.innerHTML = `<thead><tr><th>${pasta ? 'Pastas' : 'Documentos'}</th><th>Descrição</th></tr></thead><tbody>${corpo}</tbody>`;
    t.classList.add('entradas');
  });
  raiz.querySelectorAll('h2').forEach((h) => { if (TRAD[h.textContent.trim()]) h.textContent = TRAD[h.textContent.trim()]; });
}

function topo(doc) {
  const nav = doc === 'README.md' ? '' : `<nav class="topo"><a href="./">Início</a>${trilha(doc)}</nav>`;
  return `<header class="cabeca"><div class="dentro">
    <a class="marca" href="./"><img src="brasao-negativo.png" alt="Universidade Federal Rural de Pernambuco"></a>
    <a class="marca texto" href="./"><b>Docs<br>UFRPE</b></a>
    <p class="explica">Documentos oficiais da Universidade Federal Rural de Pernambuco (UFRPE), reproduzidos em Markdown para leitura no celular, busca e citação. Este site não é oficial da UFRPE. Em caso de divergência, prevalece o documento original.</p>
    <p class="autoria">Iniciativa pessoal de Lucas Silva Figueiredo, professor do Departamento de Computação da UFRPE.</p>
    <form class="busca" role="search"><label for="q">Buscar nos documentos</label>
      <input id="q" type="search" autocomplete="off" enterkeyhint="search" placeholder="interstício, RSC, acerto financeiro…"></form>
  </div></header>${nav}<section id="resultados" class="container" aria-live="polite" hidden></section>`;
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
    // Sem HTML vindo do texto (um PR de fora não injeta script): passam só <br>, <details> e <summary>, sem atributos.
    const limpo = figuras(corpo).replace(/<!--[\s\S]*?-->/g, '').replace(/!\[[^\]]*\]\((?!https?:)[^)]*\)/g, '')
      .replace(/<(?!br\s*\/?>|\/?details>|\/?summary>)/gi, '&lt;');
    const html = marked.parse(limpo, { gfm: true, breaks: false }).replace(/<table>/g, '<div class="tabela"><table>').replace(/<\/table>/g, '</table></div>');
    app.innerHTML = `${topo(doc)}<div class="container">${cartao(campos)}
      <article class="markdown-body">${html}</article>
      <footer>
        <a class="btn" href="${REPO}/edit/main/${esc(doc)}" target="_blank" rel="noopener">Propor correção</a>
        <button class="btn" id="copiar">Copiar texto para IA</button>
        <a class="btn" href="${esc(doc)}" target="_blank" rel="noopener">Texto em Markdown</a>
        <a class="btn" href="${REPO}" target="_blank" rel="noopener">Repositório no GitHub</a>
      </footer></div>`;
    ligarBusca(app);
    const art = app.querySelector('article');
    relink(art, doc);
    tabelas(art);
    // O resumo de uma linha sob o título é para o GitHub e o agente; na home, o título também sai (a faixa já o diz).
    const h1 = art.querySelector('h1');
    if (/(^|\/)(README|CONTEXT)\.md$/.test(doc) && h1?.nextElementSibling?.tagName === 'BLOCKQUOTE') h1.nextElementSibling.remove();
    const pasta = doc.match(/([\w-]+)\/CONTEXT\.md$/);
    if (h1 && pasta && h1.textContent.trim() === pasta[1]) h1.textContent = nomePasta(pasta[1]);
    if (doc === 'README.md') {
      h1?.remove();
      // O aviso "prevalece o original" do README é para o GitHub; no site, a faixa azul já o dá.
      [...art.querySelectorAll('p')].find((p) => /prevalece o original/.test(p.textContent))?.remove();
    }
    document.title = h1 && doc !== 'README.md' ? `${h1.textContent} · Docs UFRPE` : 'Docs UFRPE';
    const copiar = document.getElementById('copiar');
    copiar.addEventListener('click', async () => {
      try { await navigator.clipboard.writeText(bruto); copiar.textContent = 'Copiado'; }
      catch { location.href = doc; }
      setTimeout(() => { copiar.textContent = 'Copiar texto para IA'; }, 2000);
    });
    const q = new URLSearchParams(location.search).get('q');
    if (q) destacar(art, q);
  } catch (e) {
    app.innerHTML = `${topo(doc)}<div class="container"><p class="aviso">Não foi possível abrir ${esc(doc)} (${esc(e.message)}). <a href="./">Voltar ao início</a>.</p></div>`;
    ligarBusca(app);
  }
});

// A caixa da faixa azul procura em todo o acervo (busca.js); os resultados tomam o lugar da página enquanto há busca.
function ligarBusca(app) {
  caixa(app.querySelector('form.busca'), app.querySelector('#resultados'), app.querySelector('.container:not(#resultados)'));
}
