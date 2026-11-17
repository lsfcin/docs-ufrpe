# docs-ufrpe
> Documentos oficiais da UFRPE em Markdown, cada um com o link oficial e a data de captura.

Resoluções, instruções normativas, ofícios, formulários e tabelas da UFRPE, em texto simples. Dá para ler no celular, procurar uma palavra em todos ao mesmo tempo, copiar o artigo certo e colar numa IA sem perder nada. Para ler com tudo formatado: [ufrpe.pages.dev/docs](https://ufrpe.pages.dev/docs/).

Cada página tem um botão para o arquivo oficial. Se o texto daqui e o oficial divergirem, vale o oficial.

## Por onde começar

| Pasta | O que tem |
|---|---|
| [`normas/`](normas/CONTEXT.md) | As regras: resoluções dos conselhos e instruções normativas; as leis federais ficam dentro, em `federais/` |
| [`orientacoes/`](orientacoes/CONTEXT.md) | Como aplicar as regras: ofícios, pareceres e orientações da PROGEPE |
| [`modelos/`](modelos/CONTEXT.md) | Formulários e requerimentos |
| [`tabelas/`](tabelas/CONTEXT.md) | Salários e a correspondência entre as classes da carreira |

## O que já tem e o que falta

A ideia é juntar aqui todo documento da UFRPE que sirva a mais de uma pessoa. Por enquanto estão aqui os de **progressão e promoção docente** e os de **PDA/RDA** (Plano e Relatório Docente de Atividades). Ainda faltam:

- Calendário acadêmico
- Orientações às comissões de avaliação de progressão (CAPD)
- Estatuto e Regimento Geral
- Graduação: normas gerais, estágio, projetos pedagógicos dos cursos
- Afastamentos, licenças e capacitação docente
- Editais que se repetem todo ano (monitoria, extensão, iniciação científica)

Cada assunto entra completo, de uma vez: primeiro se lista tudo o que ele abrange, depois se converte.

<details>
<summary>Como cada documento é conferido</summary>

Todo arquivo começa com um cabeçalho escondido no site: `origin` é o link oficial, `origin_checked` é o dia em que foi conferido e `sha256` é a impressão digital do arquivo oficial. Se a UFRPE trocar o arquivo no site dela, a impressão digital deixa de bater e a gente fica sabendo. O que ainda falta conferir está em [ISSUES.md](ISSUES.md).

</details>

## Quer ajudar?

Achou um documento que falta, um link quebrado ou um erro no texto? Dá para propor a correção pelo navegador, sem instalar nada. Só uma regra: todo documento precisa do **link oficial** de onde saiu, num site da UFRPE ou do governo. Se você recebeu o documento por e-mail, procure-o antes no site do setor que o publicou. Se ele não estiver publicado em lugar nenhum, abra uma *issue* dizendo o nome do documento e quem o mandou.

Documentos sobre pessoas (portarias individuais, processos) não entram, nem dados pessoais como CPF ou SIAPE.

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

4. Clique em **Commit changes → Propose changes → Create pull request**. O GitHub faz o resto.

Para corrigir um documento que já existe, abra o `.md`, clique no lápis, corrija e proponha do mesmo jeito.

</details>

<details>
<summary>Como calcular o sha256</summary>

Baixe o arquivo do link oficial e rode `sha256sum arquivo.pdf` (Linux ou Mac) ou `certutil -hashfile arquivo.pdf SHA256` (Windows). Se não conseguir, escreva `sha256: null` e avise no pedido; o mantenedor completa.

</details>

<details>
<summary>O que acontece depois que você propõe</summary>

Uma verificação automática confere o cabeçalho, a pasta e se o `sha256` bate com o arquivo do link; o resultado aparece no próprio pedido. Depois o mantenedor compara o texto com o original e aceita. As listas de cada pasta se atualizam sozinhas: não precisa mexer nelas.

</details>

Como o repositório se organiza por dentro: [CONTEXT.md](CONTEXT.md).
