# Primeiros Passos {#first-steps}

Desenvolver um sistema operacional (SO) não é tarefa fácil, e a pergunta "Como
é que eu começo a resolver este problema?" provavelmente vai aparecer várias
vezes ao longo do projeto, para problemas diferentes. Este capítulo vai ajudar
você a preparar seu ambiente de desenvolvimento e a dar boot em um sistema
operacional muito pequeno (e primitivo).

## Ferramentas {#tools}

### Configuração Rápida {#quick-setup}
Nós (quem escreve este livro) usamos o Ubuntu [@ubuntu] como sistema
operacional para desenvolver o SO, rodando-o tanto fisicamente quanto de forma
virtual (na máquina virtual VirtualBox [@virtualbox]). Um jeito rápido de deixar
tudo funcionando é usar a mesma configuração que nós usamos, pois sabemos que
essas ferramentas funcionam com os exemplos fornecidos neste livro.

Depois de instalar o Ubuntu, seja em uma máquina física, seja em uma virtual,
os seguintes pacotes devem ser instalados com o `apt-get`:

~~~ {.bash}
    sudo apt-get install build-essential nasm genisoimage bochs bochs-sdl
~~~

### Linguagens de Programação {#programming-languages}
O sistema operacional será desenvolvido na linguagem de programação C
[@knr][@wiki:c], usando o GCC [@gcc]. Usamos C porque desenvolver um SO exige um
controle muito preciso do código gerado e acesso direto à memória. Outras
linguagens que ofereçam os mesmos recursos também podem ser usadas, mas este
livro trata apenas de C.

O código usará um atributo de tipo que é específico do GCC:

~~~
    __attribute__((packed))
~~~

Esse atributo nos permite garantir que o compilador use, para uma `struct`, um
layout de memória exatamente igual ao que definimos no código. Isso é explicado
com mais detalhes no próximo capítulo.

Por causa desse atributo, o código dos exemplos pode ser difícil de compilar com
um compilador de C que não seja o GCC.

Para escrever código assembly, escolhemos o NASM [@nasm] como assembler, pois
preferimos a sintaxe do NASM à do GNU Assembler.

O Bash [@wiki:bash] será usado como linguagem de script em todo o livro.

### Sistema Operacional Hospedeiro {#host-operating-system}
Todos os exemplos de código supõem que o código está sendo compilado em um
sistema operacional do tipo UNIX. Todos os exemplos foram compilados com
sucesso no Ubuntu [@ubuntu], nas versões 11.04 e 11.10.

### Sistema de Build {#build-system}
Usamos o Make [@make] para construir os exemplos de Makefile.

### Máquina Virtual {#virtual-machine}
Ao desenvolver um SO, é muito conveniente poder rodar o seu código em uma
_máquina virtual_ em vez de em um computador físico, já que iniciar o SO em uma
máquina virtual é bem mais rápido do que levar o SO até uma mídia física e só
então rodá-lo em uma máquina física.
O Bochs [@bochs] é um
emulador da plataforma x86 (IA-32), bastante adequado ao desenvolvimento de SO
por causa dos seus recursos de depuração. Outras escolhas populares são o QEMU
[@qemu] e o VirtualBox [@virtualbox]. Este livro usa o Bochs.

Ao usar uma máquina virtual, não temos como garantir que o nosso SO funciona em
hardware físico de verdade. O ambiente simulado pela máquina virtual foi
projetado para ser bem parecido com o das máquinas físicas, e o SO pode ser
testado em uma delas bastando copiar o executável para um CD e achar uma máquina
adequada.

## Boot {#booting}
Dar boot em um sistema operacional consiste em passar o controle ao longo de uma
cadeia de pequenos programas, cada um mais "poderoso" que o anterior, em que o
sistema operacional é o último "programa". Veja na figura a seguir um exemplo do
processo de boot:

![Um exemplo do processo de boot. Cada caixa é um programa.](images/boot_chain.png)

### BIOS {#bios}
Quando o PC é ligado, o computador inicia um pequeno programa que segue o padrão
_Basic Input Output System_ (BIOS) [@wiki:bios]. Esse programa costuma ficar
armazenado em um chip de memória somente leitura na placa-mãe do PC. O papel
original do programa da BIOS era exportar algumas funções de biblioteca para
escrever na tela, ler a entrada do teclado etc. Os sistemas operacionais
modernos não usam as funções da BIOS: usam drivers que interagem diretamente com
o hardware, sem passar pela BIOS.
Hoje, a BIOS basicamente executa alguns diagnósticos iniciais (o autoteste de
inicialização, ou _power-on self-test_) e depois passa o controle ao bootloader.

