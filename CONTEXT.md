# docs-ufrpe
> Documentos oficiais da UFRPE em Markdown, um lote por vez (o 1º: progressão, promoção e PDA/RDA), cada um com a fonte oficial e a data de captura.

**O original manda; o Markdown é para ler e buscar.** Todo `.md` de documento começa com o mesmo frontmatter: `description`, `origin` (**sempre o link oficial** do original, num site da UFRPE ou do governo), `origin_checked` (data da conferência) e `sha256` do arquivo nesse link (`null` só nas páginas federais de link). `origin_note` diz, quando preciso, por onde mais o arquivo circulou. O original (PDF, DOC, DOCX) não entra no git. Sem link oficial, o documento não entra: a exceção é um espelho público no Drive do mantenedor, registrado aqui (hoje, nenhum). [`.github/scripts/verificar.py`](.github/scripts/verificar.py) confere tudo isso em cada PR; como contribuir: [README.md](README.md) § Quer ajudar?. O mantenedor commita direto em `main` (repo aninhado, fora do gate de git flow); terceiros contribuem por PR, e cada PR aberto vira entrada no INBOX até ser resolvido.

**Uma pasta por tipo de documento**, e o critério de cada uma está na descrição dela, na rota abaixo. As federais apontam para o espelho [ctresb/leis](https://github.com/ctresb/leis) fixado num commit, e só trazem o texto inteiro quando o espelho não o tem.

**Lote = escopo completo.** Um lote só entra quando todo o escopo foi listado antes de converter. Lote 1 (11/11/2026): progressão, promoção e PDA/RDA, a partir de [progepe.ufrpe.br/documentos](https://www.progepe.ufrpe.br/documentos) e dos e-mails da comissão PDA/RDA do DC. Lacunas conhecidas: [ISSUES.md](ISSUES.md).

**Fora daqui:** atos que tratam de pessoas (portarias individuais ou coletivas, processos) — mesmo publicados em boletim, vivem no acervo privado de cada docente.

**O site** [ufrpe.pages.dev/docs](https://ufrpe.pages.dev/docs/) é `site/` (viewer estático) mais os `.md` de `main`, dentro do projeto Cloudflare `ufrpe`, que também serve o montagrade. Um deploy substitui o projeto inteiro: publique só com `core/run tools/links/ufrpe-site`, que monta todas as partes do git; nunca `wrangler pages deploy` à mão.

Os servidores UFRPE não mandam o certificado intermediário: busque-o pela URL de AIA (GlobalSign RNP 2025) e passe `--cacert`; não desligue a verificação.

<!-- routing:start -->
## Routing

| Subdirectory | Description |
|--------------|-------------|
| [`modelos/`](modelos/CONTEXT.md) | Formulários e requerimentos oficiais em Markdown, tabelas preservadas; o original editável (.doc/.docx) fica no Drive, no mesmo caminho. |
| [`normas/`](normas/CONTEXT.md) | Resoluções do CONSU/CEPE e instruções normativas da UFRPE: atos gerais, com força de regra. As federais que elas aplicam ficam em `federais/`. |
| [`orientacoes/`](orientacoes/CONTEXT.md) | Ofícios-circulares, pareceres da AGU e orientações da PROGEPE: interpretam a regra, não a criam. Cada um vale pelo que diz e por quem assina. |
| [`tabelas/`](tabelas/CONTEXT.md) | Tabelas da PROGEPE: vencimentos do Magistério Superior e correlação de classes. Cada uma vale para o período no nome. |

| File | Interface | API | Description |
|------|-----------|-----|-------------|
| [`ISSUES.md`](ISSUES.md) | — | — | What is currently untrue that we know about in this repo: hand-written issues first, every measured number inside its own generated block. |
| [`README.md`](README.md) | — | — | Documentos oficiais da UFRPE em Markdown, cada um com o link oficial e a data de captura. |
| [`site/index.html`](site/index.html) | — | — | index.html — a porta do site do docs-ufrpe: carrega o viewer, que abre o README ou o documento em ?doc=. |
| [`site/jsconfig.json`](site/jsconfig.json) | — | — | ← add first-line comment |
| [`site/marked.min.js`](site/marked.min.js) | — | — | ← add first-line comment |
| [`site/viewer.css`](site/viewer.css) | — | — | viewer.css — a cara do docs-ufrpe: azul institucional, cartão do original oficial, tabelas largas com rolagem. |
| [`site/viewer.js`](site/viewer.js) | [`site/viewer.d.ts`](site/viewer.d.ts) | `cabecalho`, `cartao`, `trilha`, `relink` | viewer.js — mostra um .md do docs-ufrpe formatado: o cabeçalho vira o cartão do original oficial, e cada página leva ao GitHub para propor correção. |
<!-- routing:end -->
