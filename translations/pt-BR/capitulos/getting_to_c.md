# Chegando ao C {#getting-to-c}
Este capítulo vai mostrar como usar C, em vez de código assembly, como a
linguagem de programação do SO. O assembly é ótimo para interagir com a CPU e
dá o máximo de controle sobre cada aspecto do código. No entanto, pelo menos
para quem escreve este livro, C é uma linguagem muito mais conveniente.
Por isso, queremos usar C o máximo possível e deixar o código assembly só
para onde ele fizer sentido.

## Configurando uma Pilha {#setting-up-a-stack}
Um pré-requisito para usar C é uma pilha, já que todo programa em C que não seja
trivial usa uma. Configurar uma pilha não é mais difícil do que fazer o
registrador `esp` apontar para o fim de uma área de memória livre (lembre que,
no x86, a pilha cresce em direção aos endereços mais baixos) e corretamente
alinhada (do ponto de vista de desempenho, recomenda-se o alinhamento em 4
bytes).

Poderíamos apontar `esp` para uma área qualquer da memória, já que, até agora,
as únicas coisas na memória são o GRUB, a BIOS, o kernel do SO e alguma E/S
mapeada em memória. Mas não é uma boa ideia -- não sabemos quanta memória está
disponível, nem se a área para a qual `esp` apontaria está sendo usada por
outra coisa. Uma ideia melhor é reservar um pedaço de memória não inicializada
na seção `bss` do arquivo ELF do kernel. É melhor usar a seção `bss` do que a
seção `data`, para reduzir o tamanho do executável do SO. Como o GRUB entende
ELF, ele vai alocar toda a memória reservada na seção `bss` ao carregar o SO.

A pseudoinstrução `resb` do NASM [@resb] pode ser usada para declarar dados não
inicializados:

~~~ {.nasm}
    KERNEL_STACK_SIZE equ 4096                  ; size of stack in bytes

    section .bss
    align 4                                     ; align at 4 bytes
    kernel_stack:                               ; label points to beginning of memory
        resb KERNEL_STACK_SIZE                  ; reserve stack for the kernel
~~~

Não há motivo para se preocupar com o uso de memória não inicializada para a
pilha, pois não é possível ler uma posição da pilha que não tenha sido escrita
(sem mexer manualmente nos ponteiros). Um programa (correto) não consegue
desempilhar um elemento sem antes ter empilhado algum. Portanto,
as posições de memória da pilha sempre serão escritas antes de serem lidas.

O ponteiro de pilha é então configurado fazendo `esp` apontar para o fim da
memória de `kernel_stack`:

~~~ {.nasm}
    mov esp, kernel_stack + KERNEL_STACK_SIZE   ; point esp to the start of the
                                                ; stack (end of memory area)
~~~

## Chamando Código C a Partir do Assembly {#calling-c-code-from-assembly}
O próximo passo é chamar uma função C a partir do código assembly. Existem
muitas convenções diferentes para chamar código C a partir de código assembly
[@wiki:ccall]. Este livro usa a convenção de chamada _cdecl_, por ser a usada
pelo GCC. A convenção cdecl determina que os argumentos de uma função sejam
passados pela pilha (no x86). Os argumentos da função devem ser empilhados da
direita para a esquerda, ou seja, o argumento mais à direita é empilhado
primeiro. O valor de retorno da função é colocado no registrador `eax`. O
código a seguir mostra um exemplo:

~~~ {.c}
    /* The C function */
    int sum_of_three(int arg1, int arg2, int arg3)
    {
        return arg1 + arg2 + arg3;
    }
~~~

~~~ {.nasm}
    ; The assembly code
    extern sum_of_three   ; the function sum_of_three is defined elsewhere

    push dword 3            ; arg3
    push dword 2            ; arg2
    push dword 1            ; arg1
    call sum_of_three       ; call the function, the result will be in eax
~~~

### Empacotando Structs {#packing-structs}
No restante deste livro, você vai encontrar com frequência "bytes de
configuração", que são um conjunto de bits em uma ordem bem específica. Abaixo
está um exemplo com 32 bits:

    Bit:     | 31     24 | 23          8 | 7     0 |
    Content: | index     | address       | config  |

Em vez de usar um inteiro sem sinal, `unsigned int`, para lidar com essas
configurações, é muito mais conveniente usar "estruturas empacotadas":

