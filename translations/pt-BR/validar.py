#!/usr/bin/env python3
"""Confere se a tradução de um capítulo preservou a estrutura do original.

Uso:
    python3 translations/pt-BR/validar.py virtual_memory        # um capítulo
    python3 translations/pt-BR/validar.py paging user_mode      # vários
    python3 translations/pt-BR/validar.py --todos                # tudo que já foi traduzido
    python3 translations/pt-BR/validar.py --glossario            # só confere o GLOSSARIO.md
    python3 translations/pt-BR/validar.py --ids paging           # ids {#...} que cada título traduzido deve levar
    python3 translations/pt-BR/validar.py --blocos paging        # mostra como o arquivo foi dividido em prosa/código

Compara <capitulo>.md (raiz do repositório) com
translations/pt-BR/capitulos/<capitulo>.md.

ERRO  = algo que quebraria o build, apagou conteúdo ou viola o glossário.
        Precisa ser corrigido.
AVISO = suspeito (ex.: trecho que parece ainda estar em inglês). Vale conferir.

Código de saída: 0 sem erros, 1 com erros.

Variável de ambiente TRADUCAO_DIR sobrescreve a pasta das traduções (para testes).
"""
import os
import re
import sys
import unicodedata
from collections import Counter
from pathlib import Path

AQUI = Path(__file__).resolve().parent
RAIZ = AQUI.parents[1]
TRADUCAO = Path(os.environ.get("TRADUCAO_DIR", AQUI / "capitulos"))
GLOSSARIO = AQUI / "GLOSSARIO.md"

CERCA = re.compile(r"^\s*(~{3,}|`{3,})")
RECUO = re.compile(r"^(?: {4}|\t)")
MARCA_CODIGO = "\u2063CODIGO\u2063"  # marcador invisível no lugar de cada bloco

CABECALHO = re.compile(r"^(#{1,6})\s+(.*?)\s*$")
ID_EXPLICITO = re.compile(r"\s*\{#([^}\s]+)\}\s*$")
INLINE_CODE = re.compile(r"`[^`]{1,200}`")
AUTOLINK = re.compile(r"<((?:https?|ftp)://[^>\s]+)>")
URL_INLINE = re.compile(r"\]\(([^)\s]+)(?:\s+\"[^\"]*\")?\)")
CITACAO = re.compile(r"\[@([^\]\s,;]+)")
NOTA = re.compile(r"\[\^([^\]]+)\]")
SEPARADOR_TABELA = re.compile(r"^\s*-{3,}(?:\s+-{3,})*\s*$")
ITEM_LISTA = re.compile(r"^\s*(?:[-*+]|\d+\.)\s+", re.M)
ESCAPE = re.compile(r"\\[_*#\[\]<>`\\$]")
ENFASE = re.compile(r"(?<![\w\\])_[^_]+?_(?![\w])", re.S)
IMAGEM = re.compile(r"!\[(.*?)\]\(", re.S)

PALAVRAS_INGLES = {"the", "and", "of", "is", "that", "with", "for", "this",
                   "are", "you", "we", "our", "it", "to", "in", "but", "not",
                   "have", "will", "your", "can", "what", "which"}


# ---------------------------------------------------------------- estrutura

def ordem_dos_capitulos():
    """Lê CHAPTERS do Makefile: a ordem importa para os ids gerados pelo Pandoc."""
    texto = (RAIZ / "Makefile").read_text()
    m = re.search(r"^CHAPTERS\s*=\s*((?:.*\\\n)*.*)$", texto, re.M)
    itens = m.group(1).replace("\\\n", " ").split()
    return [i[:-3] for i in itens if i.endswith(".md")]


def dividir(texto):
    """Devolve (prosa, blocos_de_codigo).

    Blocos de código são os cercados por ~~~/``` e os recuados em 4 espaços que
    começam depois de uma linha em branco. Na prosa, cada bloco vira MARCA_CODIGO
    (uma linha). Cada bloco é devolvido em texto bruto, com as linhas de cerca
    (`~~~ {.nasm}`) e o recuo originais; é o que o esqueleto.py reinjeta.
    """
    linhas = texto.split("\n")
    n, i = len(linhas), 0
    prosa, blocos = [], []
    anterior_em_branco = True
    while i < n:
        linha = linhas[i]
        m = CERCA.match(linha)
        if m:
            tipo = m.group(1)[0]
            j, corpo = i + 1, [linha]
            while j < n and not (CERCA.match(linhas[j])
                                 and linhas[j].strip().startswith(tipo * 3)):
                corpo.append(linhas[j])
                j += 1
            if j < n:
                corpo.append(linhas[j])  # cerca de fechamento
            blocos.append("\n".join(corpo))
            prosa.append(MARCA_CODIGO)
            i, anterior_em_branco = j + 1, False
            continue
        if anterior_em_branco and linha.strip() and RECUO.match(linha):
            j, corpo = i, []
            while j < n and (RECUO.match(linhas[j]) or not linhas[j].strip()):
                corpo.append(linhas[j])
                j += 1
            while corpo and not corpo[-1].strip():  # devolve as linhas em branco finais
                corpo.pop()
                j -= 1
            blocos.append("\n".join(corpo))
            prosa.append(MARCA_CODIGO)
            i, anterior_em_branco = j, False
            continue
        prosa.append(linha)
        anterior_em_branco = not linha.strip()
        i += 1
    return "\n".join(prosa), blocos


