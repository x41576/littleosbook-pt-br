# Saída {#output}
Este capítulo vai mostrar como exibir texto no console e como escrever dados na
porta serial. Além disso, vamos criar nosso primeiro _driver_, isto é, um
código que atua como uma camada entre o kernel e o hardware, oferecendo uma
abstração de nível mais alto do que a comunicação direta com o hardware. A
primeira parte do capítulo trata da criação de um driver para o _framebuffer_
[@wiki:fb], para poder exibir texto no console. A segunda parte mostra como
criar um driver para a porta serial. O Bochs consegue guardar a saída da porta
serial em um arquivo, o que na prática cria um mecanismo de log para o sistema
operacional.

## Interagindo com o Hardware {#interacting-with-the-hardware}
Em geral, há duas maneiras de interagir com o hardware: a _E/S mapeada em
memória_ (_memory-mapped I/O_) e as _portas de E/S_ (_I/O ports_).

Se o hardware usa E/S mapeada em memória, basta escrever em um endereço de
memória específico e o hardware será atualizado com os novos dados. Um exemplo
é o framebuffer, que será visto em mais detalhes adiante. Por exemplo, se você
escrever o valor `0x410F` no endereço `0x000B8000`, verá a letra A em branco
sobre um fundo preto (veja a seção sobre [o framebuffer](#the-framebuffer) para
mais detalhes).

Se o hardware usa portas de E/S, é preciso usar as instruções assembly `out` e
`in` para se comunicar com ele. A instrução `out` recebe dois parâmetros: o
endereço da porta de E/S e os dados a enviar. A instrução `in` recebe um único
parâmetro, o endereço da porta de E/S, e devolve dados do hardware. Podemos
pensar nas portas de E/S como uma comunicação com o hardware do mesmo modo que
você se comunica com um servidor usando sockets. O cursor (o retângulo
piscante) do framebuffer é um exemplo de hardware controlado por portas de E/S
em um PC.

## O Framebuffer {#the-framebuffer}
O framebuffer é um dispositivo de hardware capaz de exibir na tela o conteúdo
de um buffer de memória [@wiki:fb]. O framebuffer tem 80 colunas e 25 linhas, e
os índices de linha e de coluna começam em 0 (portanto as linhas são numeradas
de 0 - 24).

### Escrevendo Texto {#writing-text}
Escrever texto no console pelo framebuffer é feito com E/S mapeada em memória.
O endereço inicial da E/S mapeada em memória do framebuffer é `0x000B8000`
[@wiki:vga-compat]. A memória é dividida em células de 16 bits, e esses 16 bits
determinam ao mesmo tempo o caractere, a cor de primeiro plano e a cor de
plano de fundo. Os oito bits mais altos são o valor ASCII [@wiki:ascii] do caractere, os
bits 7 - 4 são o fundo e os bits 3 - 0 são o primeiro plano, como se vê na
figura a seguir:

    Bit:     | 15 14 13 12 11 10 9 8 | 7 6 5 4 | 3 2 1 0 |
    Content: | ASCII                 | FG      | BG      |

As cores disponíveis aparecem na tabela a seguir:

   Cor Valor         Cor Valor           Cor Valor            Cor Valor
------ ------ ---------- ------- ----------- ------ ------------- ------
 Preto 0        Vermelho 4        Cinza esc. 8        Verm. claro 12
  Azul 1         Magenta 5        Azul claro 9      Magenta claro 13
 Verde 2          Marrom 6       Verde claro 10      Marrom claro 14
 Ciano 3       Cinza cl. 7       Ciano claro 11            Branco 15

A primeira célula corresponde à linha zero, coluna zero do console. Com uma
tabela ASCII, vemos que A corresponde a 65 ou `0x41`. Portanto, para escrever o
caractere A com primeiro plano verde (2) e fundo cinza escuro (8) na posição
(0,0), usa-se a seguinte instrução assembly:

~~~ {.nasm}
    mov [0x000B8000], 0x4128
~~~

A segunda célula corresponde então à linha zero, coluna um, e o endereço dela
é, portanto:

~~~
    0x000B8000 + 16 = 0x000B8010
~~~

Também é possível escrever no framebuffer em C, tratando o endereço
`0x000B8000` como um ponteiro para char, `char *fb = (char *) 0x000B8000`.
Então, escrever A na posição (0,0) com primeiro plano verde e fundo cinza
escuro fica assim:

~~~ {.nasm}
    fb[0] = 'A';
    fb[1] = 0x28;
~~~

O código a seguir mostra como isso pode ser encapsulado em uma função:

~~~ {.c}
    /** fb_write_cell:
     *  Writes a character with the given foreground and background to position i
     *  in the framebuffer.
     *
     *  @param i  The location in the framebuffer
     *  @param c  The character
     *  @param fg The foreground color
     *  @param bg The background color
     */
    void fb_write_cell(unsigned int i, char c, unsigned char fg, unsigned char bg)
    {
        fb[i] = c;
        fb[i + 1] = ((fg & 0x0F) << 4) | (bg & 0x0F)
    }
~~~

A função pode então ser usada assim:

~~~ {.c}
    #define FB_GREEN     2
    #define FB_DARK_GREY 8

    fb_write_cell(0, 'A', FB_GREEN, FB_DARK_GREY);
~~~

### Movendo o Cursor {#moving-the-cursor}

Mover o cursor do framebuffer é feito por duas portas de E/S diferentes. A
posição do cursor é determinada por um inteiro de 16 bits: 0 significa linha
zero, coluna zero; 1 significa linha zero, coluna um; 80 significa linha um,
coluna zero, e assim por diante. Como a posição tem 16 bits e o argumento da
instrução assembly `out` tem 8 bits, a posição precisa ser enviada em duas
etapas: primeiro 8 bits, depois os outros 8. O framebuffer tem duas portas de
E/S: uma para receber os dados e outra para descrever os dados recebidos. A
porta `0x3D4` [@osdev:vga] é a que descreve os dados, e a porta `0x3D5`
[@osdev:vga] é a dos dados em si.

Para posicionar o cursor na linha um, coluna zero (posição `80 = 0x0050`),
usaríamos as seguintes instruções assembly:

~~~ {.nasm}
    out 0x3D4, 14      ; 14 tells the framebuffer to expect the highest 8 bits of the position
    out 0x3D5, 0x00    ; sending the highest 8 bits of 0x0050
    out 0x3D4, 15      ; 15 tells the framebuffer to expect the lowest 8 bits of the position
    out 0x3D5, 0x50    ; sending the lowest 8 bits of 0x0050
~~~

A instrução assembly `out` não pode ser executada diretamente em C. Por isso, é
uma boa ideia encapsular `out` em uma função em assembly, que possa ser
acessada a partir de C pela convenção de chamada cdecl [@wiki:ccall]:

~~~ {.nasm}
    global outb             ; make the label outb visible outside this file

    ; outb - send a byte to an I/O port
    ; stack: [esp + 8] the data byte
    ;        [esp + 4] the I/O port
    ;        [esp    ] return address
    outb:
        mov al, [esp + 8]    ; move the data to be sent into the al register
        mov dx, [esp + 4]    ; move the address of the I/O port into the dx register
        out dx, al           ; send the data to the I/O port
        ret                  ; return to the calling function
~~~

Guardando essa função em um arquivo chamado `io.s` e criando também um header
`io.h`, a instrução assembly `out` pode ser acessada de C com comodidade:

~~~ {.c}
    #ifndef INCLUDE_IO_H
    #define INCLUDE_IO_H

    /** outb:
     *  Sends the given data to the given I/O port. Defined in io.s
     *
     *  @param port The I/O port to send the data to
     *  @param data The data to send to the I/O port
     */
    void outb(unsigned short port, unsigned char data);

    #endif /* INCLUDE_IO_H */
~~~

Mover o cursor agora pode ser encapsulado em uma função em C:

~~~ {.c}
    #include "io.h"

    /* The I/O ports */
    #define FB_COMMAND_PORT         0x3D4
    #define FB_DATA_PORT            0x3D5

    /* The I/O port commands */
    #define FB_HIGH_BYTE_COMMAND    14
    #define FB_LOW_BYTE_COMMAND     15

    /** fb_move_cursor:
     *  Moves the cursor of the framebuffer to the given position
     *
     *  @param pos The new position of the cursor
     */
    void fb_move_cursor(unsigned short pos)
    {
        outb(FB_COMMAND_PORT, FB_HIGH_BYTE_COMMAND);
        outb(FB_DATA_PORT,    ((pos >> 8) & 0x00FF));
        outb(FB_COMMAND_PORT, FB_LOW_BYTE_COMMAND);
        outb(FB_DATA_PORT,    pos & 0x00FF);
    }
~~~

### O Driver {#the-driver}
O driver deve oferecer uma interface que o restante do código do SO vai usar
para interagir com o framebuffer. Não há certo nem errado quanto às
funcionalidades que a interface deve oferecer, mas uma sugestão é ter uma
função `write` com a seguinte declaração:

~~~ {.c}
    int write(char *buf, unsigned int len);
~~~

A função `write` escreve na tela o conteúdo do buffer `buf`, de tamanho `len`.
A função `write` deve avançar o cursor automaticamente depois que um caractere
for escrito e rolar a tela, se necessário.

## As Portas Seriais {#the-serial-ports}
A porta serial [@wiki:serial] é uma interface para comunicação entre
dispositivos de hardware e, embora esteja presente em quase todas as placas-mãe,
hoje em dia raramente é exposta ao usuário na forma de um conector DE-9. A
porta serial é fácil de usar e, mais importante, pode servir como ferramenta de
log no Bochs. Se um computador tem suporte a porta serial, em geral tem suporte
a várias, mas nós usaremos apenas uma delas. Isso porque vamos usar as portas
seriais somente para log. Além disso, vamos usá-las somente para saída, não
para entrada. As portas seriais são controladas inteiramente por portas de E/S.

### Configurando a Porta Serial {#configuring-the-serial-port}
Os primeiros dados a enviar para a porta serial são os de configuração. Para
que dois dispositivos de hardware consigam conversar, eles precisam concordar
em algumas coisas. Entre elas:

- A velocidade usada para enviar os dados (taxa de bits ou taxa de baud)
- Se algum tipo de verificação de erros será usado nos dados (bit de paridade,
  bits de parada)
- O número de bits que representa uma unidade de dados (bits de dados)

### Configurando a Linha {#configuring-the-line}
Configurar a linha significa configurar como os dados são enviados por ela. A
porta serial tem uma porta de E/S, a _porta de comando da linha_ (_line command
port_), usada para a configuração.

Primeiro vamos definir a velocidade de envio dos dados. A porta serial tem um
relógio interno que funciona a 115200 Hz. Definir a velocidade significa enviar
um divisor para a porta serial; por exemplo, enviar 2 resulta em uma velocidade
de `115200 / 2 = 57600` Hz.

O divisor é um número de 16 bits, mas só podemos enviar 8 bits por vez. Por
isso, precisamos enviar uma instrução que diga à porta serial para esperar
primeiro os 8 bits mais altos e depois os 8 bits mais baixos. Isso é feito
enviando `0x80` para a porta de comando da linha. Segue um exemplo:

~~~ {.c}
    #include "io.h" /* io.h is implement in the section "Moving the cursor" */

    /* The I/O ports */

    /* All the I/O ports are calculated relative to the data port. This is because
     * all serial ports (COM1, COM2, COM3, COM4) have their ports in the same
     * order, but they start at different values.
     */

    #define SERIAL_COM1_BASE                0x3F8      /* COM1 base port */

    #define SERIAL_DATA_PORT(base)          (base)
    #define SERIAL_FIFO_COMMAND_PORT(base)  (base + 2)
    #define SERIAL_LINE_COMMAND_PORT(base)  (base + 3)
    #define SERIAL_MODEM_COMMAND_PORT(base) (base + 4)
    #define SERIAL_LINE_STATUS_PORT(base)   (base + 5)

    /* The I/O port commands */

    /* SERIAL_LINE_ENABLE_DLAB:
     * Tells the serial port to expect first the highest 8 bits on the data port,
     * then the lowest 8 bits will follow
     */
    #define SERIAL_LINE_ENABLE_DLAB         0x80

    /** serial_configure_baud_rate:
     *  Sets the speed of the data being sent. The default speed of a serial
     *  port is 115200 bits/s. The argument is a divisor of that number, hence
     *  the resulting speed becomes (115200 / divisor) bits/s.
     *
     *  @param com      The COM port to configure
     *  @param divisor  The divisor
     */
    void serial_configure_baud_rate(unsigned short com, unsigned short divisor)
    {
        outb(SERIAL_LINE_COMMAND_PORT(com),
             SERIAL_LINE_ENABLE_DLAB);
        outb(SERIAL_DATA_PORT(com),
             (divisor >> 8) & 0x00FF);
        outb(SERIAL_DATA_PORT(com),
             divisor & 0x00FF);
    }
~~~

Também é preciso configurar a forma como os dados devem ser enviados. Isso
também é feito pela porta de comando da linha, enviando um byte. O layout dos 8
bits é o seguinte:

    Bit:     | 7 | 6 | 5 4 3 | 2 | 1 0 |
    Content: | d | b | prty  | s | dl  |

Uma descrição de cada nome está na tabela abaixo (e em [@osdev:serial]):

 Nome Descrição
----- ------------
    d Ativa (`d = 1`) ou desativa (`d = 0`) o DLAB
    b Se o controle de break está ativado (`b = 1`) ou desativado (`b = 0`)
 prty O número de bits de paridade a usar
    s O número de bits de parada a usar (`s = 0` equivale a 1, `s = 1` equivale a 1,5 ou 2)
   dl Descreve o comprimento dos dados

Vamos usar o valor `0x03` [@osdev:serial], que é o mais comum: comprimento de 8
bits, sem bit de paridade, um bit de parada e controle de break desativado. Ele
é enviado para a porta de comando da linha, como no exemplo a seguir:

~~~ {.c}
    /** serial_configure_line:
     *  Configures the line of the given serial port. The port is set to have a
     *  data length of 8 bits, no parity bits, one stop bit and break control
     *  disabled.
     *
     *  @param com  The serial port to configure
     */
    void serial_configure_line(unsigned short com)
    {
        /* Bit:     | 7 | 6 | 5 4 3 | 2 | 1 0 |
         * Content: | d | b | prty  | s | dl  |
         * Value:   | 0 | 0 | 0 0 0 | 0 | 1 1 | = 0x03
         */
        outb(SERIAL_LINE_COMMAND_PORT(com), 0x03);
    }
~~~

O artigo da OSDev [@osdev:serial] traz uma explicação mais detalhada dos
valores.

### Configurando os Buffers {#configuring-the-buffers}
Quando os dados são transmitidos pela porta serial, eles são colocados em
buffers, tanto na recepção quanto no envio. Assim, se você enviar dados para a
porta serial mais rápido do que ela consegue mandá-los pelo cabo, eles ficam em
buffer. Porém, se você enviar dados demais rápido demais, o buffer enche e
dados são perdidos. Em outras palavras, os buffers são filas FIFO. O byte de
configuração da fila FIFO é como mostra a figura a seguir:

    Bit:     | 7 6 | 5  | 4 | 3   | 2   | 1   | 0 |
    Content: | lvl | bs | r | dma | clt | clr | e |

Uma descrição de cada nome está na tabela abaixo:

 Nome Descrição
----- ------------
  lvl Quantos bytes devem ser guardados nos buffers FIFO
   bs Se os buffers devem ter 16 ou 64 bytes
    r Reservado para uso futuro
  dma Como os dados da porta serial devem ser acessados
  clt Limpa o buffer FIFO de transmissão
  clr Limpa o buffer FIFO de recepção
    e Se o buffer FIFO deve ser ativado ou não

Usamos o valor `0xC7 = 11000111`, que:

- Ativa o FIFO
- Limpa as duas filas FIFO, a de recepção e a de transmissão
- Usa 14 bytes como tamanho da fila

O WikiBook sobre programação serial [@wikibook:serial] explica os valores com
mais profundidade.

### Configurando o Modem {#configuring-the-modem}
O registrador de controle do modem é usado para um controle de fluxo por
hardware bem simples, por meio dos pinos Pronto para Transmitir (RTS) e
Terminal de Dados Pronto (DTR). Ao configurar a porta serial, queremos que RTS
e DTR valham 1, o que significa que estamos prontos para enviar dados.

O byte de configuração do modem aparece na figura a seguir:

    Bit:     | 7 | 6 | 5  | 4  | 3   | 2   | 1   | 0   |
    Content: | r | r | af | lb | ao2 | ao1 | rts | dtr |

Uma descrição de cada nome está na tabela abaixo:

 Nome Descrição
----- ------------
    r Reservado
   af Controle de fluxo automático ativado
   lb Modo de loopback (usado para depurar portas seriais)
  ao2 Saída auxiliar 2, usada para receber interrupções
  ao1 Saída auxiliar 1
  rts Pronto para Transmitir
  dtr Terminal de Dados Pronto

Não precisamos ativar interrupções, porque não vamos tratar nenhum dado
recebido. Por isso usamos o valor de configuração `0x03 = 00000011` (RTS = 1 e
DTR = 1).

### Escrevendo Dados na Porta Serial {#writing-data-to-the-serial-port}

Escrever dados na porta serial é feito pela porta de E/S de dados. Porém, antes
de escrever, a fila FIFO de transmissão precisa estar vazia (todas as escritas
anteriores devem ter terminado). A fila FIFO de transmissão está vazia se o bit
5 da porta de E/S de status da linha for igual a um.

Ler o conteúdo de uma porta de E/S é feito pela instrução assembly `in`. Não há
como usar a instrução assembly `in` em C, então é preciso encapsulá-la (do
mesmo modo que a instrução assembly `out`):

~~~ {.nasm}
    global inb

    ; inb - returns a byte from the given I/O port
    ; stack: [esp + 4] The address of the I/O port
    ;        [esp    ] The return address
    inb:
        mov dx, [esp + 4]       ; move the address of the I/O port to the dx register
        in  al, dx              ; read a byte from the I/O port and store it in the al register
        ret                     ; return the read byte
~~~

~~~ {.c}
    /* in file io.h */

    /** inb:
     *  Read a byte from an I/O port.
     *
     *  @param  port The address of the I/O port
     *  @return      The read byte
     */
    unsigned char inb(unsigned short port);
~~~

Verificar se o FIFO de transmissão está vazio pode então ser feito em C:

~~~ {.c}
    #include "io.h"

    /** serial_is_transmit_fifo_empty:
     *  Checks whether the transmit FIFO queue is empty or not for the given COM
     *  port.
     *
     *  @param  com The COM port
     *  @return 0 if the transmit FIFO queue is not empty
     *          1 if the transmit FIFO queue is empty
     */
    int serial_is_transmit_fifo_empty(unsigned int com)
    {
        /* 0x20 = 0010 0000 */
        return inb(SERIAL_LINE_STATUS_PORT(com)) & 0x20;
    }
~~~

Escrever em uma porta serial significa ficar em laço de espera (_spinning_)
enquanto a fila FIFO de transmissão não estiver vazia e, depois, escrever os
dados na porta de E/S de dados.

### Configurando o Bochs {#configuring-bochs}
Para salvar a saída da primeira porta serial, é preciso atualizar o arquivo de
configuração do Bochs, `bochsrc.txt`. A configuração `com1` instrui o Bochs
sobre como tratar a primeira porta serial:

~~~
    com1: enabled=1, mode=file, dev=com1.out
~~~

A saída da porta serial um agora será guardada no arquivo `com1.out`.

### O Driver {#the-driver-1}
Recomendamos que você implemente uma função `write` para a porta serial,
semelhante à função `write` do driver do framebuffer. Para evitar conflito de
nomes com a função `write` do framebuffer, é uma boa ideia chamar as funções de
`fb_write` e `serial_write`, para distingui-las.

Recomendamos também que você tente escrever uma função semelhante ao `printf`;
veja a seção 7.3 de [@knr]. A função `printf` poderia receber um argumento
adicional para decidir em qual dispositivo escrever a saída (framebuffer ou
serial).

Uma última recomendação é criar alguma forma de distinguir a gravidade das
mensagens de log, por exemplo, prefixando as mensagens com `DEBUG`, `INFO` ou
`ERROR`.

## Leitura Complementar {#further-reading-2}
- O livro "Serial programming" (disponível na WikiBooks) tem uma ótima seção
  sobre programação da porta serial,
  <http://en.wikibooks.org/wiki/Serial_Programming/8250_UART_Programming#UART_Registers>
- A wiki da OSDev tem uma página com muita informação sobre as portas seriais,
  <http://wiki.osdev.org/Serial_ports>
