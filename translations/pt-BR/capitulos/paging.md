# Paginação {#paging}

A segmentação traduz um endereço lógico em um endereço linear. A _paginação_
traduz esses endereços lineares para o espaço de endereços físicos, e determina
os direitos de acesso e como a memória deve ser armazenada em cache.

## Por Que Paginação? {#why-paging}

A paginação é a técnica mais comum no x86 para obter memória virtual. Memória
virtual por meio de paginação significa que cada processo terá a impressão de
que a faixa de memória disponível vai de `0x00000000` - `0xFFFFFFFF`, mesmo que
o tamanho real da memória seja bem menor. Significa também que, quando um
processo endereça um byte de memória, ele usa um endereço virtual (linear) em
vez de um endereço físico. O código do processo em modo usuário não percebe
nenhuma diferença (exceto pelos atrasos na execução). O endereço linear é
traduzido em um endereço físico pela MMU e pela tabela de páginas. Se o endereço
virtual não estiver mapeado em um endereço físico, a CPU gera uma interrupção de
falha de página.

A paginação é opcional, e alguns sistemas operacionais não a utilizam. Mas se
quisermos marcar certas áreas da memória como acessíveis apenas a código que
executa em um determinado nível de privilégio (para poder ter processos rodando
em níveis de privilégio diferentes), a paginação é a forma mais elegante de
fazer isso.

## Paginação no x86 {#paging-in-x86}

A paginação no x86 (capítulo 4 do manual da Intel [@intel3a]) consiste em um
_diretório de páginas_ (_page directory_, PDT) que pode conter referências a
1024 _tabelas de páginas_ (_page tables_, PT), cada uma das quais pode apontar
para 1024 seções de memória física chamadas _quadros de página_ (_page frames_,
PF). Cada quadro de página tem 4096 bytes. Em um endereço virtual (linear), os
10 bits mais altos especificam o deslocamento de uma entrada do diretório de
páginas (PDE) no PDT atual, e os 10 bits seguintes, o deslocamento de uma
entrada da tabela de páginas (PTE) dentro da tabela de páginas apontada por
essa PDE. Os 12 bits mais baixos do endereço são o deslocamento dentro do
quadro de página a ser endereçado.

Todos os diretórios de páginas, tabelas de páginas e quadros de página precisam
estar alinhados em endereços de 4096 bytes. Isso permite endereçar um PDT, uma
PT ou um PF apenas com os 20 bits mais altos de um endereço de 32 bits, já que
os 12 mais baixos precisam ser zero.

A estrutura da PDE e a da PTE são muito parecidas: 32 bits (4 bytes), em que os
20 bits mais altos apontam para uma PTE ou um PF, e os 12 bits mais baixos
controlam os direitos de acesso e outras configurações. 4 bytes vezes 1024 dão
4096 bytes, então um diretório de páginas e uma tabela de páginas cabem, cada um,
em um quadro de página.

A tradução de endereços lineares em endereços físicos está descrita na figura
abaixo.

Embora as páginas normalmente tenham 4096 bytes, também é possível usar páginas
de 4 MB. Nesse caso, uma PDE aponta diretamente para um quadro de página de 4
MB, que precisa estar alinhado em um limite de endereço de 4 MB. A tradução de
endereços é quase igual à da figura, só que sem a etapa da tabela de páginas. É
possível misturar páginas de 4 MB e de 4 KB.

![Traduzindo endereços virtuais (endereços lineares) em endereços físicos.
](images/intel_4_2_linear_address_translation.png)

Os 20 bits que apontam para o PDT atual ficam guardados no registrador `cr3`. Os
12 bits mais baixos de `cr3` são usados para configuração.

Para mais detalhes sobre as estruturas de paginação, veja o capítulo 4 do manual
da Intel [@intel3a]. Os bits mais interessantes são _U/S_, que determina quais
níveis de privilégio podem acessar esta página (PL0 ou PL3), e _R/W_, que faz a
memória da página ser de leitura e gravação ou somente leitura.

### Identity Paging {#identity-paging}

O tipo mais simples de paginação é aquele em que mapeamos cada endereço virtual
no mesmo endereço físico, chamado de _identity paging_. Isso pode ser feito em
tempo de compilação, criando um diretório de páginas em que cada entrada aponta
para o quadro de 4 MB correspondente. Em NASM, isso pode ser feito com macros e
comandos (`%rep`, `times` e `dd`). Também pode, é claro, ser feito em tempo de
execução, com instruções assembly comuns.

### Habilitando a Paginação {#enabling-paging}

