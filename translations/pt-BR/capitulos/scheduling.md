# Multitarefa {#multitasking}

Como fazer vários processos parecerem rodar ao mesmo tempo? Hoje, essa pergunta
tem duas respostas:

- Com a disponibilidade de processadores multi-core, ou em sistemas com vários
  processadores, dois processos podem de fato rodar ao mesmo tempo, executando
  cada um em um núcleo ou processador diferente.
- Fingir. Ou seja, alternar rapidamente (mais rápido do que uma pessoa consegue
  perceber) entre os processos. Em qualquer instante há apenas um processo em
  execução, mas a alternância rápida dá a impressão de que eles rodam "ao mesmo
  tempo".

Como o sistema operacional criado neste livro não oferece suporte a processadores
multi-core nem a vários processadores, a única opção é fingir. A parte do sistema
operacional responsável por alternar rapidamente entre os processos é chamada de
_algoritmo de escalonamento_.

## Criando Novos Processos {#creating-new-processes}

A criação de novos processos costuma ser feita com duas chamadas de sistema
diferentes: `fork` e `exec`. O `fork` cria uma cópia exata do processo em
execução, enquanto o `exec` substitui o processo atual por um especificado pelo
caminho até a localização de um programa no sistema de arquivos. Das duas,
recomendamos que você comece implementando o `exec`, já que essa chamada de
sistema executará quase exatamente os mesmos passos descritos na seção
["Preparando-se para o Modo Usuário"](#setting-up-for-user-mode) do capítulo
["Modo Usuário"](#user-mode).

## Escalonamento Cooperativo com Yielding {#cooperative-scheduling-with-yielding}

A forma mais fácil de conseguir a alternância rápida entre processos é deixar
que os próprios processos cuidem da troca. Os processos rodam por um tempo e
então avisam o SO (por meio de uma chamada de sistema) de que ele já pode passar
para outro processo. Abrir mão do controle da CPU em favor de outro processo é
chamado de _yielding_ (ceder a vez) e, quando os próprios processos são
responsáveis pelo escalonamento, ele se chama _escalonamento cooperativo_, já que
todos os processos precisam cooperar entre si.

Quando um processo cede a vez, todo o estado do processo precisa ser salvo (todos
os registradores), de preferência no heap do kernel, em uma estrutura que
represente um processo. Ao passar para um novo processo, todos os registradores
precisam ser restaurados a partir dos valores salvos.

O escalonamento pode ser implementado mantendo uma lista dos processos que estão
em execução. A chamada de sistema `yield` deve então executar o próximo processo
da lista e colocar o atual no fim (há outros esquemas possíveis, mas este é
simples).

A transferência de controle para o novo processo é feita pela instrução assembly
`iret`, exatamente da mesma forma explicada na seção
["Entrando no Modo Usuário"](#entering-user-mode) do capítulo
["Modo Usuário"](#user-mode).

Recomendamos __fortemente__ que você comece a implementar o suporte a vários
processos pelo escalonamento cooperativo. Recomendamos ainda que você tenha uma
solução funcionando para `exec`, `fork` e `yield` antes de implementar o
escalonamento preemptivo. Como o escalonamento cooperativo é determinístico, ele
é muito mais fácil de depurar do que o escalonamento preemptivo.

## Escalonamento Preemptivo com Interrupções {#preemptive-scheduling-with-interrupts}

Em vez de deixar que os próprios processos decidam quando passar para outro
processo, o SO pode trocar de processo automaticamente depois de um curto período
de tempo. O SO pode configurar o _temporizador de intervalo programável_
(_programmable interval timer_, PIT) para gerar uma interrupção após um curto
período, por exemplo 20 ms. No tratador de interrupção do PIT, o SO troca o
processo em execução por um novo. Assim, os próprios processos não precisam se
preocupar com o escalonamento. Esse tipo de escalonamento é chamado de
_escalonamento preemptivo_.

### Temporizador de Intervalo Programável {#programmable-interval-timer}

Para poder fazer escalonamento preemptivo, o PIT precisa antes ser configurado
para gerar interrupções a cada _x_ milissegundos, onde _x_ deve ser configurável.

A configuração do PIT é muito parecida com a de outros dispositivos de hardware:
um byte é enviado a uma porta de E/S. A porta de comando do PIT é `0x43`. Para
ler sobre todas as opções de configuração, veja o artigo sobre o PIT na OSDev
[@osdev:pit]. Nós usamos as seguintes opções:

- Gerar interrupções (usar o canal 0)
- Enviar o divisor como byte baixo e depois byte alto (veja a próxima seção para
  uma explicação)
- Usar uma onda quadrada
- Usar o modo binário

Isso resulta no byte de configuração `00110110`.

O intervalo com que as interrupções são geradas é definido por meio de um
_divisor_, da mesma forma que na porta serial. Em vez de enviar ao PIT um valor
(por exemplo, em milissegundos) que diga com que frequência uma interrupção deve
ser gerada, você envia o divisor. Por padrão, o PIT opera a 1193182 Hz. Enviar o
divisor 10 faz o PIT rodar a `1193182 / 10 = 119318` Hz. O divisor só pode ter 16
bits, então só é possível configurar a frequência do temporizador entre 1193182
Hz e `1193182 / 65535 = 18.2` Hz. Recomendamos que você crie uma função que receba
um intervalo em milissegundos e o converta para o divisor correto.

O divisor é enviado à porta de E/S de dados do canal 0 do PIT, mas, como só é
possível enviar um byte por vez, primeiro é preciso enviar os 8 bits mais baixos
do divisor e depois os 8 bits mais altos. A porta de E/S de dados do canal 0
fica em `0x40`. Mais uma vez, veja o artigo da OSDev [@osdev:pit] para mais
detalhes.

### Pilhas do Kernel Separadas para os Processos {#separate-kernel-stacks-for-processes}

Se todos os processos usarem a mesma pilha do kernel (a pilha exposta pelo TSS),
haverá problemas caso um processo seja interrompido ainda em modo kernel. O
processo para o qual se está trocando passará a usar a mesma pilha do kernel e
sobrescreverá o que o processo anterior escreveu na pilha (lembre-se de que a
estrutura de dados do TSS aponta para o _início_ da pilha).

Para resolver esse problema, cada processo deve ter a sua própria pilha do kernel,
da mesma forma que cada processo tem a sua própria pilha de modo usuário. Ao
trocar de processo, o TSS precisa ser atualizado para apontar para a pilha do
kernel do novo processo.

### Dificuldades do Escalonamento Preemptivo {#difficulties-with-preemptive-scheduling}

Ao usar escalonamento preemptivo, surge um problema que não existe no
escalonamento cooperativo. No escalonamento cooperativo, toda vez que um processo
cede a vez, ele está em modo usuário (nível de privilégio 3), já que yield é
uma chamada de sistema. No escalonamento preemptivo, os processos podem ser
interrompidos tanto em modo usuário quanto em modo kernel (nível de privilégio
0), já que o próprio processo não controla quando é interrompido.

Interromper um processo em modo kernel é um pouco diferente de interromper um
processo em modo usuário, por causa do modo como a CPU prepara a pilha nas
interrupções. Se ocorreu uma mudança de nível de privilégio (o processo foi
interrompido em modo usuário), a CPU empilha os valores dos registradores `ss` e
`esp` do processo. Se _não_ ocorre mudança de nível de privilégio (o processo foi
interrompido em modo kernel), a CPU não empilha o registrador `esp`. Além disso,
se não houve mudança de nível de privilégio, a CPU não troca para a pilha
definida no TSS.

Esse problema se resolve calculando qual era o valor de `esp` _antes_ da
interrupção. Como você sabe que a CPU empilha 3 coisas quando não há mudança de
privilégio e sabe quanto você mesmo empilhou, dá para calcular qual era o valor
de `esp` no momento da interrupção. Isso é possível porque a CPU não troca de
pilha quando não há mudança de nível de privilégio, então o conteúdo de `esp`
será o mesmo do momento da interrupção.

Para complicar ainda mais, é preciso pensar em como tratar o caso de trocar para
um novo processo que deve rodar em modo kernel. Como o `iret` é usado sem mudança
de nível de privilégio, a CPU não atualiza o valor de `esp` com o que foi
colocado na pilha -- você mesmo precisa atualizar o `esp`.

## Leitura Complementar {#further-reading-11}

- Para mais informações sobre diferentes algoritmos de escalonamento, veja
  <http://wiki.osdev.org/Scheduling_Algorithms>
