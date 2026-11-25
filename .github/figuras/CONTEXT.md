# figuras
> O perfil de relevância de figura deste acervo: quais figuras de um PDF valem uma chamada ao modelo de visão. A ferramenta geral `core/tools/pdf` não traz pesos; este perfil é passado a ela.
> spec: none

**Uso.** O [`converter.py`](../scripts/converter.py) já passa esta pasta: `core/run tools/pdf/pymupdf <pdf> --relevance code/docs-ufrpe/.github/figuras`. À mão, a mesma flag. Sem ela, a ferramenta descreve toda figura não decorativa (mais lento, e descreve também o que este perfil pularia). O formato de um perfil está no cabeçalho de [`pdf_relevance.py`](../../../../core/tools/pdf/pdf_relevance.py).

**O que há aqui.** `relevance.tsv`: pesos e limiar, treinados em 366 figuras de 48 PDFs do acervo (25/11/2026; sensibilidade 0,982 com o documento de fora, 58% das figuras puladas). `decorations.txt`: o hash dos brasões e logos rotulados decorativos. `boilerplate.txt`: as palavras do timbre. Critério dos rótulos: relevante é o que o texto e o OCR não entregam (tela, fluxograma, organograma, tabela ou formulário em imagem, ícone citado em tutorial); brasão, logo, QR, assinatura, foto de capa, não.

**Retreinar** (rótulos e recortes ficam locais, em `.vigia/relevancia/v2/`): corrigir `labels.tsv` vendo `core/run tools/pdf/bench/relevance_sheet.py code/docs-ufrpe/.vigia/relevancia/v2 code/docs-ufrpe/.github/figuras`, depois `core/run tools/pdf/bench/relevance_train.py code/docs-ufrpe/.vigia/relevancia/v2 --write code/docs-ufrpe/.github/figuras`. Os pesos se editam retreinando, não à mão.

<!-- routing:start -->
## Routing

| File | Description |
|------|-------------|
| [`boilerplate.txt`](boilerplate.txt) | Palavras que o timbre dos documentos da UFRPE repete: a parcela delas no OCR de uma figura é o sinal `boilerplate` de core/tools/pdf/pdf_relevance.py. Uma por linha. |
| [`decorations.txt`](decorations.txt) | Looks (256-bit average hash, hex) of figures labelled decorative by bench/relevance_train.py. |
<!-- routing:end -->
