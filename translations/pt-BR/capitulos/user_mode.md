# Modo Usuário {#user-mode}

O modo usuário já está quase ao nosso alcance: faltam só mais alguns passos.
Embora esses passos pareçam fáceis do jeito que são apresentados neste
capítulo, podem ser difíceis de implementar, pois há muitos lugares em que
pequenos erros causam bugs difíceis de achar.

## Segmentos para o Modo Usuário {#segments-for-user-mode}

Para habilitar o modo usuário, precisamos adicionar mais dois segmentos à GDT.
Eles são muito parecidos com os segmentos do kernel que adicionamos quando
[configuramos a GDT](#the-global-descriptor-table-gdt) no [capítulo sobre
segmentação](#segmentation):

 Índice  Desloc.   Nome                 Faixa de endereços        Tipo   DPL
-------  -------   -------------------  ------------------------- -----  ----
      3   `0x18`   código do usuário    `0x00000000 - 0xFFFFFFFF` RX     PL3
      4   `0x20`   dados do usuário     `0x00000000 - 0xFFFFFFFF` RW     PL3

Table: Os descritores de segmento necessários para o modo usuário.

A diferença é o DPL, que agora permite que o código execute em PL3. Os
segmentos ainda podem ser usados para endereçar todo o espaço de endereçamento;
usar apenas esses segmentos para o código em modo usuário não protege o kernel.
Para isso precisamos da paginação.

## Preparando-se para o Modo Usuário {#setting-up-for-user-mode}

Todo processo em modo usuário precisa de algumas coisas:

- Quadros de página para código, dados e pilha. Por ora basta alocar um quadro
  de página para a pilha e quadros de página suficientes para caber o código do
  programa. Não se preocupe em configurar uma pilha que possa crescer e
  encolher neste momento: concentre-se em fazer funcionar uma implementação
  básica primeiro.

- O binário do módulo do GRUB precisa ser copiado para os quadros de página
  usados para o código do programa.

- São necessários um diretório de páginas e tabelas de páginas para mapear na
  memória os quadros de página descritos acima. São necessárias pelo menos duas
  tabelas de páginas, porque o código e os dados devem ser mapeados a partir de
  `0x00000000`, em ordem crescente, e a pilha deve começar logo abaixo do
  kernel, em `0xBFFFFFFB`, crescendo em direção a endereços menores. A flag U/S
  precisa estar ligada para permitir o acesso em PL3.

Pode ser conveniente guardar essas informações numa `struct` que represente um
processo. Essa `struct` de processo pode ser alocada dinamicamente com a função
`malloc` do kernel.

## Entrando no Modo Usuário {#entering-user-mode}

A única forma de executar código com um nível de privilégio mais baixo do que o
nível de privilégio atual (CPL) é executar uma instrução `iret` ou `lret` --
retorno de interrupção ou retorno longo, respectivamente.

Para entrar no modo usuário, montamos a pilha como se o processador tivesse
gerado uma interrupção entre níveis de privilégio. A pilha deve ficar assim:

~~~
    [esp + 16]  ss      ; the stack segment selector we want for user mode
    [esp + 12]  esp     ; the user mode stack pointer
    [esp +  8]  eflags  ; the control flags we want to use in user mode
    [esp +  4]  cs      ; the code segment selector
    [esp +  0]  eip     ; the instruction pointer of user mode code to execute
~~~

Veja o manual da Intel [@intel3a], seção 6.2.1, figura 6-4, para mais
informações.

A instrução `iret` então lê esses valores da pilha e preenche os registradores
correspondentes. Antes de executar `iret`, precisamos trocar para o diretório de
páginas que configuramos para o processo em modo usuário. É importante lembrar
que, para continuar executando código do kernel depois de trocar a PDT, o
kernel precisa estar mapeado. Uma forma de conseguir isso é ter uma PDT separada
para o kernel, que mapeia todos os dados em `0xC0000000` e acima, e combiná-la
com a PDT do usuário (que só mapeia abaixo de `0xC0000000`) na hora de fazer a
troca. Lembre-se de que o endereço físico da PDT é que deve ser usado ao
definir o registrador `cr3`.

O registrador `eflags` contém um conjunto de flags diferentes, descritas na
seção 2.3 do manual da Intel [@intel3a]. A mais importante para nós é a flag de
habilitação de interrupções (IF). A instrução assembly `sti` não pode ser usada
no nível de privilégio 3 para habilitar interrupções. Se as interrupções
estiverem desabilitadas ao entrar no modo usuário, elas não poderão ser
habilitadas depois que o modo usuário for iniciado. Ligar a flag IF no valor de
`eflags` que está na pilha habilitará as interrupções no modo usuário, já que a
instrução assembly `iret` define o registrador `eflags` com o valor
correspondente da pilha.

Por enquanto, devemos deixar as interrupções desabilitadas, pois é preciso um
pouco mais de trabalho para fazer as interrupções entre níveis de privilégio
funcionarem direito (veja a seção ["Chamadas de Sistema"](#system-calls)).

O valor `eip` na pilha deve apontar para o ponto de entrada do código de usuário
- `0x00000000`, no nosso caso. O valor `esp` na pilha deve ser o lugar
onde a pilha começa -- `0xBFFFFFFB` (`0xC0000000 - 4`).

Os valores `cs` e `ss` na pilha devem ser os seletores de segmento dos
segmentos de código e de dados do usuário, respectivamente. Como vimos no
[capítulo de segmentação](#loading-the-gdt), os dois bits menos significativos
de um seletor de segmento formam o RPL -- o nível de privilégio requisitado
(_Requested Privilege Level_). Ao usar `iret` para entrar em PL3, o RPL de `cs`
e de `ss` deve ser `0x3`. O código a seguir mostra um exemplo:

~~~ {.nasm}
    USER_MODE_CODE_SEGMENT_SELECTOR equ 0x18
    USER_MODE_DATA_SEGMENT_SELECTOR equ 0x20
    mov cs, USER_MODE_CODE_SEGMENT_SELECTOR | 0x3
    mov ss, USER_MODE_DATA_SEGMENT_SELECTOR | 0x3
~~~

O registrador `ds`, e os demais registradores de segmento de dados, devem ser
definidos com o mesmo seletor de segmento de `ss`. Eles podem ser definidos do
jeito normal, com a instrução assembly `mov`.

Agora estamos prontos para executar `iret`. Se tudo foi configurado direito,
já devemos ter um kernel capaz de entrar no modo usuário.

## Usando C em Programas do Modo Usuário {#using-c-for-user-mode-programs}

Quando C é usada como linguagem de programação dos programas em modo usuário, é
importante pensar na estrutura do arquivo que resultará da compilação.

O motivo pelo qual podemos usar o ELF [@wiki:elf] como formato de arquivo do
executável do kernel é que o GRUB sabe analisar e interpretar o formato ELF. Se
implementássemos um parser de ELF, poderíamos compilar os programas em modo
usuário também como binários ELF. Deixamos isso como exercício para quem lê.

Uma coisa que podemos fazer para facilitar o desenvolvimento de programas em
modo usuário é permitir que os programas sejam escritos em C, mas compilá-los
como binários planos em vez de binários ELF. Em C, o layout do código gerado é
mais imprevisível, e o ponto de entrada, `main`, pode não estar no deslocamento
0 do binário. Uma forma comum de contornar isso é acrescentar, no deslocamento
0, algumas linhas de código assembly que chamem `main`:

~~~ {.nasm}
    extern main

    section .text
        ; push argv
        ; push argc
        call main
        ; main has returned, eax is return value
        jmp  $    ; loop forever
~~~

Se esse código for salvo num arquivo chamado `start.s`, o código a seguir mostra
um exemplo de script do linker que coloca essas instruções primeiro no
executável (lembre-se de que `start.s` é compilado para `start.o`):

~~~
    OUTPUT_FORMAT("binary")    /* output flat binary */

    SECTIONS
    {
        . = 0;                 /* relocate to address 0 */

        .text ALIGN(4):
        {
            start.o(.text)     /* include the .text section of start.o */
            *(.text)           /* include all other .text sections */
        }

        .data ALIGN(4):
        {
            *(.data)
        }

        .rodata ALIGN(4):
        {
            *(.rodata*)
        }
    }
~~~

_Observação_: `*(.text)` não vai incluir de novo a seção `.text` de `start.o`.

Com esse script, podemos escrever programas em C ou em assembler (ou em qualquer
outra linguagem que compile para arquivos objeto que o `ld` consiga linkar), e
fica fácil para o kernel carregá-los e mapeá-los (a seção `.rodata`, porém, será
mapeada como gravável).

Ao compilar os programas de usuário, queremos as seguintes flags do GCC:

~~~
    -m32 -nostdlib -nostdinc -fno-builtin -fno-stack-protector -nostartfiles
    -nodefaultlibs
~~~

Para a linkagem, devem ser usadas as flags a seguir:

~~~
    -T link.ld -melf_i386  # emulate 32 bits ELF, the binary output is specified
                           # in the linker script
~~~

A opção `-T` instrui o linker a usar o script do linker `link.ld`.

### Uma Biblioteca C {#a-c-library}

Agora pode ser interessante começar a pensar em escrever uma pequena "biblioteca
padrão" para os seus programas. Parte da funcionalidade exige [chamadas de
sistema](#system-calls) para funcionar, mas outra parte, como as funções de
`string.h`, não exige.

## Leitura Complementar {#further-reading-8}

- Gustavo Duarte escreveu um artigo sobre níveis de privilégio:
  <http://duartes.org/gustavo/blog/post/cpu-rings-privilege-and-protection>
