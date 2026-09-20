# Sistemas de Arquivos {#file-systems}

Não somos obrigados a ter sistemas de arquivos em nosso sistema operacional, mas
eles são uma abstração muito útil e costumam ter um papel central em muitos
sistemas operacionais, especialmente nos do tipo UNIX. Antes de começarmos a dar
suporte a vários processos e a chamadas de sistema, talvez valha a pena
considerar a implementação de um sistema de arquivos simples.

## Por que um Sistema de Arquivos? {#why-a-file-system}

Como especificamos quais programas executar em nosso SO? Qual é o primeiro
programa a executar? Como os programas enviam dados de saída ou leem a entrada?

Nos sistemas do tipo UNIX, com sua convenção de que quase tudo é um arquivo,
esses problemas são resolvidos pelo sistema de arquivos. (Também pode ser
interessante ler um pouco sobre o projeto Plan 9, que leva essa ideia um passo
adiante.)

## Um Sistema de Arquivos Simples, Somente Leitura {#a-simple-read-only-file-system}

O sistema de arquivos mais simples talvez seja o que já temos: um único
arquivo, que existe apenas na RAM e é carregado pelo GRUB antes de o kernel
iniciar. Quando o kernel e o sistema operacional crescerem, isso provavelmente
será limitado demais.

Um sistema de arquivos um pouco mais avançado do que apenas os bits de um
arquivo é um arquivo com metadados. Os metadados podem descrever o tipo do
arquivo, o tamanho do arquivo e assim por diante. É possível criar um programa
utilitário que rode durante o build, acrescentando esses metadados a um arquivo.
Assim, dá para construir um "sistema de arquivos dentro de um arquivo",
concatenando vários arquivos com metadados em um único arquivo grande. O
resultado dessa técnica é um sistema de arquivos somente leitura que fica na
memória (depois que o GRUB carrega o arquivo).

O programa que constrói o sistema de arquivos pode percorrer um diretório do
sistema hospedeiro e adicionar todos os subdiretórios e arquivos como parte do
sistema de arquivos de destino. Cada objeto do sistema de arquivos (diretório ou
arquivo) pode ser composto de um cabeçalho e um corpo, em que o corpo de um
arquivo é o próprio arquivo e o corpo de um diretório é uma lista de entradas --
nomes e "endereços" de outros arquivos e diretórios.

Cada objeto desse sistema de arquivos será contíguo, então será fácil para o
kernel lê-los da memória. Todos os objetos também terão tamanho fixo (exceto o
último, que pode crescer); por isso, é difícil adicionar novos arquivos ou
modificar os existentes.

## Inodes e Sistemas de Arquivos Graváveis {#inodes-and-writable-file-systems}

Quando surgir a necessidade de um sistema de arquivos gravável, é uma boa ideia
estudar o conceito de _inode_. Veja a seção ["Leitura
Complementar"](#further-reading-9) para as leituras recomendadas.

## Um Sistema de Arquivos Virtual {#a-virtual-file-system}

Que abstração deve ser usada para ler e escrever em dispositivos como a tela e o
teclado?

Um sistema de arquivos virtual (VFS) cria uma abstração sobre os sistemas de
arquivos concretos. Um VFS fornece principalmente o sistema de caminhos e a
hierarquia de arquivos, e delega as operações sobre arquivos aos sistemas de
arquivos subjacentes. O artigo original sobre o VFS é sucinto e vale muito a
leitura. Veja a seção ["Leitura Complementar"](#further-reading-9) para a
referência.

Com um VFS, poderíamos montar um sistema de arquivos especial no caminho `/dev`.
Esse sistema de arquivos trataria todos os dispositivos, como teclados e o
console. Porém, também é possível seguir a abordagem tradicional do UNIX, com
números de dispositivo maior/menor (_major/minor_) e `mknod` para criar arquivos
especiais para os dispositivos. Qual abordagem você considera a mais adequada
fica a seu critério: não há certo nem errado na construção de camadas de
abstração (embora algumas abstrações se revelem bem mais úteis do que outras).

## Leitura Complementar {#further-reading-9}

- Vale a pena conhecer as ideias por trás do sistema operacional Plan 9:
  <http://plan9.bell-labs.com/plan9/index.html>
- A página da Wikipédia sobre inodes: <http://en.wikipedia.org/wiki/Inode> e a
  estrutura de ponteiros do inode:
  <http://en.wikipedia.org/wiki/Inode_pointer_structure>.
- O artigo original sobre o conceito de vnodes e de sistema de arquivos virtual
  é bastante interessante:
  <http://www.arl.wustl.edu/~fredk/Courses/cs523/fall01/Papers/kleiman86vnodes.pdf>
- Poul-Henning Kamp discute a ideia de um sistema de arquivos especial para
  `/dev` em
  <http://static.usenix.org/publications/library/proceedings/bsdcon02/full_papers/kamp/kamp_html/index.html>
