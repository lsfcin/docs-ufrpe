# docs-ufrpe — Roadmap
> A v1 é toda a documentação, sem exceção (Lucas, 23/11/2026): todo documento que o censo marca como "entra" convertido, e toda pendência do ISSUES.md fechada. Um setor por rodada do `converter.py`, com o escopo já listado no censo.

## v1

- [ ] [lotes-censo] Converter, um tema por lote, cada link `entra` de [censo.tsv](censo.tsv) que ainda não tem `.md`, setor por setor (as contagens estão no README § censo). Pronto quando nenhum `entra` do censo ficar sem documento.
- [ ] [resolucoes-seg] Pôr no censo as resoluções do CONSU, CEPE e CURA, uma página da SEG cada (`seg.ufrpe.br/content/res-no-NNNAAAA`, com Ementa e Tipo). A busca por "resolução" acha 969, de 1997 a 2026, a maioria homologação, convênio ou ato sobre pessoas. O `vigiar.py` só lê links diretos; falta ler a página de cada resolução. Entram na v1 (Lucas, 23/11/2026). Pronto quando cada uma tem linha no censo.
- [ ] [propesq-proplad] Levantar PROPESQ (propesq.ufrpe.br) e PROPLAD (proplad.ufrpe.br) em [fontes.tsv](fontes.tsv): as home pages não têm link de documento, falta achar as páginas que listam. Entram na v1 (Lucas, 23/11/2026).
- [ ] [pendentes-censo] Nenhum link `pendente` no censo: cada um ganha `entra` ou `fora` com motivo, por [regras.py](.github/scripts/regras.py) ou à mão.
- [ ] [issues-abertas] Fechar cada item de [ISSUES.md](ISSUES.md), inclusive os que dependem de terceiros (AGU, MEC/DOU, Arquivo Nacional, Planalto).

## Rejected

- [entropia-portugues] Traduzir ou tirar do ISSUES o bloco de entropia em inglês: fica como está (Lucas, 23/11/2026).
