# Interrupções e Entrada {#interrupts-and-input}

Agora que o SO consegue produzir _saída_, seria bom que ele também pudesse
receber alguma _entrada_. (O sistema operacional precisa saber tratar
_interrupções_ para ler informações do teclado.) Uma interrupção ocorre quando
um dispositivo de hardware, como o teclado, a porta serial ou o temporizador,
avisa à CPU que o estado do dispositivo mudou. A própria CPU também pode gerar
interrupções por causa de erros de programa, por exemplo quando um programa
referencia memória à qual não tem acesso, ou quando divide um número por zero.
Por fim, existem as _interrupções de software_, que são causadas pela
instrução assembly `int` e costumam ser usadas para chamadas de sistema.

## Tratadores de Interrupção {#interrupts-handlers}

As interrupções são tratadas por meio da _tabela de descritores de interrupção_
(_Interrupt Descriptor Table_, IDT). A IDT descreve um tratador para cada
interrupção. As interrupções são numeradas (0 - 255) e o tratador da interrupção
_i_ é definido na _i_-ésima posição da tabela. Há três tipos diferentes de
tratadores de interrupção:

- Tratador de tarefa
- Tratador de interrupção
- Tratador de trap

Os tratadores de tarefa usam uma funcionalidade específica da versão Intel do
x86, então não vamos tratar deles aqui (veja o manual da Intel [@intel3a],
capítulo 6, para mais informações). A única diferença entre um tratador de
interrupção e um tratador de trap é que o tratador de interrupção desabilita as
interrupções, o que significa que não é possível receber uma interrupção
enquanto outra está sendo tratada. Neste livro, vamos usar tratadores de trap e
desabilitar as interrupções manualmente quando for preciso.

## Criando uma Entrada na IDT {#creating-an-entry-in-the-idt}

Uma entrada na IDT para um tratador de interrupção tem 64 bits. Os 32 bits mais
altos aparecem na figura abaixo:

    Bit:     | 31              16 | 15 | 14 13 | 12 | 11 | 10 9 8 | 7 6 5 | 4 3 2 1 0 |
    Content: | offset high        | P  | DPL   | 0  | D  | 1  1 0 | 0 0 0 | reserved  |

Os 32 bits mais baixos aparecem na figura a seguir:

    Bit:     | 31              16 | 15              0 |
    Content: | segment selector   | offset low        |

A descrição de cada nome está na tabela abaixo:

             Name Description
----------------- ------------
      offset high Os 16 bits mais altos do endereço de 32 bits dentro do segmento.
       offset low Os 16 bits mais baixos do endereço de 32 bits dentro do segmento.
                p Indica se o tratador está presente na memória ou não (1 = presente, 0 = ausente).
              DPL Nível de privilégio do descritor, o nível de privilégio a partir do qual o tratador pode ser chamado (0, 1, 2, 3).
                D Tamanho do gate (1 = 32 bits, 0 = 16 bits).
 segment selector O deslocamento na GDT.
                r Reservado.

O deslocamento é um ponteiro para código (de preferência, um label de assembly).
Por exemplo, para criar uma entrada para um tratador cujo código começa em
`0xDEADBEEF` e que executa no nível de privilégio 0 (portanto usando o mesmo
seletor de segmento de código do kernel), seriam usados os dois valores de 32
bits a seguir:

~~~
    0xDEAD8E00
    0x0008BEEF
~~~

Se a IDT for representada como um `unsigned integer idt[512]`, então, para
registrar o exemplo acima como tratador da interrupção 0 (divisão por zero),
seria usado o código a seguir:

~~~ {.c}
    idt[0] = 0xDEAD8E00
    idt[1] = 0x0008BEEF
~~~

