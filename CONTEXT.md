# docs-ufrpe
> Documentos oficiais que um docente da UFRPE usa para tramitar progressão, promoção e PDA/RDA, em Markdown, cada um com a fonte oficial e a data de captura.

**O original manda; o Markdown é para ler e buscar.** Cada `<pasta>/<nome>/<nome>.md` traz no cabeçalho `origin` (URL oficial ou o e-mail institucional que distribuiu), `origin_checked` (data da captura) e `sha256` do original. O original (PDF, DOC, DOCX) não entra no git: mora no Drive do mantenedor, no mesmo caminho.

**Uma pasta por tipo de documento**, e o critério de cada uma está na descrição dela, na rota abaixo. As federais apontam para o espelho [ctresb/leis](https://github.com/ctresb/leis) fixado num commit, e só trazem o texto inteiro quando o espelho não o tem.

**Lote = escopo completo.** Um lote só entra quando todo o escopo foi listado antes de converter. Lote 1 (11/11/2026): progressão, promoção e PDA/RDA, a partir de [progepe.ufrpe.br/documentos](https://www.progepe.ufrpe.br/documentos) e dos e-mails da comissão PDA/RDA do DC. Lacunas conhecidas: [ISSUES.md](ISSUES.md).

**Fora daqui:** atos que tratam de pessoas (portarias individuais ou coletivas, processos) — mesmo publicados em boletim, vivem no acervo privado de cada docente.

Os servidores UFRPE não mandam o certificado intermediário: busque-o pela URL de AIA (GlobalSign RNP 2025) e passe `--cacert`; não desligue a verificação.

<!-- routing:start -->
## Routing

| Subdirectory | Description |
|--------------|-------------|
| [`modelos/`](modelos/CONTEXT.md) | Formulários e requerimentos oficiais em Markdown, tabelas preservadas; o original editável (.doc/.docx) fica no Drive, no mesmo caminho. |
| [`normas/`](normas/CONTEXT.md) | Resoluções do CONSU/CEPE e instruções normativas da UFRPE: atos gerais, com força de regra. As federais que elas aplicam ficam em `federais/`. |
| [`orientacoes/`](orientacoes/CONTEXT.md) | Ofícios-circulares, pareceres da AGU e orientações da PROGEPE: interpretam a regra, não a criam. Cada um vale pelo que diz e por quem assina. |
| [`tabelas/`](tabelas/CONTEXT.md) | Tabelas da PROGEPE: vencimentos do Magistério Superior e correlação de classes. Cada uma vale para o período no nome. |

| File | Description |
|------|-------------|
| [`ISSUES.md`](ISSUES.md) | What is currently untrue that we know about in this repo: hand-written issues first, every measured number inside its own generated block. |
| [`README.md`](README.md) | docs-ufrpe |
<!-- routing:end -->
