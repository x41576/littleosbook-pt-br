# O Caminho até o Modo Usuário {#the-road-to-user-mode}

Agora que o kernel dá boot, escreve na tela e lê do teclado -- o que fazemos?
Normalmente, um kernel não deve executar a lógica das aplicações, e sim deixá-la
para os aplicativos. O kernel cria as abstrações adequadas (para memória,
arquivos e dispositivos) para facilitar o desenvolvimento de aplicações, executa
tarefas em nome delas (chamadas de sistema) e
[escalona processos](#multitasking).

O modo usuário, em contraste com o modo kernel, é o ambiente em que os programas
do usuário são executados. Esse ambiente tem menos privilégios do que o kernel e
impede que programas de usuário mal escritos atrapalhem outros programas ou o
kernel. Já os kernels mal escritos ficam livres para bagunçar o que quiserem.

Ainda falta um bom caminho até que o SO criado neste livro consiga executar
programas em modo usuário, mas este capítulo mostrará como executar facilmente
um programa pequeno em modo kernel.

## Carregando um Programa Externo {#loading-an-external-program}

De onde vem o programa externo? De alguma forma, precisamos carregar na memória o
código que queremos executar. Sistemas operacionais mais completos costumam ter
drivers e sistemas de arquivos que permitem carregar o software a partir de uma
unidade de CD-ROM, de um disco rígido ou de outra mídia persistente.

Em vez de criar todos esses drivers e sistemas de arquivos, vamos usar um
recurso do GRUB chamado módulos para carregar o programa.

### Módulos do GRUB {#grub-modules}

O GRUB consegue carregar arquivos quaisquer da imagem ISO na memória, e esses
arquivos costumam ser chamados de _módulos_. Para fazer o GRUB carregar um
módulo, edite o arquivo `iso/boot/grub/menu.lst` e acrescente a linha a seguir
no fim do arquivo:

~~~
    module /modules/program
~~~

Agora crie a pasta `iso/modules`:

~~~
    mkdir -p iso/modules
~~~

O aplicativo `program` será criado mais adiante neste capítulo.

O código que chama `kmain` precisa ser atualizado para passar a `kmain`
informações sobre onde encontrar os módulos. Também queremos dizer ao GRUB que
ele deve alinhar todos os módulos em limites de página ao carregá-los (veja o
capítulo ["Paginação"](#paging) para saber mais sobre o alinhamento de páginas).

Para instruir o GRUB sobre como carregar os nossos módulos, o "cabeçalho
multiboot" -- os primeiros bytes do kernel -- deve ser atualizado da seguinte
forma:

~~~ {.nasm}
    ; in file `loader.s`


    MAGIC_NUMBER    equ 0x1BADB002      ; define the magic number constant
    ALIGN_MODULES   equ 0x00000001      ; tell GRUB to align modules

    ; calculate the checksum (all options + checksum should equal 0)
    CHECKSUM        equ -(MAGIC_NUMBER + ALIGN_MODULES)

    section .text:                      ; start of the text (code) section
    align 4                             ; the code must be 4 byte aligned
        dd MAGIC_NUMBER                 ; write the magic number
        dd ALIGN_MODULES                ; write the align modules instruction
        dd CHECKSUM                     ; write the checksum
~~~

O GRUB também vai guardar no registrador `ebx` um ponteiro para uma `struct`
que, entre outras coisas, descreve em quais endereços os módulos foram
carregados. Portanto, o mais provável é que você queira colocar `ebx` na pilha antes
de chamar `kmain`, para que ele seja um argumento de `kmain`.

## Executando um Programa {#executing-a-program}

### Um Programa Bem Simples {#a-very-simple-program}

Um programa escrito nesta etapa só consegue executar algumas ações. Por isso,
basta um programa bem curto que grave um valor em um registrador como programa
de teste. Para verificar que o programa foi executado, pare o Bochs depois de
algum tempo e confira, no log do Bochs, se o registrador contém o número
correto. Este é um exemplo desse programa curto:

~~~ {.nasm}
    ; set eax to some distinguishable number, to read from the log afterwards
    mov eax, 0xDEADBEEF

    ; enter infinite loop, nothing more to do
    ; $ means "beginning of line", ie. the same instruction
    jmp $
~~~

### Compilando {#compiling}

Como o nosso kernel não sabe interpretar formatos de executáveis avançados,
precisamos compilar o código para um binário plano. O NASM faz isso com a flag
`-f`:

~~~
    nasm -f bin program.s -o program
~~~

Isso é tudo de que precisamos. Agora mova o arquivo `program` para a pasta
`iso/modules`.

### Encontrando o Programa na Memória {#finding-the-program-in-memory}

Antes de saltar para o programa, precisamos descobrir onde ele está na memória.
Supondo que o conteúdo de `ebx` seja passado como argumento para `kmain`, dá para
fazer isso inteiramente em C.

O ponteiro em `ebx` aponta para uma estrutura _multiboot_ [@multiboot]. Baixe o
arquivo `multiboot.h` em
<http://www.gnu.org/software/grub/manual/multiboot/html_node/multiboot.h.html>,
que descreve essa estrutura.

O ponteiro passado a `kmain` no registrador `ebx` pode ser convertido (cast) em
um ponteiro para `multiboot_info_t`. O endereço do primeiro módulo está no campo
`mods_addr`. O código a seguir mostra um exemplo:

~~~ {.c}
    int kmain(/* additional arguments */ unsigned int ebx)
    {
        multiboot_info_t *mbinfo = (multiboot_info_t *) ebx;
        unsigned int address_of_module = mbinfo->mods_addr;
    }
~~~

No entanto, antes de sair seguindo o ponteiro às cegas, você deve verificar se o
módulo foi carregado corretamente pelo GRUB. Isso pode ser feito conferindo o
campo `flags` da estrutura `multiboot_info_t`. Você também deve conferir o campo
`mods_count` para garantir que ele vale exatamente 1. Para mais detalhes sobre a
estrutura multiboot, consulte a documentação do multiboot [@multiboot].

### Saltando para o Código {#jumping-to-the-code}

A única coisa que resta fazer é saltar para o código carregado pelo GRUB. Como é
mais fácil interpretar a estrutura multiboot em C do que em código assembly,
chamar o código a partir de C é mais conveniente (é claro que também dá para
fazer isso com `jmp` ou `call` em assembly). O código em C poderia ser assim:

~~~ {.c}
    typedef void (*call_module_t)(void);
    /* ... */
    call_module_t start_program = (call_module_t) address_of_module;
    start_program();
    /* we'll never get here, unless the module code returns */
~~~

Se iniciarmos o kernel, esperarmos até que ele execute e entre no laço infinito
do programa, e então pararmos o Bochs, devemos ver `0xDEADBEEF` no registrador
`eax` pelo log do Bochs. Iniciamos um programa no nosso SO com sucesso!

## O Início do Modo Usuário {#the-beginning-of-user-mode}

O programa que escrevemos agora executa no mesmo nível de privilégio do kernel --
apenas o iniciamos de um jeito um tanto peculiar. Para permitir que aplicativos
executem em um nível de privilégio diferente, precisaremos, além da
[_segmentação_](#segmentation), fazer a [_paginação_](#paging) e a [_alocação de
quadros de página_](#page-frame-allocation).

É bastante trabalho e há muitos detalhes técnicos pela frente, mas, em alguns
capítulos, você terá programas em modo usuário funcionando.