Como está escrito no capítulo ["Chegando ao C"](#getting-to-c), recomendamos
que, em vez de usar bytes (ou inteiros sem sinal), você use structs empacotadas
para deixar o código mais legível.

## Tratando uma Interrupção {#handling-an-interrupt}

Quando ocorre uma interrupção, a CPU empilha algumas informações sobre ela,
procura o tratador de interrupção apropriado na IDT e salta para ele. A pilha
no momento da interrupção terá o seguinte aspecto:

~~~
    [esp + 12] eflags
    [esp + 8]  cs
    [esp + 4]  eip
    [esp]      error code?
~~~

O ponto de interrogação depois de "error code" está ali porque nem todas as
interrupções geram um _código de erro_. As interrupções da CPU que colocam um
código de erro na pilha são as de número 8, 10, 11, 12, 13, 14 e 17. O tratador
de interrupção pode usar o código de erro para obter mais informações sobre o
que aconteceu. Note também que o _número_ da interrupção _não_ é empilhado.
Só conseguimos descobrir qual interrupção ocorreu sabendo qual código está
sendo executado -- se o tratador registrado para a interrupção 17 está em
execução, então ocorreu a interrupção 17.

Quando o tratador de interrupção termina, ele usa a instrução `iret` para
retornar. A instrução `iret` espera que a pilha esteja igual à do momento da
interrupção (veja a figura acima). Portanto, todos os valores que o tratador de
interrupção empilhou precisam ser desempilhados. Antes de retornar, `iret`
restaura `eflags` desempilhando o valor da pilha e, por fim, salta para
`cs:eip`, conforme os valores que estão na pilha.

O tratador de interrupção precisa ser escrito em assembly, já que todos os
registradores que ele usa precisam ser preservados, empilhando-os. Isso porque o
código que foi interrompido não sabe da interrupção e, portanto, espera que seus
registradores continuem iguais. Escrever toda a lógica do tratador de
interrupção em assembly seria cansativo. Uma boa ideia é criar em assembly um
tratador que salva os registradores, chama uma função C, restaura os
registradores e, por fim, executa `iret`!

O tratador em C deve receber como argumentos o estado dos registradores, o
estado da pilha e o número da interrupção. As definições a seguir podem ser
usadas, por exemplo:

~~~ {.c}
    struct cpu_state {
        unsigned int eax;
        unsigned int ebx;
        unsigned int ecx;
        .
        .
        .
        unsigned int esp;
    } __attribute__((packed));

    struct stack_state {
        unsigned int error_code;
        unsigned int eip;
        unsigned int cs;
        unsigned int eflags;
    } __attribute__((packed));

    void interrupt_handler(struct cpu_state cpu, struct stack_state stack, unsigned int interrupt);
~~~

## Criando um Tratador de Interrupção Genérico {#creating-a-generic-interrupt-handler}

Como a CPU não empilha o número da interrupção, escrever um tratador de
interrupção genérico é um pouco complicado. Esta seção usa macros para mostrar
como isso pode ser feito. Escrever uma versão para cada interrupção é
trabalhoso -- é melhor usar a funcionalidade de macros do NASM [@nasm:macros].
E, como nem todas as interrupções produzem um código de erro, o valor 0 será
acrescentado como "código de erro" das interrupções que não têm um. O código a
seguir mostra um exemplo de como fazer isso:

~~~ {.nasm}
    %macro no_error_code_interrupt_handler %1
    global interrupt_handler_%1
    interrupt_handler_%1:
        push    dword 0                     ; push 0 as error code
        push    dword %1                    ; push the interrupt number
        jmp     common_interrupt_handler    ; jump to the common handler
    %endmacro

    %macro error_code_interrupt_handler %1
    global interrupt_handler_%1
    interrupt_handler_%1:
        push    dword %1                    ; push the interrupt number
        jmp     common_interrupt_handler    ; jump to the common handler
    %endmacro

    common_interrupt_handler:               ; the common parts of the generic interrupt handler
        ; save the registers
        push    eax
        push    ebx
        .
        .
        .
        push    ebp

        ; call the C function
        call    interrupt_handler

        ; restore the registers
        pop     ebp
        .
        .
        .
        pop     ebx
        pop     eax

        ; restore the esp
        add     esp, 8

        ; return to the code that got interrupted
        iret

    no_error_code_interrupt_handler 0       ; create handler for interrupt 0
    no_error_code_interrupt_handler 1       ; create handler for interrupt 1
    .
    .
    .
    error_code_handler              7       ; create handler for interrupt 7
    .
    .
    .
~~~

O `common_interrupt_handler` faz o seguinte:

- Empilha os registradores.
- Chama a função C `interrupt_handler`.
- Desempilha os registradores.
- Soma 8 a `esp` (por causa do código de erro e do número da interrupção
  empilhados antes).
- Executa `iret` para retornar ao código interrompido.

Como as macros declaram labels globais, os endereços dos tratadores de
interrupção podem ser acessados a partir de C ou de assembly na hora de criar a
IDT.

## Carregando a IDT {#loading-the-idt}

A IDT é carregada com a instrução assembly `lidt`, que recebe o endereço do
primeiro elemento da tabela. O mais fácil é encapsular essa instrução e usá-la
a partir de C:

~~~ {.nasm}
    global  load_idt

    ; load_idt - Loads the interrupt descriptor table (IDT).
    ; stack: [esp + 4] the address of the first entry in the IDT
    ;        [esp    ] the return address
    load_idt:
        mov     eax, [esp+4]    ; load the address of the IDT into register eax
        lidt    eax             ; load the IDT
        ret                     ; return to the calling function
~~~

## Controlador de Interrupção Programável (PIC) {#programmable-interrupt-controller-pic}

Para começar a usar interrupções de hardware, primeiro é preciso configurar o
controlador de interrupção programável (_Programmable Interrupt Controller_,
PIC). O PIC permite mapear sinais do hardware para interrupções. Os motivos para
configurar o PIC são:

- Remapear as interrupções. Por padrão, o PIC usa as interrupções 0 - 15 para
  interrupções de hardware, o que entra em conflito com as interrupções da CPU.
  Por isso, as interrupções do PIC precisam ser remapeadas para outro intervalo.
- Escolher quais interrupções receber. Provavelmente você não quer receber
  interrupções de todos os dispositivos, já que de qualquer forma não tem código
  para tratá-las.
- Configurar o modo correto do PIC.

No começo havia apenas um PIC (PIC 1) e oito interrupções. Conforme mais
hardware foi sendo acrescentado, 8 interrupções ficaram poucas. A solução
adotada foi encadear outro PIC (PIC 2) ao primeiro (veja a interrupção 2 do
PIC 1).

As interrupções de hardware aparecem na tabela abaixo:

 PIC 1 Hardware     PIC 2 Hardware
------ ---------   ------ ---------
     0 Temporizador     8 Relógio de Tempo Real
     1 Teclado          9 E/S Geral
     2 PIC 2           10 E/S Geral
     3 COM 2           11 E/S Geral
     4 COM 1           12 E/S Geral
     5 LPT 2           13 Coprocessador
     6 Disquete        14 Barramento IDE
     7 LPT 1           15 Barramento IDE

Um ótimo tutorial para configurar o PIC pode ser encontrado no site do SigOPS
[@acm]. Não vamos repetir essas informações aqui.

Toda interrupção vinda do PIC precisa ser confirmada (_acknowledged_) -- ou
seja, é preciso enviar ao PIC uma mensagem confirmando que a interrupção foi
tratada. Se isso não for feito, o PIC não gera mais nenhuma interrupção.

Confirmar uma interrupção do PIC é feito enviando o byte `0x20` ao PIC que
gerou a interrupção. Assim, uma função `pic_acknowledge` pode ser implementada
da seguinte forma:

~~~ {.c}
    #include "io.h"

    #define PIC1_PORT_A 0x20
    #define PIC2_PORT_A 0xA0

    /* The PIC interrupts have been remapped */
    #define PIC1_START_INTERRUPT 0x20
    #define PIC2_START_INTERRUPT 0x28
    #define PIC2_END_INTERRUPT   PIC2_START_INTERRUPT + 7

    #define PIC_ACK     0x20

    /** pic_acknowledge:
     *  Acknowledges an interrupt from either PIC 1 or PIC 2.
     *
     *  @param num The number of the interrupt
     */
    void pic_acknowledge(unsigned integer interrupt)
    {
        if (interrupt < PIC1_START_INTERRUPT || interrupt > PIC2_END_INTERRUPT) {
          return;
        }

        if (interrupt < PIC2_START_INTERRUPT) {
          outb(PIC1_PORT_A, PIC_ACK);
        } else {
          outb(PIC2_PORT_A, PIC_ACK);
        }
    }
~~~

## Lendo a Entrada do Teclado {#reading-input-from-the-keyboard}

O teclado não gera caracteres ASCII, ele gera scan codes. Um scan code
representa um botão -- tanto os pressionamentos quanto as solturas. O scan code
que representa o botão que acabou de ser pressionado pode ser lido da porta de
E/S de dados do teclado, que tem o endereço `0x60`. O exemplo a seguir mostra
como isso pode ser feito:

~~~ {.c}
    #include "io.h"

    #define KBD_DATA_PORT   0x60

    /** read_scan_code:
     *  Reads a scan code from the keyboard
     *
     *  @return The scan code (NOT an ASCII character!)
     */
    unsigned char read_scan_code(void)
    {
        return inb(KBD_DATA_PORT);
    }
~~~

O próximo passo é escrever uma função que traduza um scan code no caractere
ASCII correspondente. Se você quiser mapear os scan codes para caracteres ASCII
como é feito em um teclado americano, Andries Brouwer tem um ótimo tutorial
[@scancodes].

Lembre-se: como a interrupção do teclado é gerada pelo PIC, você deve chamar
`pic_acknowledge` no final do tratador de interrupção do teclado. Além disso, o
teclado não enviará mais nenhuma interrupção até que você leia o scan code do
teclado.

## Leitura Complementar {#further-reading-4}

- A wiki do OSDev tem uma ótima página sobre interrupções,
  <http://wiki.osdev.org/Interrupts>
- O capítulo 6 do Manual 3a da Intel [@intel3a] descreve tudo o que há para
  saber sobre interrupções.
