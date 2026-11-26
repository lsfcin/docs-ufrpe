# docs-ufrpe — Pendências
> O que sabemos que ainda não está certo neste acervo: primeiro as pendências escritas à mão, e cada número medido dentro do seu próprio bloco gerado.

## Abertas

- [ ] [parecer-agu-00002-2024] O requerimento de acerto financeiro cita o Parecer 00002/2024/CFEDU/SUBCONSU/PGF/AGU, que a PROGEPE não publica. Achar a fonte oficial e converter. Pista (18/11/2026): outras universidades citam o parecer, como a UNIFESSPA na Publica nº 77-2024; nenhuma é fonte oficial da AGU. Pedir à PROGEPE ou procurar no Sapiens da AGU.
- [ ] [portaria-normativa-mec-10-2014] Altera a Portaria MEC 982/2013; não capturada.
- [ ] [mec-554-982-dou] As Portarias MEC 554/2013 e 982/2013 vieram de cópias da UFRRJ, não do DOU (in.gov.br): conferir com a publicação oficial. Em 22/11/2026 a busca do in.gov.br não indexa 2013 e o SRU do LexML não achou as duas; falta a página do DOU (pesquisa.in.gov.br, por data e página). A Lei 15.367/2026 (art. 120) passou a comissão de Titular a 75% de externos "nos termos de ato do Ministro": conferir se a 982/2013 foi substituída.
- [ ] [censo-pendentes-mortos] Dois links seguem `pendente` no censo.tsv porque o arquivo não abre: PREG `Forum de Licenciaturas.pdf` (ww2.preg.ufrpe.br não responde desde 21/11/2026) e PROGEPE `Licença Gestante e Prorrogação.pdf` (sugep.ufrpe.br, 404 em 23/11/2026). Ler o arquivo quando voltar, ou pedir ao setor o link novo, e decidir.
- [ ] [gestao-documental-federal] Na Reitoria, a metodologia, o código de classificação e a tabela de temporalidade da atividade-fim são do Arquivo Nacional (gov.br, Portaria AN 92/2011), e o de atividade-meio aponta para um link quebrado (`https://cod_classif_tab_temp_ativ_meio_atualizacao_2024.pdf/`). Entram como federais em texto integral, porque o espelho não cobre portarias; falta o link vivo da atividade-meio.
- [ ] [notebook-prpg] O caderno do NotebookLM ainda lê o `/docs/acervo` de antes do lote PRPG, porque a fonte passou de 500 mil palavras. O deploy já gera os volumes (`/docs/acervo-1`…, 4 em 26/11/2026): falta publicar e, no caderno, trocar a fonte antiga por um volume em cada fonte. [src: agent 2026-11-26]
- [ ] [plano-quebras] `normas/plano-internacionalizacao` repete texto na virada de página (a revisão por argon, 24/11/2026): p. 14 (fim do parágrafo do CGRIFES/FAUBAI/GCUB), p. 37 (início do item 4 de 3.1.2), p. 43 (título "2) Garantia de Acessibilidade…" e "O Núcleo de Internacionalização…"), p. 51 (item 4, Feira), p. 53 ("extensão dos programas de pós-graduação da UFRPE."), p. 87 (referência à Res. CONSU 027/2020, com a URL corrompida); na p. 84 o título 5.2, o parágrafo dela e o início da Tabela 10 se fundiram na Tabela 9; p. 74 e 84 perdem hífen (`Destacase`). Corrigir contra o PDF.
- [ ] [escaneados-sem-revisao] Sete documentos são PDF escaneado ou têm figura lida por OCR, e não passaram pela revisão: `res-006-2015`, `res-108-2016`, `res-cepe-208-2014`, `res-cepe-953-2025-bolsa` (PRPG), `regimento-conselhos-superiores` e `estatuto-regimento-geral` (SEG, OCR ruim no corpo: "Ill" por "III", letras trocadas) e `in-gr-01-2024-duvidas-frequentes` (Reitoria, o texto das capturas de tela do SIPAC). Conferir o OCR contra a página renderizada (`core/run tools/pdf/pymupdf <pdf> --review`).
- [ ] [entropia-caminho] O bloco de entropia abaixo diz escanear `academy/administration/docs-ufrpe`, o caminho de antes da mudança para `code/`. [src: agent 2026-11-23]
- [ ] [formulario-matricula-xls] O último `entra` da PRPG é o Formulário de Matrícula em planilha (`prpg.ufrpe.br/sites/default/files/formularios/formulario.xls`): o `converter.py` não tem rota para planilha. A skill `sheets` do workspace lê Google Sheets: subir o `.xls` como planilha e ler de volta, como o `.docx` faz pelo `gdocs`. [src: agent 2026-11-24]
- [ ] [lote-preg-falhas] Do lote PREG ficaram de fora: `REQUERIMENTO cpga.pdf` (ww2.preg não responde), `DRCA_TUTORIAL_ACESSO AO SIGA (1).pdf` (404) e a `Ficha cadastral - 2016` (.docx), cujo `gdocs read` volta vazio (o `converter.py` agora recusa o corpo vazio). [src: agent 2026-11-25]
- [ ] [gemeo-docx-teto] Três modelos PREG em .docx (`ppc-licenciatura-presencial`, `novo-ppc-bacharelado-tecnologo`, `plano-retorno-atividades-presenciais-curso-prapc`) estão convertidos, mas fora do git, em `.git/info/exclude`: o gate de tamanho só isenta o gêmeo de PDF, que tem `source: ../<stem>.pdf` (`core/tools/pdf/pdf_meta.py:is_twin`). Os três já têm `source: ../<stem>.docx`, que o `converter.py` grava; falta o `is_twin` do workspace aceitar `.doc/.docx` (nota `[twin-docx]` no outbox do workspace, 26/11/2026). Depois disso, tirar as linhas do exclude e fazer o commit. [src: agent 2026-11-25]
- [ ] [progepe-normas-revisao] Do lote de normas da PROGEPE (26/11/2026) sobram: sete links que o `converter.py` deixou em `.vigia/fila.tsv` como "mesmo ato" (quatro da Res. CONSU 127/2018 e um de cada uma das Res. CONSU 009/2019, 117/2016 e 715/2026), para dobrar no `origin_note` ou converter com `--apesar-do-nome`; um 404; e a revisão por risco (todo escaneado, OCR e tabela, mais 10% do resto). O `in-04-2019` e o `in-87-2020` tinham a ligadura "fi"/"ti" perdida no PDF (`per�l`), trocada à mão. [src: agent 2026-11-26]
- [ ] [federais-progepe] Treze atos federais da PROGEPE (11 decretos, a Portaria MEC 658/2026 e o Ofício-Circular MEC 30/2022, mais o manual SIGEPE do Decreto 9.727/2019) esperam Lucas escolher a fonte: o PDF que a PROGEPE hospeda, convertido (rápido, sha256 verificável, mas em geral a cópia compilada do Planalto), ou a publicação original (Câmara/DOU) transcrita à mão. O ofício e o manual são orientação, não norma. O painel não respondeu em 26/11/2026 (memória e tempo esgotados). Nove INs federais (SGP/ME, MGI, TCU, Conjunta) o `regras.py` marcou `norma`, não `federal`: entraram pelo PDF da PROGEPE e foram movidas à mão para `normas/federais/`; a escolha da fonte vale para elas também, e o `regras.py` deveria reconhecer IN de órgão federal. Sete descrições da PROGEPE seguem rascunho (o deepseek estourou o tempo): `descrever.py --setor PROGEPE`. [src: agent 2026-11-26]
- [ ] [planalto-timeout] `planalto.gov.br` não responde desta máquina; o texto de um ato federal vem da publicação original na Câmara (`camara.leg.br/legin`), e o `normas.leg.br` (LexML) só monta a página por JavaScript.
- [ ] [mec-dns] `portal.mec.gov.br` não resolve no DNS desta máquina (25 e 26/11/2026), e o `gov.br/mec`, para onde o CNE migrou, devolve um desafio de JavaScript (F5) no lugar do PDF. Os 16 atos do CNE em `normas/federais/` têm por `origin` a cópia do PDF do MEC no Wayback, achada pelo digest do índice CDX. Quando o MEC voltar, trocar o `origin` pelo link do MEC, se o `sha256` bater. O PDF da Res. CNE/CP 1/2019 tem XRef quebrada no próprio MEC: o corpo foi conferido pelo Ghostscript. [src: agent 2026-11-26]

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