def normalizar_espacos(s):
    return " ".join(s.split())


def sem_acentos(s):
    return "".join(c for c in unicodedata.normalize("NFKD", s)
                   if not unicodedata.combining(c))


def texto_do_titulo(t):
    """Texto do título como o Pandoc o vê ao gerar o id (sem formatação)."""
    t = re.sub(r"`([^`]*)`", r"\1", t)
    t = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", t)
    t = re.sub(r"\\(.)", r"\1", t)
    return re.sub(r"[*_]", "", t)


def id_base(titulo):
    """Algoritmo de ids automáticos do Pandoc (docs: 'Extension: auto_identifiers')."""
    t = texto_do_titulo(titulo).strip().lower().replace(" ", "-")
    t = re.sub(r"[^\w.\-]", "", t)  # \w é unicode; sobra letras, dígitos, _ - .
    t = re.sub(r"^[^a-z]+", "", t)
    return t or "section"


def ids_esperados():
    """{capitulo: [(nivel, id), ...]} para o livro inteiro, na ordem do Makefile.

    Ids repetidos ganham sufixo -1, -2... contando o documento todo, por isso os
    títulos traduzidos levam o id explícito ({#id}) em vez de depender do Pandoc.
    """
    vistos, saida = set(), {}
    for nome in ordem_dos_capitulos():
        lista = []
        prosa, _ = dividir((RAIZ / f"{nome}.md").read_text())
        for linha in prosa.split("\n"):
            m = CABECALHO.match(linha)
            if not m:
                continue
            base = cand = id_base(m.group(2))
            k = 0
            while cand in vistos:
                k += 1
                cand = f"{base}-{k}"
            vistos.add(cand)
            lista.append((len(m.group(1)), cand))
        saida[nome] = lista
    return saida


def cabecalhos(prosa):
    """[(nivel, texto, id_declarado)] para as linhas '# ...'."""
    saida = []
    for linha in prosa.split("\n"):
        m = CABECALHO.match(linha)
        if not m:
            continue
        corpo = m.group(2)
        a = ID_EXPLICITO.search(corpo)
        corpo = ID_EXPLICITO.sub("", corpo).strip()
        saida.append((len(m.group(1)), corpo, a.group(1) if a else None))
    return saida


def limpar_prosa(prosa):
    """Só o texto a ser lido: sem código, URLs, citações, notas e marcadores."""
    p = prosa.replace(MARCA_CODIGO, " ")
    p = INLINE_CODE.sub(" ", p)
    p = AUTOLINK.sub(" ", p)
    p = re.sub(r"\]\([^)]*\)", "]", p)
    p = CITACAO.sub("[", p)
    p = re.sub(r"\[\^[^\]]+\]:?", " ", p)
    return ID_EXPLICITO.sub("", p)


# ---------------------------------------------------------------- glossário

class Termo:
    def __init__(self, ingles, portugues, evitar, manter):
        self.ingles, self.portugues, self.evitar, self.manter = \
            ingles, portugues, evitar, manter


def _alternativas(celula):
    celula = re.sub(r"\(.*?\)", "", celula)  # notas entre parênteses não fazem parte do termo
    return [a.strip() for a in celula.split(" / ")
            if a.strip() and a.strip() not in {"-", "—", "="}]


