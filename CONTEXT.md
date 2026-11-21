# docs-ufrpe
> Documentos oficiais da UFRPE em Markdown, um lote por vez (o 1º: progressão, promoção e PDA/RDA), cada um com a fonte oficial e a data de captura.

**O original manda; o Markdown é para ler e buscar.** Todo `.md` de documento começa com o mesmo frontmatter: `description`, `origin` (**sempre o link oficial** do original, num site da UFRPE ou do governo), `origin_checked` (data da conferência) e `sha256` do arquivo nesse link (`null` só nas páginas federais de link). `origin_note` diz, quando preciso, por onde mais o arquivo circulou. O original (PDF, DOC, DOCX) não entra no git. Sem link oficial, o documento não entra: a exceção é um espelho público no Drive do mantenedor, registrado aqui (hoje, nenhum). [`.github/scripts/verificar.py`](.github/scripts/verificar.py) confere tudo isso em cada PR; como contribuir: [README.md](README.md) § Sugerir correções e documentos. O mantenedor segue o git flow do workspace (repo aninhado, governado desde 19/11/2026); terceiros contribuem por PR, e cada PR aberto vira entrada no INBOX até ser resolvido.

**Uma pasta por tipo de documento**, e o critério de cada uma está na descrição dela, na rota abaixo. As federais apontam para o espelho [ctresb/leis](https://github.com/ctresb/leis) fixado num commit, e só trazem o texto inteiro quando o espelho não o tem. O `CONTEXT.md` de cada pasta é também a página dela no site: abre explicando a seção a quem chega, e nota de mantenedor não entra ali. Um modelo .doc/.docx se converte subindo ao Drive como Google Doc temporário e voltando por `gdocs read`, que mantém as tabelas (`docx text` as perde).

**Lote = escopo completo.** Um lote só entra quando todo o escopo foi listado antes de converter. Lote 1 (11/11/2026): progressão, promoção e PDA/RDA, a partir de [progepe.ufrpe.br/documentos](https://www.progepe.ufrpe.br/documentos) e dos e-mails da comissão PDA/RDA do DC. Lacunas conhecidas: [ISSUES.md](ISSUES.md).

**Dentro:** o que rege atividades de aplicação geral, calendários acadêmicos e formulários reusáveis inclusive. **Fora daqui:** o que abre, conduz ou encerra um procedimento específico (edital de concurso, seleção, chamada), e atos que tratam de pessoas (portarias individuais ou coletivas, processos) — mesmo publicados em boletim, vivem no acervo privado de cada docente. Critério de 19/11/2026, com o painel.

**O site** [ufrpe.pages.dev/docs](https://ufrpe.pages.dev/docs/) é `site/` (viewer estático) mais os `.md` de `main`, dentro do projeto Cloudflare `ufrpe`, que também serve o montagrade. Um deploy substitui o projeto inteiro: publique só com `academy/administration/ufrpe-sites/publicar.py` (repo do mantenedor), que monta todas as partes do git; nunca `wrangler pages deploy` à mão. A busca lê `busca.json`, que o deploy gera com [`.github/scripts/indexar.py`](.github/scripts/indexar.py) e que não entra no git; a tolerância a erro de digitação só age quando a busca exata não acha nada (medido contra a exata e o MiniSearch em 18/11/2026). Os achados vêm agrupados pela pasta aberta, do nível mais fundo ao resto do acervo, com as 20 vagas divididas entre os grupos; Enter não abre resultado. O mesmo `indexar.py` grava `acervo.md` (o acervo numa URL, para IA). Quem não roda JavaScript recebe o `.md` da página dentro do HTML: a Pages Function `lib/texto.js` do site das disciplinas (outputs/links), a mesma nos dois sites.

Os servidores UFRPE filtram o User-Agent de curl e não mandam o certificado intermediário: baixe por [`rede.py`](.github/scripts/rede.py), que manda UA de navegador e acha o intermediário pela URL de AIA de cada servidor (no curl: `-A` de navegador e `--cacert`); não desligue a verificação. O censo: [`fontes.tsv`](fontes.tsv) → [`vigiar.py`](.github/scripts/vigiar.py) → [`censo.tsv`](censo.tsv), triado por [`regras.py`](.github/scripts/regras.py).

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
| [`site/busca.js`](site/busca.js) | [`site/busca.d.ts`](site/busca.d.ts) | `dobra`, `perto`, `parecida`, `carregar`, `pontuar` | busca.js — a caixa "Buscar nos documentos" do docs-ufrpe: lê o busca.json do deploy, acha sem acento nem maiúscula, tolera um erro de digitação e destaca o termo no documento aberto. |
| [`site/index.html`](site/index.html) | — | — | index.html — a porta do site do docs-ufrpe: carrega o viewer, que abre o README ou o documento em ?doc=. O texto do .md já vem dentro de #app para quem não roda JavaScript (lib/texto.js, no deploy). |
| [`site/jsconfig.json`](site/jsconfig.json) | — | — | Diz ao editor que o viewer.js do docs-ufrpe é JavaScript de navegador, sem checagem de tipos. |
| [`site/viewer.css`](site/viewer.css) | — | — | viewer.css — a cara do docs-ufrpe: faixa azul-marinho oficial (#1b2d4f) com o brasão em negativo, Work Sans, listas só com linhas horizontais. |
| [`site/viewer.js`](site/viewer.js) | [`site/viewer.d.ts`](site/viewer.d.ts) | `cabecalho`, `figuras`, `cartao`, `trilha`, `relink` | viewer.js — mostra um .md do docs-ufrpe formatado: faixa com o brasão em negativo, cartão do original oficial, listas legíveis e o caminho para propor correção no GitHub. |
<!-- routing:end -->
