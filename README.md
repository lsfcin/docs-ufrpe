# docs-ufrpe
> Documentos oficiais da UFRPE em Markdown, cada um com o link oficial e a data de captura.

Catálogo de **resoluções**, **instruções normativas**, **ofícios**, **formulários** e **tabelas** da **UFRPE**, em formato Markdown (.md), para facilitar a consulta pelo celular e por ferramentas de inteligência artificial. Versão formatada para leitura: [ufrpe.pages.dev/docs](https://ufrpe.pages.dev/docs/).

Cada documento traz o link para o arquivo oficial. Em caso de divergência, prevalece o original. Este não é um site oficial da UFRPE e o acervo ainda é parcial: a ausência de um documento não significa que ele não exista. "Conferido em" é a data em que o texto foi comparado com o original, não garantia de que o documento ainda vale.

**Para uma IA** (NotebookLM, ChatGPT): cole o endereço da página aberta no site, que já traz o texto inteiro, ou [ufrpe.pages.dev/docs/acervo.md](https://ufrpe.pages.dev/docs/acervo.md), todos os documentos num arquivo só, com a data e o índice no topo. A cópia importada não se atualiza: importe de novo depois de uma mudança.

## Organização

| Pasta | Conteúdo |
|---|---|
| [`normas/`](normas/CONTEXT.md) | Resoluções dos conselhos superiores e instruções normativas; as leis federais que elas aplicam ficam em `federais/` |
| [`orientacoes/`](orientacoes/CONTEXT.md) | Ofícios, pareceres e orientações da PROGEPE (Pró-Reitoria de Gestão de Pessoas) sobre como aplicar as normas |
| [`modelos/`](modelos/CONTEXT.md) | Formulários e requerimentos |
| [`tabelas/`](tabelas/CONTEXT.md) | Vencimentos e correlação entre as classes da carreira |

## Documentos disponíveis e pendentes

O objetivo é reunir todo documento da UFRPE de interesse geral. Hoje estão disponíveis os de **progressão e promoção docente** e de **PDA** e **RDA** (Plano Docente de Atividades e Relatório Docente de Atividades). O que cada setor publica, link a link, está em [censo.tsv](censo.tsv):

<!-- censo:start -->
Contado em 21/11/2026 por [vigiar.py](.github/scripts/vigiar.py), um link por arquivo; um arquivo publicado por dois setores conta no primeiro deles.

| Setor | Fonte | Entram | Ficam de fora | Pendentes |
|---|---|---|---|---|
| PROGEPE | [/documentos](https://www.progepe.ufrpe.br/documentos) | formulários (290), normas (85, 25 federais), orientações (75), tabelas (27) | ato sobre pessoas ou seleção (6) | contado à mão: o servidor apresenta um certificado inválido desde 21/11/2026 |
| Reitoria | [/documentos-e-relatórios-ufrpe](https://ufrpe.br/documentos-e-relat%C3%B3rios-ufrpe/) | normas (6, 3 federais), orientações (1) | relatório (41), versão superada (4) | — |
| PRPG | [/resolucoes](https://prpg.ufrpe.br/resolucoes), [/pt-br/resolucoes-revogadas](https://prpg.ufrpe.br/pt-br/resolucoes-revogadas), [/formularios](https://prpg.ufrpe.br/formularios) | formulários (28), normas (46, 3 federais), orientações (6) | revogada (26), relatório (3), divulgação (1) | — |
| PREG | [preg.ufrpe.br](https://preg.ufrpe.br/), 15 páginas ([fontes.tsv](fontes.tsv)) | formulários (41), normas (25), orientações (14) | memória de reunião (21), versão superada (14) | sem motivo (1) |
<!-- censo:end -->

PRExC, PRAE e os conselhos (SOC) ainda não foram levantados.

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

1. Abra a pasta certa: `normas/`, `orientacoes/`, `modelos/` ou `tabelas/`.
2. Clique em **Add file → Create new file** e dê um nome como `<nome>/<nome>.md`, em minúsculas e com hífens: `res-consu-123-2025-assunto/res-consu-123-2025-assunto.md`.
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

4. Clique em **Commit changes → Propose changes → Create pull request**. O GitHub conclui o envio.

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

Os atos oficiais não são protegidos por direito autoral (Lei 9.610/1998, art. 8º, IV). A edição deste acervo (conversão, organização e descrições) está sob [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/deed.pt-br), e o código (`site/`, `.github/`), sob a [licença MIT](https://opensource.org/license/mit).

Como o repositório se organiza por dentro: [CONTEXT.md](CONTEXT.md).
