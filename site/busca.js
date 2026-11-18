// busca.js — a caixa "Buscar nos documentos" do docs-ufrpe: lê o busca.json do deploy, acha sem acento nem maiúscula, tolera um erro de digitação e destaca o termo no documento aberto.
// Nada do índice vira HTML: títulos, trechos e destaques entram por textContent e nós criados aqui.

const MAX = 20;
const PESOS = { titulo: 10, descricao: 5 };

// Sem acento e minúscula, unidade por unidade de UTF-16: o resultado tem o mesmo comprimento,
// então um índice no texto dobrado vale no original (trecho e destaque dependem disso).
function dobra(s) {
  return s.split('').map((c) => {
    const n = c.normalize('NFD').replace(/[̀-ͯ]/g, '').toLowerCase();
    return n.length === 1 ? n : '\u0000';
  }).join('');
}

const palavras = (q) => dobra(q).split(/[^a-z0-9]+/).filter(Boolean);
const escapa = (w) => w.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
// Até 3 letras (RSC, PDA) só casa como palavra inteira; o resto casa como pedaço ("progre" acha "progressão").
const padrao = (w) => new RegExp(w.length <= 3 ? `(?<![a-z0-9])${escapa(w)}(?![a-z0-9])` : escapa(w), 'g');

// Distância de edição até `lim`, desistindo assim que a linha inteira passa do limite.
function perto(a, b, lim) {
  if (Math.abs(a.length - b.length) > lim) return false;
  let antes = Array.from({ length: b.length + 1 }, (_, i) => i);
  for (let i = 1; i <= a.length; i++) {
    const agora = [i];
    let menor = i;
    for (let j = 1; j <= b.length; j++) {
      agora[j] = Math.min(antes[j] + 1, agora[j - 1] + 1, antes[j - 1] + (a[i - 1] === b[j - 1] ? 0 : 1));
      menor = Math.min(menor, agora[j]);
    }
    if (menor > lim) return false;
    antes = agora;
  }
  return antes[b.length] <= lim;
}

// A palavra do corpus mais parecida com `w` (1 erro; 2 a partir de 8 letras), ou null. Só para palavras de 5+ letras.
function parecida(w, vocabulario) {
  if (w.length < 5) return null;
  const lim = w.length >= 8 ? 2 : 1;
  for (const t of vocabulario) if (perto(w, t, lim) || perto(w, t.slice(0, w.length), lim)) return t;
  return null;
}

let indice = null;
function carregar() {
  if (!indice) {
    indice = fetch('busca.json').then((r) => { if (!r.ok) throw new Error(`HTTP ${r.status}`); return r.json(); })
      .then((docs) => docs.map((d) => ({ ...d, f: { titulo: dobra(d.titulo), descricao: dobra(d.descricao), texto: dobra(d.texto) } })))
      .catch((e) => { indice = null; throw e; });
  }
  return indice;
}

let vocab = null;
const vocabulario = (docs) => vocab || (vocab = [...new Set(docs.flatMap((d) => `${d.f.titulo} ${d.f.descricao} ${d.f.texto}`.split(/[^a-z0-9]+/)).filter((t) => t.length >= 4))]);

// Toda palavra precisa aparecer; vale mais no título, depois na descrição, depois no corpo, e a expressão inteira ganha bônus.
function pontuar(docs, termos, frase) {
  const achados = [];
  for (const d of docs) {
    let total = 0;
    for (const w of termos) {
      const re = padrao(w);
      const conta = (s) => (s.match(re) || []).length;
      const p = (conta(d.f.titulo) ? PESOS.titulo : 0) + (conta(d.f.descricao) ? PESOS.descricao : 0) + Math.min(5, Math.log2(1 + conta(d.f.texto)));
      if (!p) { total = 0; break; }
      total += p;
    }
    if (!total) continue;
    if (termos.length > 1 && `${d.f.titulo} ${d.f.descricao} ${d.f.texto}`.includes(frase)) total += 8;
    achados.push({ d, total });
  }
  return achados.sort((a, b) => b.total - a.total).map((a) => a.d);
}

// Busca exata primeiro; só quando ela não acha nada, cada palavra ausente do corpus troca pela mais parecida (medido: A2).
function buscar(docs, q) {
  const termos = palavras(q);
  if (!termos.length) return { docs: [], termos, corrigido: false };
  const exatos = pontuar(docs, termos, termos.join(' '));
  if (exatos.length) return { docs: exatos, termos, corrigido: false };
  const v = vocabulario(docs);
  const trocados = termos.map((w) => (v.some((t) => t.includes(w)) ? w : parecida(w, v) || w));
  return { docs: pontuar(docs, trocados, trocados.join(' ')), termos: trocados, corrigido: trocados.some((t, i) => t !== termos[i]) };
}