~~~ {.C}
    struct example {
        unsigned char config;   /* bit 0 - 7   */
        unsigned short address; /* bit 8 - 23  */
        unsigned char index;    /* bit 24 - 31 */
    };
~~~

Ao usar a `struct` do exemplo anterior, não há garantia de que o tamanho da
`struct` seja exatamente 32 bits -- o compilador pode acrescentar algum padding entre os
elementos por vários motivos, por exemplo para acelerar o acesso aos elementos
ou por exigências do hardware e/ou do compilador. Quando uma `struct` é usada
para representar bytes de configuração, é muito importante que o compilador
_não_ acrescente nenhum padding, porque a `struct` acabará sendo tratada pelo
hardware como um inteiro sem sinal de 32 bits. O atributo `packed` pode ser
usado para forçar o GCC a _não_ acrescentar nenhum padding:

~~~ {.C}
    struct example {
        unsigned char config;   /* bit 0 - 7   */
        unsigned short address; /* bit 8 - 23  */
        unsigned char index;    /* bit 24 - 31 */
    } __attribute__((packed));
~~~

Observe que `__attribute__((packed))` não faz parte do padrão C -- pode não
funcionar com todos os compiladores de C.

## Compilando Código C {#compiling-c-code}
Ao compilar o código C do SO, é preciso usar várias flags do GCC. Isso porque o
código C _não_ deve presumir a existência de uma biblioteca padrão, já que não
há nenhuma biblioteca padrão disponível para o nosso SO. Para mais informações
sobre as flags, consulte o manual do GCC.

As flags usadas para compilar o código C são:

~~~
    -m32 -nostdlib -nostdinc -fno-builtin -fno-stack-protector -nostartfiles
    -nodefaultlibs
~~~

Como sempre ao escrever programas em C, recomendamos ativar todos os avisos e
tratar os avisos como erros:

~~~
    -Wall -Wextra -Werror
~~~

Agora você pode criar uma função `kmain` em um arquivo chamado `kmain.c` e
chamá-la a partir de `loader.s`. Neste ponto, `kmain` provavelmente não vai
precisar de argumentos (mas nos próximos capítulos vai).

## Ferramentas de Build {#build-tools}
Este também é provavelmente um bom momento para configurar algumas ferramentas
de build, para facilitar a compilação e o teste do SO. Recomendamos usar o
`make` [@make], mas há muitos outros sistemas de build disponíveis. Um Makefile
simples para o SO poderia ser como o do exemplo a seguir:

~~~ {.Makefile}
    OBJECTS = loader.o kmain.o
    CC = gcc
    CFLAGS = -m32 -nostdlib -nostdinc -fno-builtin -fno-stack-protector \
             -nostartfiles -nodefaultlibs -Wall -Wextra -Werror -c
    LDFLAGS = -T link.ld -melf_i386
    AS = nasm
    ASFLAGS = -f elf

    all: kernel.elf

    kernel.elf: $(OBJECTS)
        ld $(LDFLAGS) $(OBJECTS) -o kernel.elf

    os.iso: kernel.elf
        cp kernel.elf iso/boot/kernel.elf
        genisoimage -R                              \
                    -b boot/grub/stage2_eltorito    \
                    -no-emul-boot                   \
                    -boot-load-size 4               \
                    -A os                           \
                    -input-charset utf8             \
                    -quiet                          \
                    -boot-info-table                \
                    -o os.iso                       \
                    iso

    run: os.iso
        bochs -f bochsrc.txt -q

    %.o: %.c
        $(CC) $(CFLAGS)  $< -o $@

    %.o: %.s
        $(AS) $(ASFLAGS) $< -o $@

    clean:
        rm -rf *.o kernel.elf os.iso
~~~

O conteúdo do seu diretório de trabalho agora deve ficar como na figura a
seguir:

~~~
    .
    |-- bochsrc.txt
    |-- iso
    |   |-- boot
    |     |-- grub
    |       |-- menu.lst
    |       |-- stage2_eltorito
    |-- kmain.c
    |-- loader.s
    |-- Makefile
~~~

Agora você deve conseguir iniciar o SO com o simples comando `make run`, que
vai compilar o kernel e dar boot nele no Bochs (conforme definido no Makefile
acima).

## Leitura Complementar {#further-reading-1}

- O livro de Kernighan e Ritchie, _The C Programming Language, Second Edition_,
  [@knr] é ótimo para aprender todos os aspectos de C.
