# Segmentação {#segmentation}

_Segmentação_, no x86, significa acessar a memória por meio de segmentos.
Segmentos são porções do espaço de endereçamento, possivelmente sobrepostas,
especificadas por um endereço-base e um limite. Para endereçar um byte na
memória segmentada, você usa um _endereço lógico_ de 48 bits: 16 bits que
especificam o segmento e 32 bits que especificam qual deslocamento dentro desse
segmento você quer. O deslocamento é somado ao endereço-base do segmento, e o
endereço linear resultante é conferido com o limite do segmento -- veja a figura
abaixo. Se tudo der certo (incluindo as verificações de direitos de acesso,
ignoradas por enquanto), o resultado é um _endereço linear_. Quando a paginação
está desabilitada, o espaço de endereçamento linear é mapeado 1:1 sobre o
espaço de _endereços físicos_, e a memória física pode ser acessada. (Veja o
capítulo ["Paginação"](#paging) para saber como habilitar a paginação.)

![Tradução de endereços lógicos em endereços lineares.
](images/intel_3_5_logical_to_linear.png)

Para habilitar a segmentação, é preciso configurar uma tabela que descreve cada
segmento -- uma _tabela de descritores de segmento_. No x86, há dois tipos de
tabelas de descritores: a _tabela de descritores globais_ (_Global Descriptor
Table_, GDT) e as _tabelas de descritores locais_ (_Local Descriptor Tables_,
LDT). Uma LDT é configurada e gerenciada por processos do espaço de usuário, e
cada processo tem a sua própria LDT. As LDTs podem ser usadas se um modelo de
segmentação mais complexo for desejado -- não vamos usá-las. A GDT é
compartilhada por todos -- ela é global.

Como discutimos nas seções sobre memória virtual e paginação, a segmentação
raramente é usada além de uma configuração mínima, parecida com a que faremos a
seguir.

## Acessando a Memória {#accessing-memory}

Na maioria das vezes, ao acessar a memória, não há necessidade de especificar
explicitamente o segmento a usar. O processador tem seis registradores de
segmento de 16 bits: `cs`, `ss`, `ds`, `es`, `gs` e `fs`. O registrador `cs` é o
registrador do segmento de código e especifica o segmento a usar ao buscar
instruções. O registrador `ss` é usado sempre que se acessa a pilha (por meio do
ponteiro de pilha `esp`), e `ds` é usado para os demais acessos a dados. O SO é
livre para usar os registradores `es`, `gs` e `fs` como quiser.

Abaixo, um exemplo que mostra o uso implícito dos registradores de segmento:

~~~ {.nasm}
    func:
        mov eax, [esp+4]
        mov ebx, [eax]
        add ebx, 8
        mov [eax], ebx
        ret
~~~

O exemplo acima pode ser comparado com o seguinte, que faz uso explícito dos
registradores de segmento:

~~~ {.nasm}
    func:
        mov eax, [ss:esp+4]
        mov ebx, [ds:eax]
        add ebx, 8
        mov [ds:eax], ebx
        ret
~~~

Você não precisa usar `ss` para armazenar o seletor do segmento de pilha, nem
`ds` para o seletor do segmento de dados. Você poderia guardar o seletor do
segmento de pilha em `ds` e vice-versa. No entanto, para usar o estilo implícito
mostrado acima, os seletores de segmento precisam estar armazenados nos
registradores previstos para eles.

Os descritores de segmento e seus campos são descritos na figura 3-8 do manual
da Intel [@intel3a].

## A Tabela de Descritores Globais (GDT) {#the-global-descriptor-table-gdt}

Uma GDT/LDT é um array de descritores de segmento de 8 bytes. O primeiro
descritor da GDT é sempre um descritor nulo e nunca pode ser usado para acessar
memória. São necessários pelo menos dois descritores de segmento (além do
descritor nulo) na GDT, porque o descritor contém mais informações do que
apenas os campos de base e limite. Os dois campos mais relevantes para nós são o
campo _Type_ e o campo _nível de privilégio do descritor_ (_Descriptor Privilege
Level_, DPL).

A Tabela 3-1 do capítulo 3 do manual da Intel [@intel3a] especifica os valores
do campo Type. A tabela mostra que o campo Type não pode ser gravável _e_
executável ao mesmo tempo. Portanto, são necessários dois segmentos: um para
executar código, a ser colocado em `cs` (Type é Execute-only ou Execute-Read), e
outro para ler e escrever dados (Type é Read/Write), a ser colocado nos demais
registradores de segmento.

O DPL especifica os _níveis de privilégio_ necessários para usar o segmento. O
x86 admite quatro níveis de privilégio (PL), de 0 a 3, sendo o PL0 o mais
privilegiado. Na maioria dos sistemas operacionais (ex.: Linux e Windows), apenas
o PL0 e o PL3 são usados. No entanto, alguns sistemas operacionais, como o MINIX,
usam todos os níveis. O kernel deve poder fazer qualquer coisa, por isso usa
segmentos com DPL igual a 0 (também chamado de modo kernel). O nível de
privilégio atual (CPL) é determinado pelo seletor de segmento em `cs`.

Os segmentos necessários estão descritos na tabela abaixo.

 Índice  Desloc.   Nome                 Faixa de endereços        Tipo   DPL
-------  -------   -------------------  ------------------------- -----  ----
      0   `0x00`   descritor nulo
      1   `0x08`   código do kernel     `0x00000000 - 0xFFFFFFFF` RX     PL0
      2   `0x10`   dados do kernel      `0x00000000 - 0xFFFFFFFF` RW     PL0

Table: Os descritores de segmento necessários.

Observe que os segmentos se sobrepõem -- ambos abrangem todo o espaço de
endereçamento linear. Na nossa configuração mínima, vamos usar a segmentação
apenas para obter níveis de privilégio. Veja o manual da Intel [@intel3a],
capítulo 3, para os detalhes dos demais campos do descritor.

## Carregando a GDT {#loading-the-gdt}

Carregar a GDT no processador é feito com a instrução assembly `lgdt`, que recebe
o endereço de uma struct que especifica o início e o tamanho da GDT. O mais fácil
é codificar essa informação usando uma ["struct empacotada"](#packing-structs),
como mostra o exemplo a seguir:

~~~ {.c}
    struct gdt {
        unsigned int address;
        unsigned short size;
    } __attribute__((packed));
~~~

Se o conteúdo do registrador `eax` for o endereço dessa struct, então a GDT pode
ser carregada com o código assembly abaixo:

~~~ {.nasm}
    lgdt [eax]
~~~

Pode ser mais fácil tornar essa instrução disponível a partir do C, do mesmo
jeito que foi feito com as instruções assembly `in` e `out`.

Depois que a GDT é carregada, os registradores de segmento precisam ser
carregados com os seus respectivos seletores de segmento. O conteúdo de um
seletor de segmento é descrito na figura e na tabela abaixo:

    Bit:     | 15                                3 | 2  | 1 0 |
    Content: | offset (index)                      | ti | rpl |

-------------------------------------------------------------------------
Nome             Descrição
---------------- -------------------------------------------------------
rpl              Nível de Privilégio Requisitado (_Requested Privilege Level_)
                 -- queremos executar em PL0 por enquanto.

ti               Indicador de Tabela (_Table Indicator_). 0 significa que isto
                 especifica um segmento da GDT, 1 significa um segmento da LDT.

offset (index)   Deslocamento dentro da tabela de descritores.
------------------------------------------------------------------------

Table: O formato dos seletores de segmento.

O deslocamento do seletor de segmento é somado ao início da GDT para obter o
endereço do descritor de segmento: `0x08` para o primeiro descritor e `0x10`
para o segundo, já que cada descritor tem 8 bytes. O nível de privilégio
requisitado (RPL) deve ser `0`, já que o kernel do SO deve executar no nível de
privilégio 0.

Carregar os registradores de seletor de segmento é fácil para os registradores
de dados -- basta copiar os deslocamentos corretos para os registradores:

~~~ {.nasm}
    mov ds, 0x10
    mov ss, 0x10
    mov es, 0x10
    .
    .
    .
~~~

Para carregar `cs`, precisamos fazer um "salto distante" (_far jump_):

~~~ {.nasm}
    ; code here uses the previous cs
    jmp 0x08:flush_cs   ; specify cs when jumping to flush_cs

    flush_cs:
        ; now we've changed cs to 0x08
~~~

Um salto distante é um salto em que especificamos explicitamente o endereço
lógico completo de 48 bits: o seletor de segmento a usar e o endereço absoluto
para onde saltar. Ele primeiro define `cs` como `0x08` e depois salta para
`flush_cs` usando o seu endereço absoluto.

## Leitura Complementar {#further-reading-3}

- O capítulo 3 do manual da Intel [@intel3a] está cheio de detalhes técnicos e de
  baixo nível sobre segmentação.
- A wiki da OSDev tem uma página sobre segmentação:
  <http://wiki.osdev.org/Segmentation>
- A página da Wikipedia sobre a segmentação no x86 pode valer a pena:
  <http://en.wikipedia.org/wiki/X86_memory_segmentation>
