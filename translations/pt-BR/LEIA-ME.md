# Tradução pt-BR de *The little book about OS development*

Tradução de uso pessoal do livro de Erik Helin e Adam Renberg. O texto original
(os `.md` da raiz) nunca é alterado; tudo o que é da tradução vive aqui.

**Licença:** o original é Creative Commons BY-NC-SA 3.0. A tradução é uma obra
derivada e mantém a mesma licença (atribuição, uso não comercial, mesma licença).
O aviso aparece no topo do HTML gerado (`template.html`).

## Como traduzir (o dia a dia)

No app Claude Code, dentro deste repositório:

| Comando | O que faz |
|---|---|
| `/traduzir` | Traduz o **próximo capítulo pendente** (ou `/traduzir paging`, `/traduzir "Segmentation"`) |
| `/traduzir-tudo` | Traduz **vários** em sequência, um subagente por capítulo (contexto limpo). `/traduzir-tudo 3` = os próximos 3; sem número = todos os pendentes |

Nos dois casos o resultado é conferido por scripts (abaixo), e o capítulo só passa
a 🟨 em `STATUS.md` se a validação não tiver nenhum ERRO.

## Como o processo protege a tradução

```
original .md ──extrair──▶ esqueleto (código vira @@CODIGO n@@)
                               │  traduz-se só a prosa
                               ▼
               trabalho/<cap>.pt.md ──montar──▶ capitulos/<cap>.md ──validar──▶ 🟨
                                     (código original reinjetado byte a byte)
```

1. **Código nunca é redigitado.** O livro tem 83 blocos, ~830 linhas (Makefiles com tabs,
   linker scripts, diagramas de bits alinhados). `esqueleto.py` os troca por
   marcadores antes de traduzir e os devolve idênticos depois. Não há como o
   modelo estragar um espaço.
2. **`validar.py` confere a estrutura** contra o original: blocos de código
   (com a linha de cerca `~~~ {.nasm}`), código inline, URLs, citações `[@x]`,
   destinos de link, notas de rodapé, linhas de tabela, legendas, itens de lista,
   níveis de título, ids e proporção de tamanho.
3. **Ids de título explícitos.** O Pandoc gera o id do título em inglês
   (`#further-reading-9`) e há links que dependem disso, inclusive ids com
   sufixo numérico que mudam conforme a ordem de todos os capítulos. Por isso
   todo título traduzido leva `{#id-original}`. `validar.py --ids <cap>` diz qual
   usar. (Conferido contra o Pandoc 3.11: os 122 ids calculados são idênticos
   aos reais.)
4. **O glossário é executável.** `GLOSSARIO.md` é lido pelo validador: variante
   proibida na coluna "Evitar" é ERRO; termo esperado ausente é AVISO. Assim a
   consistência não depende de cada sessão "lembrar" o glossário.
5. **`traduzir-tudo` não confia no subagente.** Quem roda `montar` e `validar`
   e decide se o capítulo passou é a sessão principal, e no fim roda
   `validar.py --todos` (um termo novo em "Evitar" pode reprovar um capítulo
   antigo).

O validador **não** avalia qualidade nem naturalidade da tradução. Isso é
trabalho de revisão humana (status ✅).

## Comandos

```bash
python3 translations/pt-BR/progresso.py resumo              # quanto falta
python3 translations/pt-BR/progresso.py proximos 3          # próximos pendentes
python3 translations/pt-BR/validar.py paging                # valida um capítulo
python3 translations/pt-BR/validar.py --todos               # valida tudo que existe
python3 translations/pt-BR/validar.py --glossario           # confere o glossário
python3 translations/pt-BR/validar.py --ids paging          # ids que os títulos devem levar
python3 translations/pt-BR/esqueleto.py extrair paging      # gera o esqueleto
python3 translations/pt-BR/esqueleto.py montar paging       # remonta com o código original
```

## Compilar o livro

Requer `pandoc` >= 2.11 (o `Makefile` original usa opções do pandoc 1.x que não
existem mais; o build pt-BR não depende delas) e, para o PDF, `pdflatex`.

```bash
make pt-BR         # build/pt-BR/book.html
make pt-BR-pdf     # build/pt-BR/book.pdf
```

Capítulos ainda não traduzidos entram **em inglês** (fallback por arquivo), então
dá para compilar o livro parcialmente traduzido a qualquer momento. `make` sem
argumentos continua compilando o livro original em inglês.

## Arquivos

| Arquivo | Função |
|---|---|
| `GUIA-DE-ESTILO.md` | Tom, o que não se traduz, ids, tabelas, gênero, pontuação |
| `GLOSSARIO.md` | Terminologia (lido pelo validador) |
| `STATUS.md` | Progresso, títulos oficiais pt-BR, erros do original |
| `capitulos/` | Os capítulos traduzidos (mesmos nomes do original), `title.txt`, `references.md` |
| `validar.py`, `esqueleto.py`, `progresso.py` | Ferramentas (só biblioteca padrão do Python 3) |
| `traducao.mk` | Regras do `make pt-BR` (incluído pelo `Makefile` da raiz) |
| `template.html`, `header.tex` | Modelos HTML e LaTeX em português |
| `trabalho/` | Rascunhos temporários (ignorado pelo git) |
| `../../.claude/skills/traduzir*` | As skills `/traduzir` e `/traduzir-tudo` |

## Decisões de terminologia que você pode querer rever

São escolhas minhas, defensáveis nos dois sentidos. Para mudar uma, edite a
linha em `GLOSSARIO.md` (e a coluna "Evitar") *antes* de traduzir mais capítulos,
e rode `validar.py --todos` para ver o que a mudança afeta.

- **stack → "pilha"** (e não "stack"). O outro livro traduzido manteve "stack",
  mas aqui o vocabulário é o de assembly x86 (`esp`, ponteiro de pilha), onde
  "pilha" é o termo estabelecido em português.
- **kernel, bootloader, driver, heap, framebuffer, buffer ficam em inglês**;
  "núcleo do sistema" e "carregador de boot" são barrados.
- **page frame → "quadro de página"** (alternativas comuns: "moldura de página").
- **interrupt handler → "tratador de interrupção"** (alternativas: "manipulador").
- **scheduling → "escalonamento"**, **yielding** fica em inglês.
- **link (verbo) → "linkar"**; **relocation → "relocação"**.

## Limitações conhecidas

- O `template.html` remove o link "PDF version" do topo (o PDF só existe se você
  rodar `make pt-BR-pdf`); passe `-V pdf=1` ao pandoc se quiser o link.
- `syscalls.md` tem, no original, um link para `#further-reading-7` que deveria
  ser `#further-reading-10`. Mantido idêntico (ver `STATUS.md`).
- O PDF compila, mas não foi inspecionado visualmente (sem `pdftoppm` na máquina).
