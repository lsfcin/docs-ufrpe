# docs-ufrpe — Pendências
> O que sabemos que ainda não está certo neste acervo: primeiro as pendências escritas à mão, e cada número medido dentro do seu próprio bloco gerado.

## Lote 1 ainda não completo

- [ ] [parecer-agu-00002-2024] O requerimento de acerto financeiro cita o Parecer 00002/2024/CFEDU/SUBCONSU/PGF/AGU, que a PROGEPE não publica. Achar a fonte oficial e converter. Pista (18/11/2026): outras universidades citam o parecer, como a UNIFESSPA na Publica nº 77-2024; nenhuma é fonte oficial da AGU. Pedir à PROGEPE ou procurar no Sapiens da AGU.
- [ ] [portaria-normativa-mec-10-2014] Altera a Portaria MEC 982/2013; não capturada.
- [ ] [mec-554-982-dou] As Portarias MEC 554/2013 e 982/2013 vieram de cópias da UFRRJ, não do DOU (in.gov.br): conferir com a publicação oficial. Em 22/11/2026 a busca do in.gov.br não indexa 2013 e o SRU do LexML não achou as duas; falta a página do DOU (pesquisa.in.gov.br, por data e página). A Lei 15.367/2026 (art. 120) passou a comissão de Titular a 75% de externos "nos termos de ato do Ministro": conferir se a 982/2013 foi substituída.
- [ ] [censo-pendentes-mortos] Dois links seguem `pendente` no censo.tsv porque o arquivo não abre: PREG `Forum de Licenciaturas.pdf` (ww2.preg.ufrpe.br não responde desde 21/11/2026) e PROGEPE `Licença Gestante e Prorrogação.pdf` (sugep.ufrpe.br, 404 em 23/11/2026). Ler o arquivo quando voltar, ou pedir ao setor o link novo, e decidir.
- [ ] [gestao-documental-federal] Na Reitoria, a metodologia, o código de classificação e a tabela de temporalidade da atividade-fim são do Arquivo Nacional (gov.br, Portaria AN 92/2011), e o de atividade-meio aponta para um link quebrado (`https://cod_classif_tab_temp_ativ_meio_atualizacao_2024.pdf/`). Entram como federais, pela regra do espelho; falta o link vivo da atividade-meio.
- [ ] [piloto-prpg] Lote PRPG convertido inteiro (74 de 78 `entra`; o resto está em `.vigia/fila.tsv`: 3 federais e `formulario.xls`, para o mantenedor). Falta: (a) 15 `description` ainda rascunho (`… (PRPG).`): `python .github/scripts/descrever.py --setor PRPG --limite 5`, em lotes, em primeiro plano (em 24/11/2026 o processo levou SIGKILL duas vezes, a máquina sem memória); depois padronizar o Nome das normas no formato do lote 1 (`Res. CEPE 609/2023`, `IN PRPG 01/2026`: saíram `Res. CEPE/UFRPE`, `Resolução CEPE`, `IN UFRPE/PRPG`) e trocar "Anexo III – Ficha de identificação" e "Formulário padrão" por nomes do documento; (b) merge em `main` e o `publicar.py` do ufrpe-sites (Lucas autorizou publicar em 24/11/2026); (c) depois de publicar, reimportar `/docs/acervo` no NotebookLM (Lucas). [src: agent 2026-11-24]
- [ ] [pasta-458] `normas/res-458-2023-processo` é a Res. CONSU 458/2024 (equidade de gênero): o nome veio do arquivo do processo. Renomear para `res-consu-458-2024-equidade-genero` (pasta, .md, .pdf e `source`); a URL já publicada pede redirect em `site/_redirects`. [src: agent 2026-11-24]
- [ ] [plano-quebras] `normas/plano-internacionalizacao` repete texto na virada de página (a revisão por argon, 24/11/2026): p. 14 (fim do parágrafo do CGRIFES/FAUBAI/GCUB), p. 37 (início do item 4 de 3.1.2), p. 43 (título "2) Garantia de Acessibilidade…" e "O Núcleo de Internacionalização…"), p. 51 (item 4, Feira), p. 53 ("extensão dos programas de pós-graduação da UFRPE."), p. 87 (referência à Res. CONSU 027/2020, com a URL corrompida); na p. 84 o título 5.2, o parágrafo dela e o início da Tabela 10 se fundiram na Tabela 9; p. 74 e 84 perdem hífen (`Destacase`). Corrigir contra o PDF.
- [ ] [escaneados-sem-revisao] Quatro normas do PRPG são PDF escaneado, sem texto a comparar, e não passaram pela revisão: `res-006-2015`, `res-108-2016`, `res-cepe-208-2014`, `res-cepe-953-2025-bolsa`. Conferir o OCR contra a página renderizada (`core/run tools/pdf/pymupdf <pdf> --review`).
- [ ] [correcao-a-mao] Nada marca no `.md` que ele tem correção à mão (Res. 009 Anexo III, Res. 042 revogada, notas do parecer AGU, `res-cepe-059-2020`, o calendário PRPG reescrito): um `converter.py --refazer` ou `pymupdf --force` apaga a correção sem avisar. O twin precisa de um campo (o `reviewed_by` já existe e é o candidato) que faça o motor recusar sobrescrever sem `--force` explícito no arquivo, e o `--refazer` pular esses. [src: agent 2026-11-24]
- [ ] [calendario-vigente] O censo marca `entra` três calendários acadêmicos do PREG (2024-2025, 2025 e 2026); só o vigente deve entrar, e a regra de `regras.py` deixa passar quem tem o ano anterior no nome. [src: agent 2026-11-24]
- [ ] [entropia-caminho] O bloco de entropia abaixo diz escanear `academy/administration/docs-ufrpe`, o caminho de antes da mudança para `code/`. [src: agent 2026-11-23]
- [ ] [indice-32-31] Em 23/11/2026, `make verify-full` indexou 32 documentos na cópia de trabalho e o `publicar.py` indexou 31 a partir do `main`, com a árvore limpa. Achar qual `.md` o índice local conta e o deploy não. [src: agent 2026-11-23]
- [ ] [planalto-timeout] `planalto.gov.br` não responde desta máquina; as federais apontam para `normas.leg.br` (LexML).

