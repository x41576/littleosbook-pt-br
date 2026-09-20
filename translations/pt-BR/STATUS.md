# Status da tradução pt-BR

Legenda: ⬜ pendente · 🟨 traduzido e validado (sem revisão) · ✅ revisado

Quem atualiza a coluna de status é o `progresso.py` (as skills `/traduzir` e
`/traduzir-tudo` o chamam ao terminar; à mão: `python3 translations/pt-BR/progresso.py marcar <capitulo> 🟨`).
**Não mude o formato das linhas da tabela**: o script as lê.

A coluna "Nº" é o número do capítulo como o Pandoc numera no livro (o texto
cita "chapter 5", "chapter 9"...). Os títulos pt-BR abaixo são os oficiais desta
tradução: use-os ao citar capítulos.

## Capítulos

| Status | Arquivo | Nº | Título original | Título pt-BR | Palavras |
|---|---|---|---|---|---|
| 🟨 | `introduction.md` | 1 | Introduction | Introdução | 917 |
| 🟨 | `environment_and_booting.md` | 2 | First Steps | Primeiros Passos | 2023 |
| 🟨 | `getting_to_c.md` | 3 | Getting to C | Chegando ao C | 1238 |
| 🟨 | `output.md` | 4 | Output | Saída | 3132 |
| 🟨 | `segmentation.md` | 5 | Segmentation | Segmentação | 1233 |
| 🟨 | `interrupts.md` | 6 | Interrupts and Input | Interrupções e Entrada | 2008 |
| 🟨 | `the_road_to_user_mode.md` | 7 | The Road to User Mode | O Caminho até o Modo Usuário | 1037 |
| 🟨 | `virtual_memory.md` | 8 | A Short Introduction to Virtual Memory | Uma Breve Introdução à Memória Virtual | 308 |
| 🟨 | `paging.md` | 9 | Paging | Paginação | 2590 |
| 🟨 | `page_frame_allocation.md` | 10 | Page Frame Allocation | Alocação de Quadros de Página | 1036 |
| 🟨 | `user_mode.md` | 11 | User Mode | Modo Usuário | 1372 |
| 🟨 | `file_systems.md` | 12 | File Systems | Sistemas de Arquivos | 645 |
| 🟨 | `syscalls.md` | 13 | System Calls | Chamadas de Sistema | 558 |
| 🟨 | `scheduling.md` | 14 | Multitasking | Multitarefa | 1310 |
| 🟨 | `references.md` | 15 | References | Referências | 2 |

## Outros arquivos traduzidos à mão

| Status | Arquivo | O que é |
|---|---|---|
| 🟨 | `capitulos/title.txt` | Título, autoria e data da página de rosto |
| 🟨 | `template.html` | Modelo HTML ("Contents" e "PDF version" no idioma) |

## Erros do original

Erros de digitação e afins encontrados no original. A tradução escreve o certo
(o texto em inglês não é alterado nunca). Quem encontrar mais um acrescenta aqui.
Formato: capítulo: o que estava, o que fica.

- `introduction`: "James Malloy" (o autor do tutorial é James Molloy; a bibliografia está certa) → "James Molloy".
- `environment_and_booting`: "Gustavo Duertes" → "Gustavo Duarte"; "Boch" → "Bochs".
- `interrupts`: "software intterupts" → "interrupções de software"; "Interrupts Handlers" (título) → "Tratadores de Interrupção"; "Privilige" (tabela do DPL) → "privilégio"; "hander" → "tratador"; "as an handler" → "como tratador"; "the following two bytes" (são dois valores de 32 bits, `0xDEAD8E00` e `0x0008BEEF`) → "os dois valores de 32 bits a seguir". O cabeçalho da tabela de campos da IDT ("Name Description") está recuado no original e por isso é tratado como bloco de código: fica em inglês.
- `syscalls`: o link para a seção "Further Reading" aponta para `#further-reading-7`, que é a seção de *Page Frame Allocation*; deveria ser `#further-reading-10`. Mantido como no original (o validador exige links idênticos), pendente de decisão.
- `getting_to_c`: "Kernigan & Richie" (Leitura Complementar) → "Kernighan e Ritchie" (Brian Kernighan e Dennis Ritchie); "it make sense" → "fizer sentido".
- `output`: "first serial serial port" (Configuring Bochs) → "primeira porta serial"; "DTS = 1" (Configuring the Modem) → "DTR = 1" (o pino é o Data Terminal Ready, como diz o parágrafo anterior).
- `paging`: "4096 byte large" → "4096 bytes"; "when an updating" → "ao atualizar"; "should should" → "devem"; "an jump" → "um salto"; a citação de link `(see the chapter ["Page Frame Allocation](...)` sem fechar aspas → aspas fechadas. Dentro de código inline (mantidos, o validador exige): `0xC01000000` (nove dígitos, deveria ser `0xC0100000`) e `0x0010000` (deveria ser `0x00100000`). Faltam também a frase "Adicionar uma entrada ..." sem ponto final na lista (mantido como no original).
- `user_mode`: "for for" → "como formato de arquivo"; "get a basic implementation work" → "fazer funcionar uma implementação básica"; "the followings flags" → "as flags a seguir"; "can't enabled" → "não poderão ser habilitadas"; "does not" (sujeito plural, "functions in `string.h`") → "não exige". A linha "- `0x00000000` in our case" começa com hífen no original (não vira lista no Pandoc por não haver linha em branco antes); mantida na mesma posição para o validador contar os itens de lista.
- `scheduling`: "on system with" → "em sistemas com"; "at at a time" → "por vez"; "has to sent first" → "é preciso enviar"; "it's own kernel stack" → "a sua própria pilha do kernel"; "the one defined it the TSS" → "definida no TSS"; "one must think of how to handle case" → "é preciso pensar em como tratar o caso"; "what the previous process have written" e "each process have" (concordância) → escritos corretamente; "`exec`, `fork` and `yield`" mantido. Singular em "the process `ss` and `esp` register" (seção sobre o Programmable Interval Timer) → "registradores `ss` e `esp`".
