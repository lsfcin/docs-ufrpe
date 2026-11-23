declare function dobra(s: any): any;
declare function perto(a: any, b: any, lim: any): boolean;
declare function parecida(w: any, vocabulario: any): any;
declare function carregar(raiz?: string): any;
declare function pontuar(docs: any, termos: any, frase: any): any[];
declare function buscar(docs: any, q: any): {
    docs: any[];
    termos: any;
    corrigido: any;
};
declare function trecho(d: any, termos: any): HTMLParagraphElement;
declare function marcar(alvo: any, texto: any, termos: any, antes: any, depois: any): void;
declare function grupos(docs: any, aberto: any): any[];
declare function vagas(tamanhos: any): any;
declare function resultados(painel: any, achado: any, q: any, aberto: any, raiz: any): void;
declare function caixa(form: any, painel: any, pagina: any, aberto: any, raiz: any): void;
declare function destacar(raiz: any, q: any): void;
declare const MAX: 20;
declare namespace PESOS {
    let titulo: number;
    let descricao: number;
}
declare function palavras(q: any): any;
declare function escapa(w: any): any;
declare function padrao(w: any): RegExp;
declare let indice: null;
declare let vocab: null;
declare function vocabulario(docs: any): any;
