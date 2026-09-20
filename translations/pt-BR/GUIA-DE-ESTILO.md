# Guia de estilo: tradução pt-BR de *The little book about OS development*

Tradução de uso pessoal, para leitura e estudo. O livro original (Erik Helin e
Adam Renberg) é licenciado sob Creative Commons BY-NC-SA 3.0; a tradução mantém
a mesma licença (ver `LEIA-ME.md`).

## Tom e voz

- O livro é um **guia prático**, direto e didático, com pouco humor. Traduza o
  efeito: instruções claras, frases curtas, sem "elevar" o registro.
- Português do Brasil, registro informal-culto. Sem gírias datadas nem
  regionalismos fortes. **Nada de português de Portugal** ("ficheiro",
  "utilizador", "ecrã": o glossário barra isso).
- As pessoas que escrevem falam em **primeira pessoa do plural** ("we
  recommend", "our kernel") e com o leitor por **"você"**. Mantenha: "recomendamos",
  "nosso kernel", "você deve".
- O original usa muito o impessoal *one* ("one can think of...") e a voz
  passiva. Em português, prefira "podemos", "é possível", "dá para", ou a
  primeira pessoa do plural, conforme soar mais natural.
- **Gênero:** nenhuma pessoa tem gênero presumido pelo nome: nem quem escreveu
  o livro, nem quem contribuiu, nem quem é citado ou agradecido. Use construções
  neutras: "quem lê" em vez de "o leitor", "a autoria", "nós" em vez de "os
  autores", "agradecemos a Fulano pelo tutorial" sem "seu"/"dele"/"grato". O
  plural genérico ("os desenvolvedores", "todos") é aceitável para grupos.
  O original tem "for his eminent tutorial": traduza sem pronome ("pelo
  excelente tutorial de kernel").
- Voz ativa quando o original usar.

## O que NUNCA se traduz

1. **Blocos de código**, tanto os cercados por `~~~` quanto os recuados em 4
   espaços: idênticos ao original, byte a byte, inclusive **os comentários
   dentro deles**.
2. **Código inline** entre crases: registradores, instruções, nomes de arquivo,
   comandos, valores. Ex.: `esp`, `0xC0000000`, `lgdt`, `loader.s`. A crase
   pode quebrar a linha ao reflowar; o conteúdo, não.
3. **URLs**, tanto `<http://...>` quanto o destino de `[texto](destino)`.
4. **Citações** `[@chave]`: a chave não muda nunca.
5. **Caminhos de imagem** (`images/x.png`), **rótulos de nota de rodapé**
   (`[^1]`), **linhas de traços de tabela** (`-------  -----`) e o prefixo
   `Table:`.
6. **Nomes próprios**: pessoas, projetos, produtos (GRUB, NASM, Bochs, Intel),
   **títulos de obras** (ficam no original, em itálico; não invente título
   brasileiro).
7. **Escapes** com barra, como em `x86\_64`.
8. Siglas do hardware e do manual da Intel: GDT, IDT, PDT, TLB, DPL, PL0...

## O que se traduz

- Todo o texto corrido, itens de lista e descrições nas seções "Leitura
  Complementar" (mas os nomes de quem escreveu os artigos ficam).
- **Títulos de seção**, preservando o `{#id}` (ver abaixo).
- A **legenda das imagens** (o texto entre `![` e `]`), que pode quebrar linha.
- Cabeçalhos e células de **tabelas** que não sejam código, e a legenda depois de
  `Table:`.
- O texto das **notas de rodapé** (`[^1]: ...`).
- O texto dos links (`[texto](#id)`), nunca o destino.

## Títulos e âncoras (`{#id}`)

O Pandoc gera o id de cada título a partir do texto em inglês, e há links no
livro que apontam para esses ids (`[chapter 2](#first-steps)`), inclusive ids com
sufixo numérico (`#further-reading-9`), que dependem da ordem de todos os
capítulos. Para nada quebrar, **todo título traduzido leva o id original
explícito** no fim da linha:

```markdown
## Carregando a GDT {#loading-the-gdt}
### Posicionando o Kernel em `0xC0000000` {#placing-the-kernel-at-0xc0000000}
```

Não invente nem calcule o id: peça ao validador.

```bash
python3 translations/pt-BR/validar.py --ids <capitulo>
```

Ele lista, na ordem, o nível, o id e o título original de cada seção do capítulo.
Copie o id exatamente.

Títulos: use *Title Case* em português (preposições e artigos em minúscula):
"Chamadas de Sistema", "Configurando a Linha". "Further Reading" sempre é
"Leitura Complementar" (ver glossário).

## Links entre capítulos e seções

O original usa links internos assim: `[chapter 5](#segmentation)` e
`the section ["Further Reading"](#further-reading-7)`.

- Traduza o texto, mantenha o destino: `[capítulo 5](#segmentation)`.
- Quando o texto cita um capítulo pelo nome, use o **título oficial pt-BR** da
  tabela de `STATUS.md` (mesmo que aquele capítulo ainda não tenha sido
  traduzido), nas aspas do original: `["Paginação"](#paging)`.
- Números de capítulo escritos no texto ("chapter 2") ficam como estão.

## Tabelas

As tabelas são do tipo simples/multilinha do Pandoc, e o Pandoc decide as
colunas pelas linhas de traços, que **não mudam**. Traduza os cabeçalhos e as
células que não são código, mas mantenha cada texto **dentro da sua coluna**,
começando na mesma posição do original. Se a palavra em português for mais
longa do que a coluna, abrevie ou reformule; em tabelas multilinha, quebre o
conteúdo em mais linhas dentro da mesma coluna. Depois de traduzir, confira o
resultado com `make pt-BR` (ver `LEIA-ME.md`) e olhe a tabela no HTML.

- Cabeçalhos usuais: Index → Índice, Name → Nome, Type → Tipo, Description →
  Descrição, Address range → Faixa de endereços, Offset → Deslocamento (ou
  "Desloc." se a coluna for estreita).
- Nomes de campo que aparecem também no **diagrama de bits** (um bloco de
  código, que não muda), como `rpl`, `ti`, `offset (index)`, ficam em inglês:
  a tabela precisa continuar batendo com a figura.
- Nomes de segmento etc. numa coluna estreita: encurte ("código do kernel", em
  vez de "segmento de código do kernel"), o título/legenda da tabela já diz que
  são segmentos.

## Termos técnicos

Ver `GLOSSARIO.md` (é lido pelo `validar.py`). Regra geral: **fica em inglês o
que a comunidade brasileira de sistemas já usa em inglês** (kernel, bootloader,
driver, heap, buffer, framebuffer...); o resto se traduz.

Quando o original **define** um termo em itálico (`_segment descriptor_`), o termo
em português vai em itálico no mesmo lugar. Se for um termo que a pessoa vai
precisar procurar em inglês (o Manual da Intel e a OSDev estão em inglês) e ele
não está em "Ficam em inglês", acrescente o original entre parênteses **na
primeira vez que aparece no capítulo**:

> _falha de página_ (_page fault_)

Estrangeirismos mantidos ficam em texto normal, sem itálico, exceto na
definição. Plurais sem apóstrofo: "os drivers", "os buffers".

Siglas: o original define "operating system (OS)". Em português: "sistema
operacional (SO)" na introdução; nos capítulos seguintes, use "SO" e "sistema
operacional" livremente. Mantenha as siglas de hardware em inglês (GDT, IDT...), e
quando o original expande a sigla, expanda em português seguido da sigla:
"tabela de descritores globais (GDT)".

Abreviações latinas: *e.g.* → "por exemplo" (ou "ex.:"), *i.e.* → "ou seja",
*etc.* → "etc.".

## Pontuação e formatação

- Aspas: retas `"` como no original (o Pandoc converte).
- **Travessão de frase:** o original escreve ` - ` (hífen entre espaços) como
  travessão. Em português, escreva ` -- ` (o Pandoc converte em travessão).
  Faixas numéricas (`0 - 24`, `bit 7 - 4`) e intervalos de endereço **não**
  mudam.
- Mantenha ênfase (`_texto_`), negrito (`**texto**`), listas e quebras de linha do
  original. Pode-se reflowar o parágrafo (linhas de ~80 colunas), mas **não
  fundir nem dividir parágrafos**, nem itens de lista.
- A ordem e o número dos itens de lista não mudam.
- Números e unidades como no original: `4 MB`, `115200 Hz`, `0xC0000000`.
- Nomes de arquivo, comandos e funções ficam como estão.

## Erros do original

O original tem erros de digitação (por exemplo, "intterupts", "Malloy",
"Duertes", "Boch"). Na tradução, **escreva o certo** e registre na seção "Erros
do original" de `STATUS.md` (capítulo, o que estava errado). Não é permitido
alterar código, URLs ou ids por causa disso: o validador exige que fiquem
idênticos. Se um link do original estiver apontando para o lugar errado,
mantenha-o e registre também.

## Formato do arquivo

Um arquivo por capítulo, com o **mesmo nome** do original, em
`translations/pt-BR/capitulos/`. Sem frontmatter, sem cabeçalho extra, sem notas do
tradutor. O arquivo traduzido substitui o original no build.