### O Bootloader {#the-bootloader}
O programa da BIOS passará o controle do PC a um programa chamado
_bootloader_. A tarefa do bootloader é passar o controle a nós, quem desenvolve
o sistema operacional, e ao nosso código. No entanto, por causa de algumas
restrições[^1] do hardware e da compatibilidade com versões anteriores, o
bootloader costuma ser dividido em duas partes: a primeira passa o controle à
segunda, que por fim entrega o controle do PC ao sistema operacional.

[^1]: O bootloader precisa caber no setor de boot do _master boot record_ (MBR)
de um disco rígido, que tem apenas 512 bytes.

Escrever um bootloader envolve escrever muito código de baixo nível que interage
com a BIOS. Por isso, usaremos um bootloader já existente: o GNU GRand
Unified Bootloader (GRUB) [@grub].

Com o GRUB, o sistema operacional pode ser construído como um executável ELF
[@wiki:elf] comum, que o GRUB carregará no local correto da memória.
A compilação do kernel exige que o código seja organizado na memória de um jeito
específico (como compilar o kernel será discutido mais adiante neste capítulo).

### O Sistema Operacional {#the-operating-system}
O GRUB passará o controle ao sistema operacional saltando para uma posição da
memória. Antes do salto, o GRUB procura um número mágico, para se certificar de
que está mesmo saltando para um SO e não para um código qualquer. Esse número
mágico faz parte da _especificação multiboot_ [@multiboot], que o GRUB segue.
Assim que o GRUB dá o salto, o SO tem controle total do computador.

## Olá, Cafebabe {#hello-cafebabe}
Esta seção descreve como implementar o menor SO possível que funcione com o
GRUB. A única coisa que esse SO fará é escrever `0xCAFEBABE` no registrador
`eax` (a maioria das pessoas provavelmente nem chamaria isso de SO).

