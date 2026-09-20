#!/usr/bin/env python3
"""Controle de progresso da tradução (lê e escreve a tabela de STATUS.md).

Uso:
    python3 translations/pt-BR/progresso.py resumo               # quantos capítulos em cada estado
    python3 translations/pt-BR/progresso.py proximos [N]         # os N (padrão 1) próximos pendentes, um por linha
    python3 translations/pt-BR/progresso.py titulo <capitulo>    # título pt-BR oficial
    python3 translations/pt-BR/progresso.py marcar <capitulo> [🟨|✅|⬜]   # muda o status (padrão 🟨)

<capitulo> é o nome do arquivo sem .md (ex.: paging), o título em inglês ou o
título em português. "proximos" respeita a ordem do livro.
"""
import re
import sys
from pathlib import Path

AQUI = Path(__file__).resolve().parent
STATUS = AQUI / "STATUS.md"
LINHA = re.compile(r"^\| (⬜|🟨|✅) \| `([^`]+)\.md` \| (\d+) \| (.+?) \| (.+?) \| (\d+) \|\s*$")


def ler():
    """[(indice_da_linha, estado, arquivo, numero, en, pt, palavras)]"""
    itens = []
    for i, linha in enumerate(STATUS.read_text().split("\n")):
        m = LINHA.match(linha)
        if m:
            itens.append((i, m.group(1), m.group(2), m.group(3), m.group(4),
                          m.group(5), m.group(6)))
    if not itens:
        sys.exit("Nenhuma linha de capítulo reconhecida em STATUS.md (formato mudou?)")
    return itens


def achar(itens, chave):
    chave = chave.removesuffix(".md").strip().lower()
    for it in itens:
        if chave in (it[2].lower(), it[4].lower(), it[5].lower()):
            return it
    sys.exit(f"Capítulo não encontrado em STATUS.md: {chave!r}")


def main(argv):
    if not argv:
        print(__doc__)
        return 2
    cmd, args = argv[0], argv[1:]
    itens = ler()
    if cmd == "resumo":
        for emoji, nome in (("⬜", "pendentes"), ("🟨", "traduzidos"), ("✅", "revisados")):
            sel = [it for it in itens if it[1] == emoji]
            print(f"{emoji} {nome}: {len(sel)} capítulos, {sum(int(x[6]) for x in sel)} palavras")
    elif cmd == "proximos":
        n = int(args[0]) if args else 1
        for it in [it for it in itens if it[1] == "⬜"][:n]:
            print(it[2])
    elif cmd == "titulo":
        print(achar(itens, " ".join(args))[5])
    elif cmd == "marcar":
        if not args:
            sys.exit("uso: marcar <capitulo> [🟨|✅|⬜]")
        novo = args[1] if len(args) > 1 else "🟨"
        if novo not in ("⬜", "🟨", "✅"):
            sys.exit("status deve ser ⬜, 🟨 ou ✅")
        it = achar(itens, args[0])
        linhas = STATUS.read_text().split("\n")
        linhas[it[0]] = linhas[it[0]].replace(f"| {it[1]} |", f"| {novo} |", 1)
        STATUS.write_text("\n".join(linhas))
        print(f"{it[2]}.md: {it[1]} -> {novo}")
    else:
        print(__doc__)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