A paginação é habilitada escrevendo primeiro o endereço de um diretório de
páginas em `cr3` e depois definindo como `1` o bit 31 (o bit PG, de "paging-enable")
de `cr0`. Para usar páginas de 4 MB, defina o bit PSE (_Page Size Extensions_,
bit 4) de `cr4`. O código assembly a seguir mostra um exemplo:

~~~ {.nasm}
    ; eax has the address of the page directory
    mov cr3, eax

    mov ebx, cr4        ; read current cr4
    or  ebx, 0x00000010 ; set PSE
    mov cr4, ebx        ; update cr4

    mov ebx, cr0        ; read current cr0
    or  ebx, 0x80000000 ; set PG
    mov cr0, ebx        ; update cr0

    ; now paging is enabled
~~~

### Alguns Detalhes {#a-few-details}

É importante notar que todos os endereços dentro do diretório de páginas, das
tabelas de páginas e em `cr3` precisam ser endereços físicos das estruturas,
nunca virtuais. Isso será mais relevante nas seções posteriores, em que vamos
atualizar dinamicamente as estruturas de paginação (veja o capítulo
["Modo Usuário"](#user-mode)).

Uma instrução útil ao atualizar um PDT ou uma PT é `invlpg`. Ela invalida a
entrada da _Translation Lookaside Buffer_ (TLB) referente a um endereço virtual.
A TLB é um cache de endereços traduzidos, que mapeia endereços virtuais nos
endereços físicos correspondentes. Isso só é necessário ao alterar uma PDE ou
uma PTE que antes estava mapeada para outra coisa. Se a PDE ou a PTE já tinha
sido marcada como não presente (o bit 0 estava em 0), executar `invlpg` é
desnecessário. Alterar o valor de `cr3` faz todas as entradas da TLB serem
invalidadas.

Abaixo está um exemplo de como invalidar uma entrada da TLB:

~~~ {.nasm}
    ; invalidate any TLB references to virtual address 0
    invlpg [0]
~~~

## Paginação e o Kernel {#paging-and-the-kernel}

Esta seção vai descrever como a paginação afeta o kernel do SO. Recomendamos que
você rode o seu SO com identity paging antes de tentar implementar uma
configuração de paginação mais avançada, já que pode ser difícil depurar uma
tabela de páginas que não funciona quando ela é montada por código assembly.

### Motivos para Não Fazer o Mapeamento de Identidade do Kernel {#reasons-to-not-identity-map-the-kernel}

Se o kernel for colocado no início do espaço de endereços virtuais -- ou seja,
se o espaço de endereços virtuais (`0x00000000`, `"size of kernel"`) for mapeado
na posição do kernel na memória --, haverá problemas ao linkar o código dos
processos em modo usuário. Normalmente, durante a linkagem, o linker assume que o
código será carregado na posição de memória `0x00000000`. Por isso, ao resolver
referências absolutas, `0x00000000` será o endereço-base usado para calcular a
posição exata. Mas se o kernel estiver mapeado no espaço de endereços virtuais
(`0x00000000`, `"size of kernel"`), o processo em modo usuário não pode ser
carregado no endereço virtual `0x00000000` -- ele precisa ser colocado em outro
lugar. Assim, a suposição do linker de que o processo em modo usuário é
carregado na memória na posição `0x00000000` está errada. Isso pode ser corrigido
com um script do linker que diga ao linker para assumir outro endereço inicial,
mas essa é uma solução muito trabalhosa para quem usa o sistema operacional.

Isso também pressupõe que queremos que o kernel faça parte do espaço de
endereçamento do processo em modo usuário. Como veremos adiante, isso é uma
característica útil, pois, durante as chamadas de sistema, não precisamos mudar
nenhuma estrutura de paginação para acessar o código e os dados do kernel. As
páginas do kernel exigirão, é claro, nível de privilégio 0 para acesso, a fim de
impedir que um processo do usuário leia ou escreva na memória do kernel.

### O Endereço Virtual do Kernel {#the-virtual-address-for-the-kernel}

O ideal é que o kernel seja colocado em um endereço de memória virtual bem alto,
por exemplo `0xC0000000` (3 GB). É improvável que um processo em modo usuário
tenha 3 GB, o que agora é a única forma de ele entrar em conflito com o kernel.
Quando o kernel usa endereços virtuais a partir de 3 GB, ele é chamado de _kernel
na metade superior_ (_higher-half kernel_). `0xC0000000` é apenas um exemplo: o
kernel pode ser colocado em qualquer endereço acima de 0 para obter os mesmos
benefícios. Escolher o endereço certo depende de quanta memória virtual deve
estar disponível para o kernel (é mais fácil se toda a memória acima do endereço
virtual do kernel pertencer ao kernel) e de quanta memória virtual deve estar
disponível para o processo.

Se o processo em modo usuário tiver mais de 3 GB, o kernel precisará enviar
algumas páginas para o disco (_swap out_). A troca de páginas (_swapping_) não
faz parte deste livro.

### Posicionando o Kernel em `0xC0000000` {#placing-the-kernel-at-0xc0000000}

Para começar, é melhor colocar o kernel em `0xC0100000` do que em `0xC0000000`,
pois assim é possível mapear (`0x00000000`, `0x00100000`) em
(`0xC0000000`, `0xC0100000`). Dessa forma, toda a faixa de memória
(`0x00000000`, `"size of kernel"`) fica mapeada na faixa
(`0xC0000000`, `0xC0000000  + "size of kernel"`).

Colocar o kernel em `0xC0100000` não é difícil, mas exige algum cuidado. Trata-se,
mais uma vez, de um problema de linkagem. Quando o linker resolve todas as
referências absolutas no kernel, ele assume que o nosso kernel é carregado na
posição de memória física `0x00100000`, e não `0x00000000`, já que o script do
linker usa relocação (veja a seção ["Linkando o Kernel"](#linking-the-kernel)).
Porém, queremos que os saltos sejam resolvidos usando `0xC0100000` como
endereço-base, pois, caso contrário, um salto no kernel iria direto para o código
do processo em modo usuário (lembre-se de que o processo em modo usuário é
carregado na memória virtual `0x00000000`).

No entanto, não podemos simplesmente dizer ao linker para assumir que o kernel
começa (é carregado) em `0xC01000000`, já que queremos que ele seja carregado no
endereço físico `0x00100000`. O motivo de carregar o kernel em 1 MB é que ele
não pode ser carregado em `0x00000000`, pois há código da BIOS e do GRUB
carregado abaixo de 1 MB. Além disso, não podemos presumir que dá para carregar o
kernel em `0xC0100000`, já que a máquina pode não ter 3 GB de memória física.

Isso pode ser resolvido usando tanto a relocação (`.=0xC0100000`) quanto a
instrução `AT` no script do linker. A relocação especifica que as referências à
memória que não são relativas devem usar o endereço de relocação como base nos
cálculos de endereço. A `AT` especifica onde o kernel deve ser carregado na
memória. A relocação é feita em tempo de linkagem pelo GNU ld [@ldcmdlang]; o
endereço de carga especificado por `AT` é tratado pelo GRUB ao carregar o kernel
e faz parte do formato ELF [@wiki:elf].

### Script do Linker para a Metade Superior {#higher-half-linker-script}

Podemos modificar o [primeiro script do linker](#linking-the-kernel) para
implementar isso:

~~~
    ENTRY(loader)           /* the name of the entry symbol */

    . = 0xC0100000          /* the code should be relocated to 3GB + 1MB */

    /* align at 4 KB and load at 1 MB */
    .text ALIGN (0x1000) : AT(ADDR(.text)-0xC0000000)
    {
        *(.text)            /* all text sections from all files */
    }

    /* align at 4 KB and load at 1 MB + . */
    .rodata ALIGN (0x1000) : AT(ADDR(.text)-0xC0000000)
    {
        *(.rodata*)         /* all read-only data sections from all files */
    }

    /* align at 4 KB and load at 1 MB + . */
    .data ALIGN (0x1000) : AT(ADDR(.text)-0xC0000000)
    {
        *(.data)            /* all data sections from all files */
    }

    /* align at 4 KB and load at 1 MB + . */
    .bss ALIGN (0x1000) : AT(ADDR(.text)-0xC0000000)
    {
        *(COMMON)           /* all COMMON sections from all files */
        *(.bss)             /* all bss sections from all files */
    }
~~~

### Entrando na Metade Superior {#entering-the-higher-half}

Quando o GRUB salta para o código do kernel, não existe tabela de páginas. Por
isso, todas as referências a `0xC0100000 + X` não serão mapeadas no endereço
físico correto e causarão, na melhor das hipóteses, uma exceção de proteção geral
(GPE) ou, se o computador tiver mais de 3 GB de memória, simplesmente travarão o
computador.

Portanto, é preciso usar código assembly que não use saltos relativos nem
endereçamento de memória relativo para fazer o seguinte:

- Montar uma tabela de páginas.
- Adicionar um mapeamento de identidade para os primeiros 4 MB do espaço de
  endereços virtuais.
- Adicionar uma entrada para `0xC0100000` que mapeia em `0x0010000`

Se pularmos o mapeamento de identidade dos primeiros 4 MB, a CPU geraria uma
falha de página imediatamente depois de a paginação ser habilitada, ao tentar
buscar a próxima instrução na memória. Depois que a tabela for criada, dá para
fazer um salto para um label, de modo que `eip` passe a apontar para um endereço
virtual na metade superior:

~~~ {.nasm}
    ; assembly code executing at around 0x00100000
    ; enable paging for both actual location of kernel
    ; and its higher-half virtual location

    lea ebx, [higher_half] ; load the address of the label in ebx
    jmp ebx                ; jump to the label

    higher_half:
        ; code here executes in the higher half kernel
        ; eip is larger than 0xC0000000
        ; can continue kernel initialisation, calling C code, etc.
~~~

O registrador `eip` agora vai apontar para uma posição de memória logo depois de
`0xC0100000` -- todo o código já pode executar como se estivesse localizado em
`0xC0100000`, a metade superior. O mapeamento dos primeiros 4 MB de memória
virtual nos primeiros 4 MB de memória física agora pode ser removido da tabela
de páginas, e a entrada correspondente na TLB, invalidada com `invlpg [0]`.

### Executando na Metade Superior {#running-in-the-higher-half}

Ainda há mais alguns detalhes com que precisamos lidar ao usar um kernel na
metade superior. Precisamos ter cuidado ao usar E/S mapeada em memória que usa
posições de memória específicas. Por exemplo, o framebuffer fica em
`0x000B8000`, mas, como já não há entrada na tabela de páginas para o endereço
`0x000B8000`, é preciso usar o endereço `0xC00B8000`, já que o endereço virtual
`0xC0000000` mapeia no endereço físico `0x00000000`.

Qualquer referência explícita a endereços dentro da estrutura multiboot também
precisa ser alterada para refletir os novos endereços virtuais.

Mapear páginas de 4 MB para o kernel é simples, mas desperdiça memória (a menos
que você tenha um kernel realmente grande). Criar um kernel na metade superior
mapeado com páginas de 4 KB economiza memória, mas é mais difícil de configurar.
A memória para o diretório de páginas e para uma tabela de páginas pode ser
reservada na seção `.data`, mas é preciso configurar os mapeamentos de endereços
virtuais em físicos em tempo de execução. O tamanho do kernel pode ser
determinado exportando labels a partir do script do linker [@ldcmdlang], o que
de qualquer forma precisaremos fazer mais adiante, ao escrever o alocador de
quadros de página (veja o capítulo
["Alocação de Quadros de Página"](#page-frame-allocation)).

## Memória Virtual por Meio da Paginação {#virtual-memory-through-paging}

A paginação possibilita duas coisas que são boas para a memória virtual.
Primeiro, permite um controle de acesso detalhado à memória. É possível marcar
páginas como somente leitura, leitura e gravação, apenas para PL0 etc. Segundo,
cria a ilusão de memória contígua. Os processos em modo usuário, e o kernel,
podem acessar a memória como se ela fosse contígua, e essa memória contígua pode
ser estendida sem precisar mover dados de lugar na memória. Também podemos
permitir que os programas em modo usuário acessem toda a memória abaixo de 3 GB,
mas, a menos que eles realmente a usem, não precisamos atribuir quadros de
página às páginas. Isso permite que os processos tenham o código localizado perto
de `0x00000000` e a pilha logo abaixo de `0xC0000000`, sem exigir mais do que
duas páginas reais.

## Leitura Complementar {#further-reading-6}

- O capítulo 4 (e, em certa medida, o capítulo 3) do manual da Intel [@intel3a]
  são as suas fontes definitivas para os detalhes sobre a paginação.
- A Wikipedia tem um artigo sobre paginação: <http://en.wikipedia.org/wiki/Paging>
- A wiki da OSDev tem uma página sobre paginação: <http://wiki.osdev.org/Paging>
  e um tutorial para criar um kernel na metade superior:
  <http://wiki.osdev.org/Higher_Half_bare_bones>
- O artigo de Gustavo Duarte sobre como um kernel gerencia a memória vale muito
  a pena ser lido:
  <http://duartes.org/gustavo/blog/post/anatomy-of-a-program-in-memory>
- Detalhes sobre a linguagem de comandos do linker estão no site de Steve
  Chamberlain [@ldcmdlang].
- Mais detalhes sobre o formato ELF estão nesta apresentação:
  <http://flint.cs.yale.edu/cs422/doc/ELF_Format.pdf>