def carregar_glossario():
    """Lê as tabelas de GLOSSARIO.md. Devolve (termos, problemas)."""
    termos, problemas = [], []
    if not GLOSSARIO.exists():
        return termos, [f"não existe {GLOSSARIO.relative_to(RAIZ)}"]
    colunas = None
    for n, linha in enumerate(GLOSSARIO.read_text().split("\n"), 1):
        if not linha.lstrip().startswith("|"):
            colunas = None
            continue
        celulas = [c.strip() for c in linha.strip().strip("|").split("|")]
        if colunas is None:
            colunas = [c.lower() for c in celulas]
            continue
        if all(re.fullmatch(r":?-{2,}:?", c) for c in celulas if c):
            continue
        d = dict(zip(colunas, celulas))
        if "inglês" not in d:
            continue
        if len(celulas) != len(colunas):
            problemas.append(f"GLOSSARIO.md:{n}: {len(celulas)} colunas, esperado "
                             f"{len(colunas)} ('|' dentro de uma célula?)")
            continue
        ing = _alternativas(d["inglês"])
        if "português" in d:
            manter, pt = False, _alternativas(d["português"])
            if not pt:
                problemas.append(f"GLOSSARIO.md:{n}: '{d['inglês']}' sem tradução")
        else:
            manter, pt = True, list(ing)
        ev = _alternativas(d.get("evitar", ""))
        if ing:
            termos.append(Termo(ing, pt, ev, manter))
    return termos, problemas


def _flexao(palavra):
    """Regex de uma palavra aceitando plural simples (pt e en)."""
    p = re.escape(palavra)  # a palavra já vem sem acentos (ver regex_do_termo)
    if palavra.endswith("ao") and len(palavra) > 3:
        return re.escape(palavra[:-2]) + r"(?:ao|oes|aes|aos)"
    if palavra.endswith("o") and len(palavra) > 3:  # contiguo/contigua/contiguos/contiguas
        return re.escape(palavra[:-1]) + r"(?:o|a|os|as)"
    if palavra.endswith("l") and not palavra.endswith("ll"):
        return re.escape(palavra[:-1]) + r"(?:l|is)"
    if palavra.endswith("r") or palavra.endswith("z"):
        return p + r"(?:es)?"
    return p + r"(?:s|es)?"


def regex_do_termo(termo, maiusculas=False):
    termo = sem_acentos(termo if maiusculas else termo.lower())
    palavras = re.split(r"[\s]+", termo)
    corpo = r"\s+".join(_flexao(p) for p in palavras)
    return re.compile(r"(?<![\w-])" + corpo + r"(?![\w-])")


def _texto_para_busca(prosa):
    return sem_acentos(limpar_prosa(prosa).lower())


def _achou_evitado(ev, preferidos, trad, trad_cs):
    """Há uso real da variante a evitar na tradução?

    Duas exceções ao casamento com flexão, para não acusar a forma certa:
    - variante que só difere da preferida por maiúsculas ("Github" x "GitHub")
      é procurada respeitando maiúsculas;
    - um trecho que a própria forma preferida aceita ("Bochs", plural de
      "Boch"; "sistemas de arquivos") não conta, a menos que seja
      literalmente a variante evitada.
    """
    so_maiusculas = any(ev.lower() == p.lower() and ev != p for p in preferidos)
    texto = trad_cs if so_maiusculas else trad
    literal = sem_acentos(ev if so_maiusculas else ev.lower())
    for m in regex_do_termo(ev, so_maiusculas).finditer(texto):
        achado = re.sub(r"\s+", " ", m.group(0))
        if achado == literal:
            return True
        if not any(regex_do_termo(p).fullmatch(achado.lower()) for p in preferidos):
            return True
    return False


def checar_glossario(prosa_orig, prosa_trad, termos):
    erros, avisos = [], []
    orig, trad = _texto_para_busca(prosa_orig), _texto_para_busca(prosa_trad)
    trad_cs = sem_acentos(limpar_prosa(prosa_trad))  # com maiúsculas
    for t in termos:
        for ev in t.evitar:
            if _achou_evitado(ev, t.portugues, trad, trad_cs):
                erros.append(f'Glossário: "{ev}" deve ser evitado; use '
                             f'"{" / ".join(t.portugues)}" (en: {t.ingles[0]}).')
        if not any(regex_do_termo(e).search(orig) for e in t.ingles):
            continue
        if not any(regex_do_termo(p).search(trad) for p in t.portugues):
            verbo = "mantenha em inglês" if t.manter else "traduza como"
            avisos.append(f'Glossário: "{t.ingles[0]}" aparece no original, mas '
                          f'não achei "{" / ".join(t.portugues)}" na tradução '
                          f"({verbo}).")
    return erros, avisos


# ---------------------------------------------------------------- validação

