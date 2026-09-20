# Alocação de Quadros de Página {#page-frame-allocation}

Ao usar memória virtual, como o SO sabe quais partes da memória estão livres
para uso? Esse é o papel do alocador de quadros de página.

## Gerenciando a Memória Disponível {#managing-available-memory}

### Quanta Memória Existe? {#how-much-memory-is-there}

Primeiro precisamos saber quanta memória está disponível no computador em que o
SO está rodando.
O jeito mais fácil de descobrir isso é lê-la da estrutura multiboot
[@multiboot] que o GRUB nos passa. O GRUB coleta as informações de que
precisamos sobre a memória -- o que é reservado, mapeado em E/S, somente
leitura etc. Também precisamos garantir que a parte da memória usada pelo
kernel não seja marcada como livre (já que o GRUB não marca essa memória como
reservada). Uma forma de saber quanta memória o kernel usa é exportar labels no
início e no fim do binário do kernel a partir do script do linker:

~~~
    ENTRY(loader)           /* the name of the entry symbol */

    . = 0xC0100000          /* the code should be relocated to 3 GB + 1 MB */

    /* these labels get exported to the code files */
    kernel_virtual_start = .;
    kernel_physical_start = . - 0xC0000000;

    /* align at 4 KB and load at 1 MB */
    .text ALIGN (0x1000) : AT(ADDR(.text)-0xC0000000)
    {
        *(.text)            /* all text sections from all files */
    }

    /* align at 4 KB and load at 1 MB + . */
    .rodata ALIGN (0x1000) : AT(ADDR(.rodata)-0xC0000000)
    {
        *(.rodata*)         /* all read-only data sections from all files */
    }

    /* align at 4 KB and load at 1 MB + . */
    .data ALIGN (0x1000) : AT(ADDR(.data)-0xC0000000)
    {
        *(.data)            /* all data sections from all files */
    }

    /* align at 4 KB and load at 1 MB + . */
    .bss ALIGN (0x1000) : AT(ADDR(.bss)-0xC0000000)
    {
        *(COMMON)           /* all COMMON sections from all files */
        *(.bss)             /* all bss sections from all files */
    }

    kernel_virtual_end = .;
    kernel_physical_end = . - 0xC0000000;
~~~

Essas labels podem ser lidas diretamente do código assembly e colocadas na
pilha, para ficarem disponíveis ao código C:

~~~ {.nasm}
    extern kernel_virtual_start
    extern kernel_virtual_end
    extern kernel_physical_start
    extern kernel_physical_end

    ; ...

    push kernel_physical_end
    push kernel_physical_start
    push kernel_virtual_end
    push kernel_virtual_start

    call kmain
~~~

Assim recebemos as labels como argumentos de `kmain`. Se você quiser usar C em
vez de código assembly, uma forma de fazer isso é declarar as labels como
funções e pegar os endereços dessas funções:

~~~ {.c}
    void kernel_virtual_start(void);

    /* ... */

    unsigned int vaddr = (unsigned int) &kernel_virtual_start;
~~~

Se você usar módulos do GRUB, é preciso garantir que a memória que eles usam
também seja marcada como reservada.

Note que a memória disponível não precisa ser contígua. No primeiro 1 MB há
várias seções de memória mapeadas em E/S, além da memória usada pelo GRUB e
pela BIOS. Outras partes da memória também podem estar indisponíveis de forma
parecida.

É conveniente dividir as seções de memória em quadros de página completos, já
que não podemos mapear em memória apenas parte de uma página.

### Gerenciando a Memória Disponível {#managing-available-memory-1}

Como saber quais quadros de página estão em uso? O alocador de quadros de
página precisa controlar quais estão livres e quais não estão. Há várias formas
de fazer isso: bitmaps, listas encadeadas, árvores, o Buddy System (usado pelo
Linux) etc.
Para mais informações sobre os diferentes algoritmos, veja o artigo da OSDev
[@osdev:pfa].

Bitmaps são bem fáceis de implementar. Usa-se um bit para cada quadro de página,
e um (ou mais) quadros de página são dedicados a armazenar o bitmap. (Note que
essa é só uma das formas de fazer; outros projetos podem ser melhores e/ou mais
divertidos de implementar.)

## Como Podemos Acessar um Quadro de Página? {#how-can-we-access-a-page-frame}

O alocador de quadros de página devolve o endereço físico de início do quadro
de página. Esse quadro de página não está mapeado: nenhuma tabela de páginas
aponta para ele. Como podemos ler e gravar dados no quadro?

Precisamos mapear o quadro de página na memória virtual, atualizando o PDT e/ou
a PT usados pelo kernel. E se todas as tabelas de páginas disponíveis estiverem
cheias? Então não conseguimos mapear o quadro de página na memória, porque
precisaríamos de uma nova tabela de páginas -- que ocupa um quadro de página
inteiro -- e, para gravar nesse quadro de página, precisaríamos mapear o
quadro dele... De algum modo, essa dependência circular precisa ser quebrada.

Uma solução é reservar uma parte da primeira tabela de páginas usada pelo kernel
(ou de alguma outra tabela de páginas da metade superior) para mapear
temporariamente quadros de página e torná-los acessíveis. Se o kernel está
mapeado em `0xC0000000` (a entrada do diretório de páginas de índice 768) e são
usados quadros de página de 4 KB, então o kernel tem pelo menos uma tabela de
páginas. Se supusermos -- ou nos limitarmos a -- um kernel de no máximo 4 MB
menos 4 KB, podemos dedicar a última entrada (a entrada 1023) dessa tabela de
páginas aos mapeamentos temporários. O endereço virtual das páginas mapeadas
com a última entrada da PT do kernel será:

~~~
    (768 << 22) | (1023 << 12) | 0x000 = 0xC03FF000
~~~

Depois de mapear temporariamente o quadro de página que queremos usar como
tabela de páginas, e de configurá-lo para mapear o nosso primeiro quadro de
página, podemos adicioná-lo ao diretório de páginas e remover o mapeamento
temporário.

## Um Heap do Kernel {#a-kernel-heap}

Até agora só conseguimos trabalhar com dados de tamanho fixo, ou diretamente com
a memória bruta. Agora que temos um alocador de quadros de página, podemos
implementar `malloc` e `free` para usar no kernel.

Kernighan e Ritchie [@knr] têm uma implementação de exemplo no livro deles [@knr]
que podemos usar como inspiração. A única modificação necessária é trocar as
chamadas a `sbrk`/`brk` por chamadas ao alocador de quadros de página quando
mais memória for necessária. Também precisamos garantir que os quadros de
página devolvidos pelo alocador de quadros de página sejam mapeados em
endereços virtuais.
Uma implementação correta também deve devolver quadros de página ao alocador de
quadros de página na chamada a `free`, sempre que blocos de memória
suficientemente grandes forem liberados.

## Leitura Complementar {#further-reading-7}

- A página da wiki da OSDev sobre alocação de quadros de página:
  <http://wiki.osdev.org/Page_Frame_Allocation>
