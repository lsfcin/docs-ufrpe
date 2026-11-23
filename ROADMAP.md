# docs-ufrpe — Roadmap
> A v1 é toda a documentação, sem exceção (Lucas, 23/11/2026): todo documento que o censo marca como "entra" convertido, e toda pendência do ISSUES.md fechada. Um lote por sessão, cada um com o escopo listado antes de converter.

## v1

- [ ] [lotes-censo] Converter, um tema por lote, cada link `entra` de [censo.tsv](censo.tsv) que ainda não tem `.md`: PROGEPE, Reitoria, PRPG e PREG (as contagens estão no README § censo). Pronto quando nenhum `entra` do censo ficar sem documento.
- [ ] [setores-faltantes] Levantar PRExC, PRAE e os conselhos (SOC) em [fontes.tsv](fontes.tsv) e rodar `vigiar.py --gravar`. Pronto quando os três têm linha no censo do README.
- [ ] [pendentes-censo] Nenhum link `pendente` no censo: cada um ganha `entra` ou `fora` com motivo, por [regras.py](.github/scripts/regras.py) ou à mão.
- [ ] [issues-abertas] Fechar cada item de [ISSUES.md](ISSUES.md), inclusive os que dependem de terceiros (AGU, MEC/DOU, Arquivo Nacional, Planalto).

## Rejected

- [entropia-portugues] Traduzir ou tirar do ISSUES o bloco de entropia em inglês: fica como está (Lucas, 23/11/2026).