def validar(nome, expected, termos):
    erros, avisos = [], []
    orig_path, trad_path = RAIZ / f"{nome}.md", TRADUCAO / f"{nome}.md"
    if not orig_path.exists():
        return [f"não existe o original {orig_path.relative_to(RAIZ)}"], []
    if not trad_path.exists():
        return [f"não existe a tradução {trad_path}"], []

    orig, trad = orig_path.read_text(), trad_path.read_text()
    p_o, c_o = dividir(orig)
    p_t, c_t = dividir(trad)

    def comparar(rotulo, a, b, ordenado=True):
        if not ordenado:
            a, b = sorted(a), sorted(b)
        if a == b:
            return
        if Counter(a) != Counter(b):
            faltam, sobram = Counter(a) - Counter(b), Counter(b) - Counter(a)
            msg = f"{rotulo}: diferente do original."
            if faltam:
                msg += f" Faltam: {list(faltam.elements())[:6]}."
            if sobram:
                msg += f" Sobram: {list(sobram.elements())[:6]}."
        else:
            msg = f"{rotulo}: mesmos itens, mas em ordem diferente."
        erros.append(msg)

    # 1. Blocos de código: idênticos, byte a byte.
    comparar("Blocos de código (~~~ e recuados)", c_o, c_t)

    # 2. Código inline: mesmo conjunto (a ordem pode mudar ao traduzir).
    inline = lambda p: [normalizar_espacos(c) for c in INLINE_CODE.findall(p)]
    comparar("Código inline `...`", inline(p_o), inline(p_t), ordenado=False)

    # 3. Links, URLs, citações [@chave], notas de rodapé.
    comparar("Links <url>", AUTOLINK.findall(p_o), AUTOLINK.findall(p_t), False)
    comparar("Destinos de link ](url) e imagens",
             URL_INLINE.findall(p_o), URL_INLINE.findall(p_t), False)
    comparar("Citações [@chave]", CITACAO.findall(p_o), CITACAO.findall(p_t), False)
    comparar("Notas de rodapé [^n]", NOTA.findall(p_o), NOTA.findall(p_t), False)

    # 4. Tabelas: linhas de separação definem as colunas.
    seps = lambda p: [l.strip() for l in p.split("\n") if SEPARADOR_TABELA.match(l)]
    comparar("Linhas de separação de tabela (-----)", seps(p_o), seps(p_t))
    legendas = lambda p: len(re.findall(r"^Table:", p, re.M))
    if legendas(p_o) != legendas(p_t):
        erros.append(f"Legendas 'Table:': original {legendas(p_o)}, "
                     f"tradução {legendas(p_t)}. Traduza a legenda mantendo 'Table:'.")

    # 5. Cabeçalhos: mesmos níveis e id explícito igual ao que o Pandoc geraria.
    h_o, h_t = cabecalhos(p_o), cabecalhos(p_t)
    if [h[0] for h in h_o] != [h[0] for h in h_t]:
        erros.append(f"Cabeçalhos: níveis diferentes. Original {[h[0] for h in h_o]}, "
                     f"tradução {[h[0] for h in h_t]}.")
    else:
        for (nivel, _, _), (_, traduzido, declarado), (_, esperado) in \
                zip(h_o, h_t, expected[nome]):
            if declarado != esperado:
                erros.append(f'Cabeçalho "{traduzido}": use {{#{esperado}}} no fim '
                             f"da linha (veio: {declarado}).")
            if re.search(r"\{[^}]*\}", ID_EXPLICITO.sub("", traduzido)):
                erros.append(f'Cabeçalho "{traduzido}": atributos além de {{#id}}.')

    # 6. Imagens: a legenda (alt) deve ser traduzida.
    alt_o = [normalizar_espacos(a) for a in IMAGEM.findall(p_o)]
    alt_t = [normalizar_espacos(a) for a in IMAGEM.findall(p_t)]
    for a, b in zip(alt_o, alt_t):
        if a and a == b:
            avisos.append(f'Legenda de imagem sem tradução: "{a[:60]}"')

    # 7. Listas e blocos de texto.
    n_o, n_t = len(ITEM_LISTA.findall(p_o)), len(ITEM_LISTA.findall(p_t))
    if n_o != n_t:
        erros.append(f"Itens de lista: original {n_o}, tradução {n_t}.")
    # título é bloco próprio, com ou sem linha em branco depois dele
    blocos = lambda p: [b for b in re.split(r"\n\s*\n", re.sub(
        r"^(#{1,6} .*)$", r"\1\n", p, flags=re.M)) if b.strip()]
    if len(blocos(p_o)) != len(blocos(p_t)):
        avisos.append(f"Blocos de texto (separados por linha em branco): original "
                      f"{len(blocos(p_o))}, tradução {len(blocos(p_t))}. Parágrafo "
                      f"fundido, dividido ou omitido?")
    # ênfase a mais é esperada (o guia manda pôr o termo em inglês em itálico)
    for rotulo, cnt, so_perda in (
            ("Ênfases _..._", lambda t: len(ENFASE.findall(t)), True),
            ("Negritos **", lambda t: t.count("**"), False),
            ("Escapes com barra (\\_)", lambda t: len(ESCAPE.findall(t)), False)):
        a, b = cnt(p_o), cnt(p_t)
        if (b < a) if so_perda else (a != b):
            avisos.append(f"{rotulo}: original {a}, tradução {b}.")

    # 8. Tamanho: tradução muito menor que o original sugere trecho omitido.
    pal_o, pal_t = len(limpar_prosa(p_o).split()), len(limpar_prosa(p_t).split())
    if pal_o >= 60 and not (0.85 <= pal_t / pal_o <= 1.5):
        avisos.append(f"Tamanho: {pal_o} palavras no original, {pal_t} na tradução "
                      f"(razão {pal_t / pal_o:.2f}; esperado ~1.0-1.3).")

    # 9. Inglês remanescente.
    for i, bloco in enumerate(re.split(r"\n\s*\n", limpar_prosa(p_t)), 1):
        palavras = re.findall(r"[A-Za-z']+", bloco.lower())
        n = sum(1 for p in palavras if p in PALAVRAS_INGLES)
        if n >= 4 and n / max(len(palavras), 1) > 0.15:
            avisos.append(f'Possível inglês no bloco {i}: '
                          f'"{" ".join(bloco.split())[:70]}..."')

    # 10. Glossário.
    e, a = checar_glossario(p_o, p_t, termos)
    erros += e
    avisos += a
    return erros, avisos


