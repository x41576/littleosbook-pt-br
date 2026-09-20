---
name: traduzir-tudo
description: Traduz vários capítulos do livro em sequência, com um subagente por capítulo (contexto limpo) e validação independente de cada um. Use quando o usuário pedir "/traduzir-tudo", "traduza o livro todo" ou "traduza os próximos N capítulos".
argument-hint: "[N | capítulo1 capítulo2 ...]  (vazio = todos os pendentes)"
---

# Traduzir vários capítulos, um subagente por capítulo

Você é o **orquestrador**. Não traduz nada você mesmo: delega cada capítulo a um
subagente novo (assim cada tradução começa com contexto limpo e relê o glossário
atualizado) e **você** confere o resultado com os scripts, sem confiar no relato
do subagente. Todos os comandos rodam da raiz do repositório.

O processo de tradução de um capítulo está em `.claude/skills/traduzir/SKILL.md`.
Leia-o antes de começar (você precisa conhecê-lo para cobrar o subagente).

## 1. Montar o plano

- Argumento numérico `N`: `python3 translations/pt-BR/progresso.py proximos N`
- Nomes de capítulos: use-os, na ordem do livro (confira cada um com
  `progresso.py titulo <nome>`), pulando os que já estão 🟨/✅ (avise).
- Sem argumento: todos os pendentes (`progresso.py proximos 99`).

Antes de começar, rode `python3 translations/pt-BR/validar.py --glossario` (se
falhar, pare e mostre o problema) e mostre ao usuário o plano: a lista de
capítulos com o número de palavras (de `STATUS.md`). Não peça confirmação, a não
ser que o plano tenha mais de 8 capítulos e o usuário não tenha dito quantos
queria; nesse caso, pergunte uma vez.

## 2. Para cada capítulo, **em sequência** (nunca em paralelo)

O glossário é atualizado a cada capítulo, então dois subagentes ao mesmo tempo
decidiriam termos em duplicidade.

### 2.1 Delegar

Chame a ferramenta Agent (tipo `general-purpose`, em primeiro plano) com um prompt
autossuficiente, no espírito de:

> Traduza o capítulo `<arquivo>` do livro para português do Brasil. Leia
> `.claude/skills/traduzir/SKILL.md` e siga os passos 1 a 4 à risca, para
> este capítulo. Diferenças: NÃO execute o passo 5 (não marque o status e não
> apague o rascunho em `translations/pt-BR/trabalho/`, o orquestrador faz isso).
> Você pode acrescentar termos ao `GLOSSARIO.md` e erros do original ao
> `STATUS.md`. Termine só quando `python3 translations/pt-BR/validar.py <arquivo>`
> não mostrar nenhum ERRO. Responda, em português e em poucas linhas: (1) o
> resultado final do validar.py, (2) os avisos que você examinou e por que ignorou
> cada um, (3) os termos novos que registrou no glossário, (4) os trechos em que
> a tradução foi mais livre.

### 2.2 Conferir você mesmo

```bash
python3 translations/pt-BR/esqueleto.py montar <arquivo>
python3 translations/pt-BR/validar.py <arquivo>
```

(O `montar` de novo garante que `capitulos/` reflete o `.pt.md` final.)

- **Sem ERRO:** examine os AVISOS que sobraram; se algum indicar problema real
  (parágrafo em inglês, omissão), trate como falha. Se estiver tudo bem,
  `python3 translations/pt-BR/progresso.py marcar <arquivo>` e apague o rascunho:
  `rm -f translations/pt-BR/trabalho/<arquivo>.md translations/pt-BR/trabalho/<arquivo>.pt.md`
- **Com ERRO (ou aviso grave):** devolva ao mesmo subagente (SendMessage, se
  você tiver o id dele; senão, um novo Agent) com a saída **completa** do
  validador e a instrução de corrigir **o `.pt.md`** (não `capitulos/`) e
  repetir `montar` + `validar`. **No máximo 2 tentativas de correção.** Se ainda
  falhar, deixe o capítulo ⬜, mantenha o rascunho para inspeção, anote o motivo
  e **siga para o próximo** (não trave o lote por um capítulo).

Se um subagente alterar arquivos fora de `translations/pt-BR/` (confira com
`git status --short`), reverta só essa alteração e registre o incidente.

## 3. Depois do lote

1. `python3 translations/pt-BR/validar.py --glossario` e depois
   `python3 translations/pt-BR/validar.py --todos`. Um termo **novo** em "Evitar"
   pode ter deixado um capítulo **antigo** fora do glossário: liste esses casos.
   Corrija-os você mesmo só se for troca trivial e segura de termo; senão,
   reporte.
2. Se o `pandoc` estiver instalado, `make pt-BR` para conferir que o livro
   compila.
3. `python3 translations/pt-BR/progresso.py resumo`.

## 4. Relatório final (em português)

- Tabela: capítulo · resultado (🟨 / falhou) · tentativas · avisos relevantes.
- Termos novos no glossário e decisões que o usuário pode querer rever (mostre
  como ver: `git diff translations/pt-BR/GLOSSARIO.md`).
- Erros do original encontrados.
- Capítulos que falharam, com o motivo, e o que fazer.
- Próximo passo (capítulos pendentes; ou, se acabou, sugerir revisão).

## Regras de segurança

- Os subagentes só escrevem em `translations/pt-BR/`. Nunca em `.md` originais,
  `images/`, `files/`, `Makefile` ou `bibliography.bib`.
- Não faça `git commit`/`git push`. O usuário decide quando.
- Não altere `validar.py`, `esqueleto.py` nem `progresso.py`.