### Compilando o Sistema Operacional {#compiling-the-operating-system}
Esta parte do SO precisa ser escrita em código assembly, já que o C exige uma
pilha, que não está disponível (o capítulo ["Chegando ao C"](#getting-to-c)
descreve como configurar uma). Salve o código a seguir em um arquivo chamado
`loader.s`:

~~~ {.nasm}
    global loader                   ; the entry symbol for ELF

    MAGIC_NUMBER equ 0x1BADB002     ; define the magic number constant
    FLAGS        equ 0x0            ; multiboot flags
    CHECKSUM     equ -MAGIC_NUMBER  ; calculate the checksum
                                    ; (magic number + checksum + flags should equal 0)

    section .text:                  ; start of the text (code) section
    align 4                         ; the code must be 4 byte aligned
        dd MAGIC_NUMBER             ; write the magic number to the machine code,
        dd FLAGS                    ; the flags,
        dd CHECKSUM                 ; and the checksum

    loader:                         ; the loader label (defined as entry point in linker script)
        mov eax, 0xCAFEBABE         ; place the number 0xCAFEBABE in the register eax
    .loop:
        jmp .loop                   ; loop forever
~~~

A única coisa que este SO fará é escrever o número bem específico `0xCAFEBABE`
no registrador `eax`. É _muito_ improvável que o número `0xCAFEBABE` estivesse
no registrador `eax` se o SO _não_ o tivesse colocado lá.

O arquivo `loader.s` pode ser compilado em um arquivo objeto ELF [@wiki:elf] de
32 bits com o seguinte comando:

~~~ {.bash}
    nasm -f elf32 loader.s
~~~

### Linkando o Kernel {#linking-the-kernel}
Agora o código precisa ser linkado para produzir um arquivo executável, o que
exige um pouco mais de cuidado do que ao linkar a maioria dos programas. Queremos
que o GRUB carregue o kernel em um endereço de memória maior ou igual a
`0x00100000` (1 megabyte (MB)), porque os endereços abaixo de 1 MB são usados
pelo próprio GRUB, pela BIOS e pela E/S mapeada em memória. Por isso, é preciso
o seguinte script do linker (escrito para o GNU LD [@gnubinutils]):

~~~
ENTRY(loader)                /* the name of the entry label */

SECTIONS {
    . = 0x00100000;          /* the code should be loaded at 1 MB */

    .text ALIGN (0x1000) :   /* align at 4 KB */
    {
        *(.text)             /* all text sections from all files */
    }

    .rodata ALIGN (0x1000) : /* align at 4 KB */
    {
        *(.rodata*)          /* all read-only data sections from all files */
    }

    .data ALIGN (0x1000) :   /* align at 4 KB */
    {
        *(.data)             /* all data sections from all files */
    }

    .bss ALIGN (0x1000) :    /* align at 4 KB */
    {
        *(COMMON)            /* all COMMON sections from all files */
        *(.bss)              /* all bss sections from all files */
    }
}
~~~

Salve o script do linker em um arquivo chamado `link.ld`. Agora o executável
pode ser linkado com o seguinte comando:

~~~ {.bash}
    ld -T link.ld -melf_i386 loader.o -o kernel.elf
~~~

O executável final se chamará `kernel.elf`.

### Obtendo o GRUB {#obtaining-grub}
A versão do GRUB que usaremos é o GRUB Legacy, pois assim a imagem ISO do SO
pode ser gerada tanto em sistemas que usam o GRUB Legacy quanto em sistemas que
usam o GRUB 2. Mais especificamente, usaremos o bootloader `stage2_eltorito` do
GRUB Legacy. Esse arquivo pode ser construído a partir do GRUB 0.97, baixando o
código-fonte em <ftp://alpha.gnu.org/gnu/grub/grub-0.97.tar.gz>. No entanto, o
script `configure` não funciona bem com o Ubuntu [@ubuntu-grub], então o
arquivo binário pode ser baixado em
<http://littleosbook.github.com/files/stage2_eltorito>. Copie o arquivo
`stage2_eltorito` para a pasta que já contém `loader.s` e `link.ld`.

### Construindo uma Imagem ISO {#building-an-iso-image}
O executável precisa ser colocado em uma mídia que possa ser carregada por uma
máquina virtual ou física. Neste livro usaremos arquivos de imagem ISO
[@wiki:iso] como mídia, mas também é possível usar imagens de disquete,
dependendo do que a máquina virtual ou física suportar.

Criaremos a imagem ISO do kernel com o programa `genisoimage`. Antes, é preciso
criar uma pasta que contenha os arquivos que estarão na imagem ISO. Os comandos
a seguir criam a pasta e copiam os arquivos para os lugares corretos:

~~~ {.bash}
    mkdir -p iso/boot/grub              # create the folder structure
    cp stage2_eltorito iso/boot/grub/   # copy the bootloader
    cp kernel.elf iso/boot/             # copy the kernel
~~~

É preciso criar um arquivo de configuração `menu.lst` para o GRUB. Esse arquivo
diz ao GRUB onde o kernel está e configura algumas opções:

~~~
    default=0
    timeout=0

    title os
    kernel /boot/kernel.elf
~~~

Coloque o arquivo `menu.lst` na pasta `iso/boot/grub/`. O conteúdo da pasta
`iso` deve ficar como na figura a seguir:

~~~
    iso
    |-- boot
      |-- grub
      | |-- menu.lst
      | |-- stage2_eltorito
      |-- kernel.elf
~~~

A imagem ISO pode então ser gerada com o seguinte comando:

~~~
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
~~~

Para mais informações sobre as flags usadas no comando, consulte o manual do
`genisoimage`.

A imagem ISO `os.iso` agora contém o executável do kernel, o bootloader GRUB e
o arquivo de configuração.

### Rodando o Bochs {#running-bochs}
Agora podemos rodar o SO no emulador Bochs usando a imagem ISO `os.iso`.
O Bochs precisa de um arquivo de configuração para iniciar; abaixo está um
exemplo de arquivo de configuração simples:

~~~
    megs:            32
    display_library: sdl
    romimage:        file=/usr/share/bochs/BIOS-bochs-latest
    vgaromimage:     file=/usr/share/bochs/VGABIOS-lgpl-latest
    ata0-master:     type=cdrom, path=os.iso, status=inserted
    boot:            cdrom
    log:             bochslog.txt
    clock:           sync=realtime, time0=local
    cpu:             count=1, ips=1000000
~~~

Talvez seja preciso mudar o caminho de `romimage` e `vgaromimage`, dependendo de
como você instalou o Bochs. Mais informações sobre o arquivo de configuração do
Bochs estão no site do Bochs [@bochs-config].

Se você salvou a configuração em um arquivo chamado `bochsrc.txt`, pode rodar o
Bochs com o seguinte comando:

~~~
    bochs -f bochsrc.txt -q
~~~

A flag `-f` diz ao Bochs para usar o arquivo de configuração indicado, e a flag
`-q` diz ao Bochs para pular o menu interativo de início. Agora você deve ver o
Bochs iniciando e exibindo um console com algumas informações do GRUB.

Depois de sair do Bochs, exiba o log produzido por ele:

~~~
    cat bochslog.txt
~~~

Em algum ponto da saída você deve ver o conteúdo dos registradores da CPU
simulada pelo Bochs. Se encontrar `RAX=00000000CAFEBABE` ou `EAX=CAFEBABE`
(dependendo de você estar rodando o Bochs com ou sem suporte a 64 bits) na
saída, então o seu SO deu boot com sucesso!

## Leitura Complementar {#further-reading}
- Gustavo Duarte escreveu um artigo detalhado sobre o que de fato acontece
  quando um computador x86 dá boot,
  <http://duartes.org/gustavo/blog/post/how-computers-boot-up>
- Gustavo continua descrevendo o que o kernel faz nas etapas iniciais em
  <http://duartes.org/gustavo/blog/post/kernel-boot-process>
- A wiki da OSDev também tem um bom artigo sobre o boot de um computador x86:
  <http://wiki.osdev.org/Boot_Sequence>
