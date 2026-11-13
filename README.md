# docs-ufrpe
> Documentos oficiais da UFRPE sobre progressão, promoção e PDA/RDA docente, em Markdown, cada um com o link oficial e a data de captura.

Resoluções, instruções normativas, ofícios, pareceres, formulários e tabelas que um docente da UFRPE usa para progressão, promoção e PDA/RDA, convertidos para Markdown. Assim dá para ler no celular, buscar uma palavra em todos de uma vez e citar o artigo certo.

**O original sempre manda.** Todo documento começa com um cabeçalho: `origin` é o link oficial do arquivo, `origin_checked` é a data em que foi conferido e `sha256` é a impressão digital do arquivo. Na dúvida, abra o link.

## Onde está cada coisa

| Pasta | O que tem |
|---|---|
| [`normas/`](normas/CONTEXT.md) | Resoluções do CONSU/CEPE e instruções normativas; as leis federais em `normas/federais/` |
| [`orientacoes/`](orientacoes/CONTEXT.md) | Ofícios-circulares, pareceres da AGU e orientações da PROGEPE |
| [`modelos/`](modelos/CONTEXT.md) | Formulários e requerimentos |
| [`tabelas/`](tabelas/CONTEXT.md) | Vencimentos e correlação de classes |

O que ainda falta ou está por conferir: [ISSUES.md](ISSUES.md). Como o repositório se organiza por dentro: [CONTEXT.md](CONTEXT.md).

## Quer ajudar?

Achou um documento que falta, um link quebrado ou um erro no texto? Qualquer pessoa pode propor pelo navegador, sem instalar nada. Um PR entra rápido quando traz duas coisas: o **texto em Markdown** e o **link oficial** do arquivo de onde ele saiu.

### A regra única: link oficial sempre

Todo documento aponta para o arquivo original publicado num site oficial (`*.ufrpe.br`, `gov.br`, `in.gov.br`, `normas.leg.br`). Se você recebeu o documento por e-mail, procure-o antes no site do setor que o emitiu (PROGEPE, PREG, CPPD, uma unidade acadêmica). Se ele não estiver publicado em lugar nenhum, abra uma *issue* em vez de um PR, com o nome do documento e quem o distribuiu.

### Pelo navegador, sem instalar nada

1. Abra a pasta certa: `normas/` (resoluções e instruções normativas), `orientacoes/` (ofícios, pareceres, orientações), `modelos/` (formulários) ou `tabelas/` (tabelas da PROGEPE).
2. **Add file → Create new file** e escreva o nome como `<nome>/<nome>.md`, em minúsculas e com hífens: `res-consu-123-2025-assunto/res-consu-123-2025-assunto.md`.
3. Comece o arquivo com o cabeçalho e cole o texto embaixo:

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

4. **Commit changes → Propose changes → Create pull request.** O GitHub cria a sua cópia e o PR sozinho.

Para corrigir um documento que já existe, abra o `.md`, clique no lápis, corrija e proponha do mesmo jeito.

### O sha256

É a impressão digital do arquivo: prova que o texto saiu daquele arquivo e avisa quando o site o troca. Para calcular, baixe o arquivo do link e rode `sha256sum arquivo.pdf` (Linux/Mac) ou `certutil -hashfile arquivo.pdf SHA256` (Windows). Se não conseguir, deixe `sha256: null` e diga no PR; o mantenedor completa.

### O que acontece depois

Uma verificação automática confere o cabeçalho, a pasta e se o `sha256` bate com o arquivo do link. O resultado aparece no próprio PR. Depois o mantenedor revisa o texto contra o original e faz o merge. As tabelas dos `CONTEXT.md` se atualizam sozinhas: não as edite.

**Fora daqui:** atos sobre pessoas (portarias individuais, processos), mesmo publicados em boletim. Dados pessoais (CPF, SIAPE) nunca.
