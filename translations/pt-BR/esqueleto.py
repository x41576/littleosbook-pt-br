#!/usr/bin/env python3
"""Extrai um capítulo como esqueleto (sem código) e remonta depois de traduzido.

Os blocos de código do livro (Makefiles com tabs, linker scripts, diagramas de
bits alinhados) não devem ser redigitados: erro de um espaço já é diferença. Por
isso o fluxo é:

    python3 translations/pt-BR/esqueleto.py extrair paging
        -> translations/pt-BR/trabalho/paging.md   (original em inglês; cada bloco
           de código vira uma linha  @@CODIGO n@@ )
    (traduzir a prosa para translations/pt-BR/trabalho/paging.pt.md, mantendo as
     linhas @@CODIGO n@@ exatamente onde estão, cada uma sozinha na linha)
    python3 translations/pt-BR/esqueleto.py montar paging
        -> translations/pt-BR/capitulos/paging.md  (marcadores trocados pelos
           blocos originais, byte a byte)

`montar` recusa o esqueleto se faltar, sobrar ou estiver fora de ordem algum
marcador, ou se um marcador não estiver sozinho na linha.
"""
import re
import sys
from pathlib import Path

import validar
from validar import MARCA_CODIGO, RAIZ, dividir

TRABALHO = Path(__file__).resolve().parent / "trabalho"


def curto(caminho):
    """Caminho relativo à raiz do repositório, quando possível (para mensagens)."""
    try:
        return caminho.relative_to(RAIZ)
    except ValueError:
        return caminho


MARCADOR = re.compile(r"^@@CODIGO (\d+)@@$")


def extrair(nome):
    origem = RAIZ / f"{nome}.md"
    if not origem.exists():
        sys.exit(f"não existe o original {curto(origem)}")
    prosa, blocos = dividir(origem.read_text())
    partes, n = [], 0
    for linha in prosa.split("\n"):
        if linha == MARCA_CODIGO:
            n += 1
            linha = f"@@CODIGO {n}@@"
        partes.append(linha)
    TRABALHO.mkdir(exist_ok=True)
    destino = TRABALHO / f"{nome}.md"
    destino.write_text("\n".join(partes))
    print(f"{curto(destino)}: {len(blocos)} blocos de código viraram marcadores")
    for i, b in enumerate(blocos, 1):
        print(f"  @@CODIGO {i}@@  {len(b.splitlines()):>3} linhas  {validar.resumo_do_bloco(b)}")


def montar(nome):
    _, blocos = dividir((RAIZ / f"{nome}.md").read_text())
    fonte = TRABALHO / f"{nome}.pt.md"
    if not fonte.exists():
        sys.exit(f"não existe {curto(fonte)}")
    saida, vistos, problemas = [], [], []
    for numero, linha in enumerate(fonte.read_text().split("\n"), 1):
        m = MARCADOR.match(linha)
        if m:
            k = int(m.group(1))
            vistos.append(k)
            if not 1 <= k <= len(blocos):
                problemas.append(f"linha {numero}: marcador {k} não existe (há {len(blocos)} blocos)")
                continue
            saida.append(blocos[k - 1])
            continue
        if "@@CODIGO" in linha:
            problemas.append(f"linha {numero}: marcador fora do formato exato "
                             f"'@@CODIGO n@@' sozinho na linha: {linha!r}")
        saida.append(linha)
    esperado = list(range(1, len(blocos) + 1))
    if vistos != esperado:
        faltam = sorted(set(esperado) - set(vistos))
        sobram = sorted(k for k in set(vistos) if vistos.count(k) > 1)
        if faltam:
            problemas.append(f"marcadores que faltam: {faltam}")
        if sobram:
            problemas.append(f"marcadores repetidos: {sobram}")
        if not faltam and not sobram:
            problemas.append(f"marcadores fora de ordem: {vistos}")
    if problemas:
        print(f"ERRO ao montar {nome}:")
        for p in problemas:
            print(f"  {p}")
        return 1
    destino = validar.TRADUCAO / f"{nome}.md"
    destino.parent.mkdir(parents=True, exist_ok=True)
    destino.write_text("\n".join(saida))
    print(f"{curto(destino)}: montado com {len(blocos)} blocos de código originais")
    return 0


def main(argv):
    if len(argv) != 2 or argv[0] not in ("extrair", "montar"):
        print(__doc__)
        return 2
    nome = argv[1].removesuffix(".md").split("/")[-1]
    if argv[0] == "extrair":
        extrair(nome)
        return 0
    return montar(nome)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
