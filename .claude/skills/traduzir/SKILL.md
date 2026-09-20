---
name: traduzir
description: Traduz um capítulo do livro "The little book about OS development" (arquivos .md da raiz) para português do Brasil, um por vez, sem digitar código (só a prosa), e valida o resultado. Use quando o usuário pedir "/traduzir <capítulo>" ou para traduzir/continuar a tradução do livro.
argument-hint: "[capítulo]  ex.: paging | \"Segmentation\" | (vazio = próximo pendente)"
---

# Traduzir um capítulo (pt-BR)

Traduza **um** capítulo para `translations/pt-BR/capitulos/`, seguindo o processo
abaixo. Os arquivos de apoio ficam em `translations/pt-BR/`. Todos os comandos
rodam a partir da raiz do repositório.

## 1. Escolher o capítulo

- Com argumento: aceite o nome do arquivo (`paging`), o título em inglês ou o
  título pt-BR. Confirme com:
  `python3 translations/pt-BR/progresso.py titulo <argumento>`
- Sem argumento: `python3 translations/pt-BR/progresso.py proximos 1`
- Se já existir `translations/pt-BR/capitulos/<arquivo>.md`, pergunte se é para
  refazer antes de sobrescrever.
- Traduza **um capítulo por invocação**. Se o usuário pedir vários, traduza o
  primeiro, reporte, e sugira `/traduzir-tudo` (que usa um subagente por
  capítulo, com contexto limpo) ou `/clear` antes do próximo.

## 2. Ler o contexto

Leia integralmente, nesta ordem:

1. `translations/pt-BR/GUIA-DE-ESTILO.md`
2. `translations/pt-BR/GLOSSARIO.md` (as colunas **Evitar** são verificadas por
   máquina: usar um termo evitado é ERRO)
3. `translations/pt-BR/STATUS.md` (títulos pt-BR dos capítulos, para referências
   cruzadas, e a seção "Erros do original")
4. O capítulo original, `<arquivo>.md` (na raiz), para entender o código ao redor
5. Se existir, o começo (uns 40 linhas) da tradução do capítulo anterior em
   `translations/pt-BR/capitulos/`, para manter a voz

Depois gere o esqueleto e a lista de ids:

```bash
python3 translations/pt-BR/esqueleto.py extrair <arquivo>
python3 translations/pt-BR/validar.py --ids <arquivo>
```

O primeiro cria `translations/pt-BR/trabalho/<arquivo>.md`: o capítulo **sem os
blocos de código**, cada um substituído por uma linha `@@CODIGO n@@`. O segundo
lista o `{#id}` que cada título traduzido precisa levar.

## 3. Traduzir

Você **não digita código nunca**. O código volta sozinho, byte a byte, no passo
seguinte. Portanto:

- Leia `translations/pt-BR/trabalho/<arquivo>.md` e escreva a tradução em
  `translations/pt-BR/trabalho/<arquivo>.pt.md`.
- Onde houver `@@CODIGO n@@`, escreva a mesma linha, **sozinha na linha, na mesma
  posição** entre os parágrafos, com o mesmo `n`. Não apague, não repita, não
  reordene marcadores.
- Trabalhe **seção por seção** (cada `## `; em capítulos grandes, também `###`).
  Escreva o primeiro trecho com Write e acrescente os seguintes com
  `cat >> arquivo <<'EOF_TRAD' ... EOF_TRAD` (delimitador entre aspas simples,
  para o shell não interpretar `$` nem crases).
- Cubra **tudo**: todos os parágrafos, itens de lista, tabelas (cabeçalhos e
  células de texto), legendas `Table:`, legendas de imagem, notas de rodapé e as
  listas de "Leitura Complementar". Não resuma, não omita, não acrescente
  comentários do tradutor.
- Todo título leva o `{#id}` que `--ids` mostrou, copiado exatamente.
- Aplique o guia de estilo à risca: o que nunca se traduz, links, citações
  `[@x]`, travessão ` -- `, neutralidade de gênero, termos do glossário.
- Erros do original (ver `STATUS.md`): escreva o certo, e registre novos que
  encontrar na seção "Erros do original" do `STATUS.md`.
- Termo novo que precise de decisão: escolha, use de forma consistente e
  registre no `GLOSSARIO.md` (na tabela certa, respeitando as regras do topo do
  arquivo). Se estiver inseguro, coloque em "Dúvidas em aberto".

## 4. Montar e validar (obrigatório)

```bash
python3 translations/pt-BR/esqueleto.py montar <arquivo>
python3 translations/pt-BR/validar.py <arquivo>
```

- Se `montar` reclamar de marcadores, corrija o `.pt.md` e repita.
- Todo **ERRO** do `validar.py` deve ser corrigido **no `.pt.md`**, remontando
  em seguida (nunca edite direto em `capitulos/`, senão o próximo `montar`
  desfaz a correção). Repita até passar.
- Cada **AVISO** deve ser examinado. Corrija se for um problema real (parágrafo
  em inglês, trecho omitido, termo do glossário ausente); ignore se for falso
  positivo (ex.: uma citação que fica no original), e diga isso no relatório.
- Não altere `validar.py`, `esqueleto.py` nem as tabelas do glossário só para
  fazer o capítulo passar. Se uma regra estiver errada, avise o usuário.
- Erros de "Glossário: X deve ser evitado" são exigência do glossário: troque o
  termo. Se acha a regra errada, deixe o termo como está, explique no relatório e
  não mexa no glossário sem o usuário.

Depois de validar, se o `pandoc` estiver instalado, confirme que o livro compila
com o capítulo:

```bash
make pt-BR
```

Se falhar, o erro costuma ser marcação quebrada (tabela desalinhada, `{#id}`
mal formado). Veja `translations/pt-BR/LEIA-ME.md`.

## 5. Encerrar

1. `python3 translations/pt-BR/progresso.py marcar <arquivo>` (passa a 🟨).
2. Apague o rascunho: `rm translations/pt-BR/trabalho/<arquivo>.md translations/pt-BR/trabalho/<arquivo>.pt.md`
   (a pasta é ignorada pelo git, mas mantenha-a limpa).
3. Confirme que o `GLOSSARIO.md` recebeu os termos novos.
4. Responda ao usuário, em português, com: capítulo traduzido, resultado da
   validação (erros corrigidos, avisos examinados), termos novos decididos,
   trechos em que a tradução foi mais livre, erros do original encontrados e o
   próximo capítulo pendente.

## Regras de segurança

- Nunca edite os `.md` originais da raiz, `images/`, `files/`, `Makefile` nem
  `bibliography.bib`.
- Só escreva dentro de `translations/pt-BR/` (e o `.claude/skills/` se o usuário
  pedir para mudar o processo).
- A tradução é para uso pessoal; o livro é CC BY-NC-SA 3.0 (ver `LEIA-ME.md`).