<!-- entropy:start -->
## Entropy

> Generated by `core/hooks/entropy/dashboard/entropy-dashboard.py`, which scans `academy/administration/docs-ufrpe` and no other. Never edit inside this block, and never copy a count out of it — a copied number is the drift these checks exist to catch.

2026-11-19 · 61 tracked files scanned · **6 findings here**

| Check | Findings |
|-------|----------|
| Off-allowlist `.md` types | 0 |
| CONTEXT.md hand-written inventories | 0 |
| Naming and placement | 0 |
| Routing tables pointing at files git does not carry | 0 |
| Projects not declaring their goal | 0 |
| Wiki-links naming nothing | 3 |
| Retired tokens still alive | 0 |
| Roadmap item numbers cited outside a roadmap | 0 |
| Items claimed by two lists | 0 |
| Size signals | 0 |
| Source files with no interface stub | 0 |
| Directories holding too many files | 0 |
| Prose describing finished work | 1 |
| Unanswered placeholders | 0 |
| Doubt stores missing their own discipline | 0 |
| Lists naming a model where they mean a level | 0 |
| Header fields naming code that is not there | 0 |
| Truncated routing descriptions | 0 |
| Constraints trapped in a CONTEXT.md head | 0 |
| Local branches holding unpromoted work | 0 |
| Work that exists on this disk and nowhere else | 0 |
| Local branches already merged into their base | 1 |
| Remote branches already merged into their base | 1 |

*A check with no findings is the `0` in that table and nothing more. Only a check with something to show gets a section below.*

### Wiki-links naming nothing

*a [[name]] is a goal file or an item in one*

- ISSUES.md: [[14]] names no goal file and no item in one.
- ISSUES.md: [[name]] names no goal file and no item in one.
- orientacoes/parecer-agu-00038-2023-progressao-docente/parecer-agu-00038-2023-progressao-docente.md: [[14]] names no goal file and no item in one.

### Prose describing finished work

*git is the history — cut it, or rewrite it as present-tense state*

- normas/res-consu-009-2019-progressao-promocao-2024-12/res-consu-009-2019-progressao-promocao-2024-12.md:1105: strikethrough — prose describing finished work.

### Local branches already merged into their base

*safe to delete, and purely local — `git -C <repo> branch -d <branch>`*

- . — 1 merged into main: git -C . branch -d feature/contribuicoes

### Remote branches already merged into their base

*safe to delete, and outward-facing — `git -C <repo> push origin --delete <branch>`, Lucas*

- . — 1 merged into main: git -C . push origin --delete feature/contribuicoes

<!-- entropy:end -->
