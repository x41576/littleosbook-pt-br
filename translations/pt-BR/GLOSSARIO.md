# Glossário pt-BR

Decisões fixas de terminologia. **Consulte antes de traduzir** e **acrescente**
todo termo novo relevante que aparecer.

## Como este arquivo é usado (leia antes de editar)

O `validar.py` lê as tabelas abaixo e confere cada capítulo traduzido:

- **Evitar** (coluna): se qualquer variante listada aparecer na prosa traduzida,
  é **ERRO**. Serve para impor a escolha e barrar variantes (inclusive
  regionalismos de Portugal).
- **Português** (coluna): se o termo em inglês aparece no original e nenhuma das
  formas em português aparece na tradução, é **AVISO**.
- Nas tabelas "Ficam em inglês", o próprio termo em inglês é a forma esperada.

Regras de formatação, para o parser não engasgar:

1. Uma linha por conceito. Alternativas dentro da mesma célula se separam por
   ` / ` (espaço, barra, espaço). Não use `|` dentro de uma célula.
2. Escreva os termos no singular. O validador aceita plural simples
   (`quadro de página` casa com `quadros de página`).
3. Parênteses numa célula são ignorados na conferência: o que importa é o que
   está fora deles. Use-os para siglas (`(GDT)`).
4. Acentos e maiúsculas não importam na conferência (exceção: uma variante em
   **Evitar** que só difere da forma certa por maiúsculas, como `Github` x `GitHub`,
   é procurada respeitando maiúsculas; e um trecho que a própria forma certa
   aceita, como `Bochs` ou `sistemas de arquivos`, nunca é acusado). Código inline (crases),
   URLs e citações `[@x]` são ignorados.
5. Só coloque em **Evitar** o que é errado em **qualquer** contexto. Uma
   palavra comum que pode ser legítima em outro sentido (ex.: "registro")
   fica só na observação.
6. Depois de editar, rode `python3 translations/pt-BR/validar.py --glossario`.

Regra geral: **fica em inglês o que a comunidade brasileira de sistemas já usa
em inglês**; o resto se traduz. Onde a prática é dividida, a escolha está aqui
e vale para o livro todo.

## Ficam em inglês

| Inglês | Evitar | Observação |
|---|---|---|
| kernel | núcleo do sistema / núcleo do SO / núcleo do sistema operacional | "núcleo" só para núcleo de processador (multi-core) |
| bootloader | carregador de boot / carregador de inicialização / carregador de bootstrap | negrito/itálico na definição, como o original |
| boot | | "o processo de boot", "dar boot" |
| driver | | plural: drivers |
| framebuffer | buffer de quadro / buffer de vídeo / memória de vídeo | |
| heap | | "heap do kernel" |
| buffer | | |
| array | vetor | "array de descritores"; plural: arrays |
| struct | | "struct empacotada" para *packed struct* (ver "Traduzimos") |
| flag | sinalizador | "flag IF", "flags do GCC" |
| padding | | |
| bitmap | | "usar um bitmap"; plural: bitmaps (alocador de quadros de página) |
| Buddy System | | nome do algoritmo de alocação (usado pelo Linux), fica como no original |
| label | rótulo | rótulo de assembly, como `flush_cs` |
| macro | | |
| assembly | | "código assembly", "instrução assembly" |
| assembler | montador | |
| linker | ligador | "script do linker" |
| scan code | código de varredura | |
| yielding | | "ceder a vez" na explicação; o termo em itálico ao definir |
| trap | | "tratador de trap" |
| gate | | "tamanho do gate" (campo D do descritor da IDT); não traduzir por "porta", que é a porta de E/S |
| acknowledge | | "confirmar" a interrupção do PIC; ao definir: (_acknowledged_) |
| log | | "o log do Bochs"; "registro" só no sentido de logging se o texto pedir |
| pull request | | |
| issue | | "issues do GitHub" |
| patch | | |
| fork | | "fazer um fork" (verbo e substantivo) |
| bug | | "achar os bugs" |
| wiki | | |
| tutorial | | |
| Translation Lookaside Buffer | | seguido da sigla: TLB |
| Basic Input Output System | | seguido da sigla: BIOS |
| master boot record | | seguido da sigla: MBR |
| identity paging | paginação de identidade / paginação por identidade | itálico ao definir |
| Molloy | Malloy | James Molloy: o original grafa "Malloy" no texto, mas o autor do tutorial é Molloy (a bibliografia está certa) |
| Duarte | Duertes | Gustavo Duarte: o original tem uma grafia errada em "Getting to C"/"First Steps" |
| Bochs | Boch | |
| x86 / x86\_64 | | manter o `\_` |
| Pandoc | | |
| GitHub | Github | |
| inode | | itálico ao definir (_inode_); plural: inodes |
| vnode | | plural: vnodes |

