# docs-ufrpe — Roadmap
> A v1 é toda a documentação, sem exceção (Lucas, 23/11/2026): todo documento que o censo marca como "entra" convertido, e toda pendência do ISSUES.md fechada. Um setor por rodada do `converter.py`, com o escopo já listado no censo.

## v1

- [ ] [figuras-por-tipo] Descrever figura só onde ela tem conteúdo: manual e tutorial (capturas de tela) sim; norma, formulário e tabela, cujas figuras são brasão, logo e assinatura, não. Medido em 24/11/2026: 127 chamadas de visão em série, mediana de 31 s; o Manual de identidade visual levou ~35 min e o PDI passou de 60 min sem terminar. Na projeção, o resto do censo leva ~25 h assim. Pede ao `tools/pdf/pymupdf` um `--describer none` (repo do workspace) e ao `converter.py` a escolha por tipo. Antes do PDI e do Plano de Integridade (Reitoria), que ficaram por converter. [src: agent 2026-11-24]
- [ ] [lotes-censo] Converter, um tema por lote, cada link `entra` de [censo.tsv](censo.tsv) que ainda não tem `.md`, setor por setor (o que falta é a coluna "Convertidos" do README). Pronto quando nenhum `entra` do censo ficar sem documento.
- [ ] [federais-prpg] Os três atos federais que a PRPG publica e o `converter.py` deixou para a mão: a Lei 11.907/2009 vira uma linha na lista do espelho em [normas/federais/CONTEXT.md](normas/federais/CONTEXT.md); a Portaria CAPES 156/2014 e a Res. CNE 1/2018 entram em texto integral, da publicação oficial. [src: agent 2026-11-24]
- [ ] [espelho-no-acervo] O `/docs/acervo` (o que a IA e o caderno do NotebookLM leem) não tem o texto das leis que só estão no espelho. No deploy, o `indexar.py` pode puxar do ctresb/leis, no commit fixado, o `.md` de cada lei da lista de `normas/federais/`, sem guardá-lo no git (o painel argon, 24/11/2026). [src: agent 2026-11-24]
- [ ] [resolucoes-seg] Pôr no censo as resoluções do CONSU, CEPE e CURA, uma página da SEG cada (`seg.ufrpe.br/content/res-no-NNNAAAA`, com Ementa e Tipo). A busca por "resolução" acha 969, de 1997 a 2026, a maioria homologação, convênio ou ato sobre pessoas. O `vigiar.py` só lê links diretos; falta ler a página de cada resolução. Entram na v1 (Lucas, 23/11/2026). Pronto quando cada uma tem linha no censo.
- [ ] [propesq-proplad] Levantar PROPESQ e PROPLAD em [fontes.tsv](fontes.tsv). Páginas achadas em 25/11/2026: PROPESQ `/documentos-da-pesquisa/` (13 arquivos: regimento, normas de grupo de pesquisa, estrutura) e `/relatorio-gestao-propesq/` (relatórios, a maioria `fora`); PROPLAD `/organogramas-regimentos-e-resolucoes/` e `/documentos-e-relatorios/` (ambas "em construção"), `/mapa-estrategico-proplad/`; Ouvidoria `/content/normativos-e-legislacao-aplicaveis-a-ouvidoria` no `ww2.ouvidoria.ufrpe.br`. Entram na v1 (Lucas, 23/11/2026).
- [ ] [organograma-ordem] Pôr os setores na ordem do menu do ufrpe.br (Reitoria; PREG, PRPG, PROPESQ, PROExC, PROGESTI, PROGEPE, PROPLAD; SEG; demais órgãos) em [fontes.tsv](fontes.tsv), com a linha de rodapé "varridos, sem documentos" e a data. Varredura de 25/11/2026: Procuradoria Federal (`/pfufrpe/`) e Biblioteca (sib.ufrpe.br) sem arquivo listado. `proexc.ufrpe.br` falha no `rede.py` com `CERTIFICATE_VERIFY_FAILED` (o AIA não resolve o intermediário): consertar antes de ler as duas páginas da PROExC (`/novo-regimento-da-proexc/`, `/prestacao-de-contas-e-relatorios/`). A página das pró-reitorias diz "seis", e o menu lista sete. [src: agent 2026-11-25]
- [ ] [pendentes-censo] Nenhum link `pendente` no censo: cada um ganha `entra` ou `fora` com motivo, por [regras.py](.github/scripts/regras.py) ou à mão.
- [ ] [issues-abertas] Fechar cada item de [ISSUES.md](ISSUES.md), inclusive os que dependem de terceiros (AGU, MEC/DOU, Arquivo Nacional, Planalto).

## Depois da v1

- [ ] [dc-docs] Um projeto irmão para o DC (Departamento de Computação): os documentos que só valem para ele, os fluxos e os guias, com o não oficial separado do oficial, e link para o docs-ufrpe nas normas gerais em vez de cópia. Decidir depois da v1, reusando o motor daqui (Lucas e o painel, 24/11/2026: abrir agora dobraria a manutenção). [src: agent 2026-11-24]

## Rejected

- [entropia-portugues] Traduzir ou tirar do ISSUES o bloco de entropia em inglês: fica como está (Lucas, 23/11/2026).
