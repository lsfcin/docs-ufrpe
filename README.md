# docs-ufrpe
> Documentos oficiais da UFRPE em Markdown, cada um com o link oficial e a data de captura.

Catálogo de **resoluções**, **instruções normativas**, **orientações**, **formulários**, **calendários** e **tabelas** da **UFRPE**, em formato Markdown (.md), para facilitar a consulta pelo celular e por ferramentas de inteligência artificial. Versão formatada para leitura: [ufrpe.pages.dev/docs](https://ufrpe.pages.dev/docs/).

Cada documento traz o link para o arquivo oficial. Em caso de divergência, prevalece o original. Este não é um site oficial da UFRPE e o acervo ainda é parcial: a ausência de um documento não significa que ele não exista. "Conferido em" é a data em que o texto foi comparado com o original, não garantia de que o documento ainda vale.

**Pergunte a uma IA.** O [caderno do NotebookLM](https://ufrpe.pages.dev/docs/notebook/) já tem o acervo inteiro e responde citando o documento e o artigo (requer conta Google). Em outra IA (ChatGPT, Claude, Gemini), cole o endereço da página aberta no site, que já traz o texto inteiro, ou [ufrpe.pages.dev/docs/acervo.md](https://ufrpe.pages.dev/docs/acervo.md), todos os documentos num arquivo só, com a data e o índice no topo. Confira a resposta no original.

## Organização

| Pasta | Conteúdo |
|---|---|
| [`normas/`](normas/CONTEXT.md) | Resoluções dos conselhos superiores e instruções normativas; as leis federais que elas aplicam ficam em `federais/` |
| [`orientacoes/`](orientacoes/CONTEXT.md) | Ofícios, pareceres, manuais e mapas de processo sobre como aplicar as normas |
| [`modelos/`](modelos/CONTEXT.md) | Formulários e requerimentos |
| [`calendarios/`](calendarios/CONTEXT.md) | Calendários acadêmicos em vigor |
| [`tabelas/`](tabelas/CONTEXT.md) | Vencimentos e correlação entre as classes da carreira |

## Documentos disponíveis e pendentes

O objetivo é reunir todo documento da UFRPE de interesse geral, setor por setor. O que cada setor publica, link a link, está em [censo.tsv](censo.tsv); a tabela abaixo resume esse censo, e a coluna **Convertidos** diz quantos desses documentos já estão no acervo:

<!-- censo:start -->
Contado em 24/11/2026 por [vigiar.py](.github/scripts/vigiar.py), um link por arquivo; um arquivo publicado por dois setores conta no primeiro deles. "Convertidos" conta os que já estão no acervo, fora os atos federais; "Entram" os conta. As fontes e o motivo de cada exclusão estão em cada setor, logo abaixo da tabela.

| Setor | Convertidos | Entram | Fora | Pendentes |
|---|---|---|---|---|
| Reitoria | 10 de 10 | 13 | 49 | — |
| PREG | 0 de 78 | 78 | 37 | 1 |
| PRPG | 76 de 77 | 80 | 30 | — |
| PROGESTI | 0 de 46 | 46 | 2 | — |
| PROGEPE | 17 de 443 | 458 | 25 | 1 |
| SEG | 8 de 8 | 8 | 6 | — |

<details>
<summary>Reitoria: fontes e motivos</summary>

- **Fonte:** [/documentos-e-relatórios-ufrpe](https://ufrpe.br/documentos-e-relat%C3%B3rios-ufrpe/), [/br/capr](https://www.uast.ufrpe.br/br/capr)
- **Entram:** formulários (5), normas (6, 3 federais), orientações (2)
- **Ficam de fora:** relatório (42), versão superada (4), cópia: o original está na PROGEPE (3)

</details>
<details>
<summary>PREG: fontes e motivos</summary>

- **Fonte:** [preg.ufrpe.br](https://preg.ufrpe.br/), 15 páginas ([fontes.tsv](fontes.tsv))
- **Entram:** calendários (1), formulários (41), normas (22), orientações (14)
- **Ficam de fora:** memória de reunião (21), versão superada (16)
- **Pendentes:** sem motivo (1)

</details>
<details>
<summary>PRPG: fontes e motivos</summary>

- **Fonte:** [/resolucoes](https://prpg.ufrpe.br/resolucoes), [/pt-br/resolucoes-revogadas](https://prpg.ufrpe.br/pt-br/resolucoes-revogadas), [/formularios](https://prpg.ufrpe.br/formularios)
- **Entram:** calendários (1), formulários (28), normas (45, 3 federais), orientações (6)
- **Ficam de fora:** revogada (26), relatório (3), divulgação (1)

</details>
<details>
<summary>PROGESTI: fontes e motivos</summary>

- **Fonte:** [www.progesti.ufrpe.br](https://www.progesti.ufrpe.br/), 6 páginas ([fontes.tsv](fontes.tsv))
- **Entram:** formulários (14), normas (32)
- **Ficam de fora:** procedimento específico (1), ato sobre pessoas (1)

</details>
<details>
<summary>PROGEPE: fontes e motivos</summary>

- **Fonte:** [/documentos](https://www.progepe.ufrpe.br/documentos)
- **Entram:** formulários (266), normas (89, 15 federais), orientações (76), tabelas (27)
- **Ficam de fora:** ato sobre pessoas (20), procedimento específico (5)
- **Pendentes:** sem motivo (1)

</details>
<details>
<summary>SEG: fontes e motivos</summary>

- **Fonte:** [seg.ufrpe.br](https://seg.ufrpe.br/), 4 páginas ([fontes.tsv](fontes.tsv))
- **Entram:** formulários (5), normas (2), orientações (1)
- **Ficam de fora:** divulgação (6)

</details>
<!-- censo:end -->

A PROExC não publica lista de documentos (23/11/2026). As resoluções do CONSU, do CEPE e do CURA ficam cada uma numa página da SEG, achada só pela busca dela, e ainda não entraram no censo.

A inclusão de cada tema começa pelo levantamento de todos os seus documentos, seguido da conversão para Markdown.

<details>
<summary>Como cada documento é conferido</summary>

Todo arquivo começa com um cabeçalho, oculto no site: `origin` é o link oficial, `origin_checked` é a data da conferência e `sha256` é a impressão digital do arquivo oficial. Se a UFRPE substituir o arquivo, a impressão digital deixa de coincidir e a divergência é detectada. As conferências pendentes estão em [ISSUES.md](ISSUES.md).

</details>

## Sugerir correções e documentos

Documentos ausentes, links quebrados e erros no texto podem ser corrigidos pelo navegador, sem instalar programas. Para propor um documento, informe o **link oficial** num site da UFRPE ou do governo. Um documento recebido por e-mail deve ser procurado antes no site do setor que o publicou; se não estiver publicado, abra uma *issue* com o nome do documento e o remetente.

Entram os documentos que regem atividades de aplicação geral, inclusive os calendários acadêmicos e os formulários que qualquer pessoa reusa. Não entram os que abrem, conduzem ou encerram um procedimento específico (um concurso, uma seleção, uma chamada), os documentos sobre pessoas (portarias individuais, processos) nem dados pessoais, como CPF ou SIAPE.

<details>
<summary>Passo a passo para propor um documento novo</summary>

1. Abra a pasta certa: `normas/`, `orientacoes/`, `modelos/`, `calendarios/` ou `tabelas/`.
2. Clique em **Add file → Create new file** (adicionar arquivo → criar arquivo novo; o GitHub mostra os botões em inglês) e dê um nome como `<nome>/<nome>.md`, em minúsculas e com hífens: `res-consu-123-2025-assunto/res-consu-123-2025-assunto.md`.
3. Comece o arquivo com este cabeçalho e cole o texto embaixo:

```markdown
---
description: "Uma frase: o que o documento é e para que serve."
origin: "https://www.progepe.ufrpe.br/sites/default/files/.../arquivo.pdf"
origin_checked: "2026-11-13"
sha256: "64 letras e números do arquivo baixado de origin"
---

# Título do documento

(o texto do documento)
```

4. Clique em **Commit changes → Propose changes → Create pull request** (gravar a mudança → propor → abrir o pedido). O GitHub conclui o envio.

Para corrigir um documento que já existe, abra o `.md`, clique no lápis, corrija e proponha da mesma forma.

</details>

<details>
<summary>Como calcular o sha256</summary>

Baixe o arquivo do link oficial e rode `sha256sum arquivo.pdf` (Linux ou Mac) ou `certutil -hashfile arquivo.pdf SHA256` (Windows). Se não for possível, escreva `sha256: null` e informe no pedido; o mantenedor completa.

</details>

<details>
<summary>Depois do envio</summary>

Uma verificação automática confere o cabeçalho, a pasta e se o `sha256` bate com o arquivo do link; o resultado aparece no próprio pedido. Em seguida, o mantenedor compara o texto com o original e aceita a proposta. As listas de cada pasta se atualizam automaticamente.

</details>

## Licença

Os atos oficiais não são protegidos por direito autoral (Lei 9.610/1998, art. 8º, IV). A edição deste acervo (conversão, organização e descrições) está sob [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/deed.pt-br), e o código (`site/`, `.github/`), sob a [licença MIT](https://opensource.org/license/mit). O texto das três: [LICENSE](LICENSE).

Como o repositório se organiza por dentro: [CONTEXT.md](CONTEXT.md).