## Traduzimos

| Inglês | Português | Evitar | Observação |
|---|---|---|---|
| operating system | sistema operacional | | sigla "SO" depois da primeira ocorrência, como o original faz com "OS" |
| virtual machine | máquina virtual | | |
| emulator | emulador | | |
| host operating system | sistema operacional hospedeiro | | |
| build system | sistema de build | | |
| build tools | ferramentas de build | | |
| ISO image | imagem ISO | | |
| object file | arquivo objeto | | |
| executable | executável | | substantivo e adjetivo |
| entry point | ponto de entrada | | |
| entry symbol | símbolo de entrada | | |
| flat binary | binário plano | | |
| compile | compilar | | |
| compiler | compilador | | |
| link (verbo) | linkar | | "linkado", "linkagem" para *linking*; heading "Linking the Kernel" = "Linkando o Kernel" |
| linker script | script do linker | script de linker | |
| calling convention | convenção de chamada | | |
| stack | pilha | stack | decisão deliberada: o vocabulário de x86/assembly em português usa "pilha" |
| stack pointer | ponteiro de pilha | | |
| kernel stack | pilha do kernel | | |
| pointer | ponteiro | | |
| register | registrador | | "registro" é outra coisa (log, MBR): nunca para *register* |
| segment register | registrador de segmento | | |
| instruction | instrução | | |
| packed struct | struct empacotada | struct compactada | |
| offset | deslocamento | | cabeçalho de tabela "Offset" = "Deslocamento" |
| alignment | alinhamento | | "alinhado", "alinhar" |
| section | seção | | seções do ELF (`.bss`, `.data`) |
| relocation | relocação | realocação | |
| load address | endereço de carga | | |
| absolute address | endereço absoluto | | |
| far jump | salto distante | | itálico/aspas conforme o original |
| I/O port | porta de E/S | porta de I/O | E/S = entrada/saída |
| memory-mapped I/O | E/S mapeada em memória | | |
| interrupt | interrupção | | |
| interrupt handler | tratador de interrupção | manipulador de interrupção / handler de interrupção | "handler" avulso também é evitado na prosa |
| software interrupt | interrupção de software | | |
| hardware interrupt | interrupção de hardware | | |
| exception | exceção | | |
| general protection exception | exceção de proteção geral | | sigla GPE |
| page fault | falha de página | | ao definir, pode-se acrescentar (*page fault*) |
| error code | código de erro | | |
| Interrupt Descriptor Table | tabela de descritores de interrupção | | sigla IDT |
| Global Descriptor Table | tabela de descritores globais | | sigla GDT |
| Local Descriptor Table | tabela de descritores locais | | sigla LDT |
| Task State Segment | segmento de estado de tarefa | | sigla TSS; ao definir: (_Task State Segment_, TSS); "descritor de segmento de TSS" |
| descriptor | descritor | | |
| null descriptor | descritor nulo | | |
| segment descriptor | descritor de segmento | | |
| segment selector | seletor de segmento | | |
| code segment | segmento de código | | |
| data segment | segmento de dados | | |
| segmentation | segmentação | | |
| paging | paginação | | |
| page | página | | |
| page frame | quadro de página | moldura de página / frame de página / quadro de memória | sigla PF |
| page frame allocator | alocador de quadros de página | | |
| page table | tabela de páginas | tabela de página | sigla PT |
| page directory | diretório de páginas | diretório de página | sigla PDT |
| page directory entry | entrada do diretório de páginas | | sigla PDE |
| page table entry | entrada da tabela de páginas | | sigla PTE |
| identity mapping | mapeamento de identidade | | mapear virtual = físico; a técnica em si, *identity paging*, fica em inglês |
| higher half | metade superior | | "kernel na metade superior (*higher-half kernel*)" ao definir |
| virtual memory | memória virtual | | |
| physical memory | memória física | | |
| address space | espaço de endereçamento | | |
| virtual address | endereço virtual | | |
| physical address | endereço físico | | |
| linear address | endereço linear | | |
| logical address | endereço lógico | | |
| memory allocation | alocação de memória | | |
| fragmentation | fragmentação | | |
| contiguous | contíguo | | |
| privilege level | nível de privilégio | camada de privilégio | siglas PL, CPL, DPL, RPL mantidas |
| Descriptor Privilege Level | nível de privilégio do descritor | | DPL |
| Requested Privilege Level | nível de privilégio requisitado | | RPL |
| current privilege level | nível de privilégio atual | | sigla CPL |
| user mode | modo usuário | modo de usuário / modo do usuário / user mode | |
| kernel mode | modo kernel | modo de kernel / modo do kernel / kernel mode | |
| user space | espaço de usuário | | |
| process | processo | | |
| multitasking | multitarefa | | |
| scheduling | escalonamento | agendamento / scheduling | |
| scheduler | escalonador | agendador | |
| cooperative scheduling | escalonamento cooperativo | | |
| preemptive scheduling | escalonamento preemptivo | | |
| system call | chamada de sistema | chamada ao sistema / chamada do sistema / syscall | |
| file system | sistema de arquivos | sistema de ficheiros / sistema de arquivo | |
| virtual file system | sistema de arquivos virtual | | sigla VFS |
| directory | diretório | | |
| mount | montar | | "montar um sistema de arquivos em `/dev`" |
| major/minor device number | número de dispositivo maior/menor | | ao definir: (_major/minor_) |
| path | caminho | | caminho de arquivo (`/dev`) |
| metadata | metadados | | |
| read-only | somente leitura | | |
| writable | gravável | | |
| device | dispositivo | | |
| keyboard | teclado | | |
| serial port | porta serial | | |
| timer | temporizador | | |
| Programmable Interval Timer | temporizador de intervalo programável | | sigla PIT |
| Programmable Interrupt Controller | controlador de interrupção programável | | sigla PIC |
| divider | divisor | | |
| baud rate | taxa de baud | | |
| parity bit | bit de paridade | | |
| stop bit | bit de parada | | |
| data bits | bits de dados | | |
| FIFO queue | fila FIFO | | |
| foreground | primeiro plano | | "cor de primeiro plano" |
| background | plano de fundo | | "cor de fundo" |
| cursor | cursor | | |
| line command port | porta de comando da linha | | porta de E/S da porta serial; ao definir: (*line command port*) |
| cell | célula | | célula de 16 bits do framebuffer |
| spinning | laço de espera | | "ficar em laço de espera (*spinning*)" (busy-wait) |
| row | linha | | posição do cursor/framebuffer |
| column | coluna | | |
| magic number | número mágico | | |
| multiboot specification | especificação multiboot | | |
| module | módulo | | "módulos do GRUB" |
| pair-programming | programação em par | | ao definir: (*pair programming*) |
| power-on self-test | autoteste de inicialização | | ao definir: (*power-on self-test*) |
| Further Reading | Leitura Complementar | Leitura Adicional | título de seção; vale também para "Further reading" |
| folder | pasta | | o original usa "folder" para diretório em comandos de shell; "diretório" também é aceito |
| media | mídia | | mídia de armazenamento (CD, ISO, disquete) |
| file | arquivo | ficheiro | evita pt-PT |
| user | usuário | utilizador | evita pt-PT |
| screen | tela | ecrã | evita pt-PT |

## Nomes de capítulos (títulos oficiais)

Ver a tabela de `STATUS.md`. Ao citar um capítulo pelo nome, use o título de lá,
mesmo que aquele capítulo ainda não tenha sido traduzido.

## Dúvidas em aberto

Termos em que a decisão ainda é provisória. Quem decidir, mova para uma das
tabelas acima e apague daqui.

- *"reader"*: o livro fala muito de "the reader". Como o gênero de quem lê é
  desconhecido, preferir construções neutras ("quem lê", "você", a pessoa
  que está lendo). Ver `GUIA-DE-ESTILO.md`.