// Um trecho de ~160 caracteres em volta da primeira ocorrência, com os termos marcados.
function trecho(d, termos) {
  let pos = -1;
  for (const w of termos) { const m = padrao(w).exec(d.f.texto); if (m && (pos < 0 || m.index < pos)) pos = m.index; }
  const p = document.createElement('p');
  p.className = 'trecho';
  if (pos < 0) { p.textContent = d.descricao; return p; }
  const ini = Math.max(0, pos - 60);
  const fim = Math.min(d.texto.length, pos + 100);
  marcar(p, d.texto.slice(ini, fim).replace(/\s+/g, ' '), termos, ini > 0, fim < d.texto.length);
  return p;
}

// Escreve `texto` em `alvo` como nós de texto, com cada ocorrência dos termos num <mark>.
function marcar(alvo, texto, termos, antes, depois) {
  const dobrado = dobra(texto);
  const faixas = [];
  for (const w of termos) for (const m of dobrado.matchAll(padrao(w))) faixas.push([m.index, m.index + m[0].length]);
  faixas.sort((a, b) => a[0] - b[0]);
  let i = 0;
  if (antes) alvo.append('… ');
  for (const [a, b] of faixas) {
    if (a < i) continue;
    alvo.append(texto.slice(i, a));
    const mk = document.createElement('mark');
    mk.textContent = texto.slice(a, b);
    alvo.append(mk);
    i = b;
  }
  alvo.append(texto.slice(i));
  if (depois) alvo.append(' …');
}

function resultados(painel, achado, q) {
  painel.replaceChildren();
  const aviso = (txt) => { const p = document.createElement('p'); p.className = 'estado'; p.textContent = txt; painel.append(p); };
  if (!achado.docs.length) { aviso(`Nenhum documento contém “${q}”.`); return; }
  const n = achado.docs.length;
  aviso(`${n > MAX ? `Mostrando ${MAX} de ${n} documentos; refine a busca para ver os demais.` : `${n} documento${n > 1 ? 's' : ''}`}${achado.corrigido ? ` para “${achado.termos.join(' ')}”` : ''}.`);
  const lista = document.createElement('ol');
  lista.className = 'achados';
  for (const d of achado.docs.slice(0, MAX)) {
    const li = document.createElement('li');
    const a = document.createElement('a');
    a.href = `?doc=${encodeURIComponent(d.doc)}&q=${encodeURIComponent(achado.termos.join(' '))}`;
    const t = document.createElement('b');
    t.textContent = d.titulo;
    a.append(t);
    li.append(a, trecho(d, achado.termos));
    lista.append(li);
  }
  painel.append(lista);
}

// Liga a caixa: carrega o índice no primeiro foco e mostra os resultados no painel, escondendo a página enquanto há busca.
function caixa(form, painel, pagina) {
  const campo = form.querySelector('input');
  let espera;
  const mostrar = async () => {
    const q = campo.value.trim();
    if (q.length < 2) { painel.hidden = true; pagina.hidden = false; return; }
    painel.hidden = false;
    pagina.hidden = true;
    try {
      if (!(indice instanceof Array)) { painel.replaceChildren(Object.assign(document.createElement('p'), { className: 'estado', textContent: 'Carregando o índice…' })); }
      const docs = await carregar();
      if (campo.value.trim() === q) resultados(painel, buscar(docs, q), q);
    } catch (e) {
      painel.replaceChildren();
      const p = Object.assign(document.createElement('p'), { className: 'estado aviso', textContent: `Não foi possível carregar o índice de busca (${e.message}). ` });
      const b = Object.assign(document.createElement('button'), { type: 'button', className: 'btn', textContent: 'Tentar de novo' });
      b.addEventListener('click', mostrar);
      p.append(b);
      painel.append(p);
    }
  };
  campo.addEventListener('focus', () => carregar().catch(() => {}), { once: true });
  campo.addEventListener('input', () => { clearTimeout(espera); espera = setTimeout(mostrar, 150); });
  form.addEventListener('submit', (e) => { e.preventDefault(); const a = painel.querySelector('.achados a'); if (a && !painel.hidden) location.href = a.href; });
}

// No documento aberto por um resultado (?q=), marca os termos nos nós de texto, abre os <details> em volta e rola até o primeiro.
function destacar(raiz, q) {
  const termos = palavras(q);
  if (!termos.length) return;
  const nos = [];
  const andar = document.createTreeWalker(raiz, NodeFilter.SHOW_TEXT);
  while (andar.nextNode()) nos.push(andar.currentNode);
  let primeiro = null;
  for (const no of nos) {
    if (!termos.some((w) => padrao(w).test(dobra(no.data)))) continue;
    const frag = document.createDocumentFragment();
    marcar(frag, no.data, termos, false, false);
    primeiro = primeiro || frag.querySelector('mark');
    no.replaceWith(frag);
  }
  if (!primeiro) return;
  for (let el = primeiro.parentElement; el && el !== raiz; el = el.parentElement) if (el.tagName === 'DETAILS') el.open = true;
  primeiro.scrollIntoView({ block: 'center' });
}
