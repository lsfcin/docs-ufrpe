declare function cabecalho(texto: any): {
    campos: {};
    corpo: any;
};
declare function figuras(md: any): any;
declare function cartao(c: any): string;
declare function trilha(doc: any): any;
declare function relink(raiz: any, doc: any): void;
declare function rotulo(a: any, desc: any): any[];
declare function tabelas(raiz: any): void;
declare function topo(doc: any): string;
declare function ligarBusca(app: any): void;
declare const REPO: "https://github.com/lsfcin/docs-ufrpe";
declare namespace PASTAS {
    let orientacoes: string;
}
declare namespace TRAD {
    let Subdirectory: string;
    let File: string;
    let Description: string;
    let Routing: string;
}
declare function esc(s: any): string;
declare function data(iso: any): any;
declare function nomePasta(p: any): any;