def resumo_do_bloco(bloco):
    """Primeira linha com conteúdo do bloco (sem a cerca), para listagens."""
    for linha in bloco.split("\n"):
        if linha.strip() and not CERCA.match(linha):
            return linha.strip()[:70]
    return "(vazio)"


def mostrar_ids(nome):
    expected = ids_esperados()
    if nome not in expected:
        print(f"'{nome}' não está em CHAPTERS no Makefile")
        return
    prosa, _ = dividir((RAIZ / f"{nome}.md").read_text())
    titulos = [m.group(2) for m in map(CABECALHO.match, prosa.split("\n")) if m]
    print(f"=== {nome}: título original -> id a usar")
    for (nivel, id_), titulo in zip(expected[nome], titulos):
        print(f"{'#' * nivel} {titulo} {{#{id_}}}")


def mostrar_blocos(nome):
    prosa, blocos = dividir((RAIZ / f"{nome}.md").read_text())
    print(f"=== {nome}: {len(blocos)} blocos de código")
    for i, b in enumerate(blocos, 1):
        print(f"  [{i}] {len(b.splitlines())} linhas: {resumo_do_bloco(b)}")


def main(argv):
    if not argv:
        print(__doc__)
        return 2
    if argv[0] == "--glossario":
        termos, problemas = carregar_glossario()
        print(f"{len(termos)} termos lidos de {GLOSSARIO.relative_to(RAIZ)}")
        for p in problemas:
            print(f"  ERRO  {p}")
        return 1 if problemas else 0
    if argv[0] == "--ids":
        for a in argv[1:]:
            mostrar_ids(a.removesuffix(".md"))
        return 0
    if argv[0] == "--blocos":
        for a in argv[1:]:
            mostrar_blocos(a.removesuffix(".md"))
        return 0

    if argv == ["--todos"]:
        nomes = [n for n in ordem_dos_capitulos() if (TRADUCAO / f"{n}.md").exists()]
        if not nomes:
            print("Nenhuma tradução encontrada ainda.")
            return 0
    else:
        nomes = [a.removesuffix(".md").split("/")[-1] for a in argv]

    termos, problemas = carregar_glossario()
    for p in problemas:
        print(f"  ERRO  {p}")
    expected = ids_esperados()
    total_erros = len(problemas)
    for nome in nomes:
        if nome not in expected:
            print(f"[FALHOU] {nome}\n  ERRO  '{nome}' não está em CHAPTERS no Makefile")
            total_erros += 1
            continue
        erros, avisos = validar(nome, expected, termos)
        total_erros += len(erros)
        situacao = "FALHOU" if erros else ("ok com avisos" if avisos else "ok")
        print(f"[{situacao}] {nome}")
        for e in erros:
            print(f"  ERRO  {e}")
        for a in avisos:
            print(f"  AVISO {a}")
    return 1 if total_erros else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
