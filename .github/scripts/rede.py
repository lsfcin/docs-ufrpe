# rede.py — como falar com os servidores da UFRPE: User-Agent de navegador e o certificado intermediário achado pela URL de AIA de cada servidor.
"""Os servidores da UFRPE não mandam o intermediário e cada um usa um diferente; o de AIA (caIssuers) vem dentro do
próprio certificado, que é lido sem verificar só para achar essa URL. O download segue verificado.
Eles também filtram o User-Agent: com o de curl, a PREG dá 502 depois de 90 s; com o de navegador, 200 em 0,6 s (21/11/2026).
Só stdlib, para a Action rodar sem instalar nada.
"""
from __future__ import annotations

import re
import ssl
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Callable

UA = 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0 Safari/537.36'
# A URL de caIssuers é um IA5String legível dentro do DER; a de OCSP e a de CRL não terminam em .crt/.cer/.p7c.
AIA = re.compile(rb'https?://(?:(?!https?://)[\x21-\x7e])+?\.(?:crt|cer|p7c)')
_contextos: dict[str, ssl.SSLContext] = {}
_intermediarios: dict[str, str] = {}


def intermediarios(host: str, porta: int = 443) -> list[str]:
    """As URLs de AIA do certificado que `host` apresenta, lido sem verificar."""
    pem = ssl.get_server_certificate((host, porta), timeout=20)
    return [u.decode() for u in AIA.findall(ssl.PEM_cert_to_DER_cert(pem))]


def contexto(host: str) -> ssl.SSLContext:
    """Um contexto que verifica `host` com as raízes do sistema mais o intermediário dele. Um por host, guardado."""
    if host in _contextos:
        return _contextos[host]
    ctx = ssl.create_default_context()
    try:
        urls = intermediarios(host)
    except OSError:
        urls = []
    for url in urls:
        try:
            if url not in _intermediarios:
                der = urllib.request.urlopen(url, timeout=20).read()
                _intermediarios[url] = der.decode() if der.startswith(b'-----') else ssl.DER_cert_to_PEM_cert(der)
            ctx.load_verify_locations(cadata=_intermediarios[url])
        except (OSError, ssl.SSLError, ValueError):
            pass
    _contextos[host] = ctx
    return ctx


def baixar(url: str, timeout: int = 60) -> bytes:
    """O conteúdo de `url`, com verificação e User-Agent de navegador. Levanta OSError quando falha."""
    host = urllib.parse.urlsplit(url).hostname or ''
    if url.startswith('http://') and host.endswith('ufrpe.br'):   # o 302 para https seria seguido sem o intermediário
        url = 'https://' + url[len('http://'):]
    pedido = urllib.request.Request(url, headers={'User-Agent': UA})
    ctx = contexto(host) if url.startswith('https://') else None
    with urllib.request.urlopen(pedido, timeout=timeout, context=ctx) as resposta:
        return resposta.read()


def normalizar(href: str, base: str) -> str:
    """O link absoluto, sem fragmento e com o caminho codificado de um jeito só (o mesmo arquivo, a mesma chave)."""
    partes = urllib.parse.urlsplit(urllib.parse.urljoin(base, href.strip()))
    caminho = urllib.parse.quote(urllib.parse.unquote(partes.path), safe="/:@!$&'()*+,;=-._~")
    return urllib.parse.urlunsplit((partes.scheme, partes.netloc.lower(), caminho, partes.query, ''))


def salvas(pasta: Path) -> Callable[[str], bytes]:
    """Um `baixar` que devolve a página salva pelo navegador cuja <link rel="canonical"> é a URL pedida."""
    paginas = {}
    for arquivo in pasta.glob('*.htm*'):
        texto = arquivo.read_bytes()
        if (m := re.search(rb'<link rel="canonical" href="([^"]+)"', texto)):
            paginas[normalizar(m.group(1).decode(), '')] = texto

    def ler(url: str) -> bytes:
        if (chave := normalizar(url, '')) not in paginas:
            raise OSError(f'sem página salva para {url}')
        return paginas[chave]
    return ler
