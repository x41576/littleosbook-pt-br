# Chamadas de Sistema {#system-calls}

_Chamadas de sistema_ (_system calls_) são a forma como as aplicações em modo
usuário interagem com o kernel -- para pedir recursos, solicitar a execução de
operações e assim por diante. A API de chamadas de sistema é a parte do kernel
mais exposta a quem usa o sistema; por isso, seu projeto exige alguma reflexão.

## Projetando Chamadas de Sistema {#designing-system-calls}

Cabe a nós, quem desenvolve o kernel, projetar as chamadas de sistema que
poderão ser usadas por quem desenvolve aplicações. Podemos nos inspirar nos
padrões POSIX ou, se eles parecerem trabalho demais, olhar apenas as chamadas do
Linux e escolher as que quisermos. Veja a seção
["Leitura Complementar"](#further-reading-7) no fim do capítulo para
referências.

## Implementando Chamadas de Sistema {#implementing-system-calls}

Tradicionalmente, as chamadas de sistema são invocadas com interrupções de
software. As aplicações de usuário colocam os valores apropriados em
registradores ou na pilha e então disparam uma interrupção predefinida, que
transfere a execução para o kernel. O número da interrupção usado depende do
kernel; o Linux usa o número `0x80` para identificar que uma interrupção é
destinada a uma chamada de sistema.

Quando as chamadas de sistema são executadas, o nível de privilégio atual
normalmente muda de PL3 para PL0 (se a aplicação estiver em execução em modo
usuário). Para permitir isso, o DPL da entrada na IDT para a interrupção de
chamada de sistema precisa permitir acesso a partir do PL3.

Sempre que ocorrem interrupções entre níveis de privilégio, o processador
empilha alguns registradores importantes -- os mesmos que usamos para
[entrar em modo usuário](#user-mode); veja a figura 6-4, seção 6.12.1, do manual
da Intel [@intel3a]. Qual pilha é usada? A mesma seção de [@intel3a] especifica
que, se uma interrupção fizer o código executar em um nível de privilégio
numericamente menor, ocorre uma troca de pilha. Os novos valores dos
registradores `ss` e `esp` são carregados a partir do segmento de estado de
tarefa (_Task State Segment_, TSS) atual. A estrutura do TSS é especificada na
figura 7-2, seção 7.2.1 do manual da Intel [@intel3a].

Para habilitar as chamadas de sistema, precisamos configurar um TSS antes de
entrar em modo usuário. Isso pode ser feito em C, preenchendo os campos `ss0` e
`esp0` de uma "struct empacotada" que representa um TSS. Antes de carregar a
"struct empacotada" no processador, é preciso adicionar um descritor de TSS à
GDT. A estrutura do descritor de TSS está descrita na seção 7.2.2 de [@intel3a].

Você especifica o seletor de segmento de TSS atual carregando-o no registrador
`tr` com a instrução assembly `ltr`. Se o descritor de segmento de TSS tiver
índice 5 e, portanto, deslocamento `5 * 8 = 40 = 0x28`, esse é o valor que deve
ser carregado no registrador `tr`.

Quando entramos em modo usuário, no capítulo
["Entrando no Modo Usuário"](#entering-user-mode), desabilitamos as interrupções
durante a execução em PL3. Como as chamadas de sistema são implementadas com
interrupções, elas precisam estar habilitadas em modo usuário. Ligar o bit da
flag IF no valor de `eflags` que está na pilha fará o `iret` habilitar as
interrupções (pois o valor de `eflags` na pilha será carregado no registrador
`eflags` pela instrução assembly `iret`).

## Leitura Complementar {#further-reading-10}

- A página da Wikipedia sobre POSIX, com links para as especificações:
  <http://en.wikipedia.org/wiki/POSIX>
- Uma lista de chamadas de sistema usadas no Linux:
  <http://bluemaster.iu.hio.no/edu/dark/lin-asm/syscalls.html>
- A página da Wikipedia sobre chamadas de sistema:
  <http://en.wikipedia.org/wiki/System_call>
- As seções do manual da Intel [@intel3a] sobre interrupções (capítulo 6) e TSS
  (capítulo 7) são onde você encontra todos os detalhes de que precisa.
