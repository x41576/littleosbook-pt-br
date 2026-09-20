# Uma Breve Introdução à Memória Virtual {#a-short-introduction-to-virtual-memory}

A _memória virtual_ é uma abstração da memória física. O objetivo da memória
virtual costuma ser simplificar o desenvolvimento de aplicações e permitir que
os processos endereçem mais memória do que a que realmente existe na máquina.
Também não queremos que as aplicações mexam no kernel ou na memória de outras
aplicações, por questões de segurança.

Na arquitetura x86, a memória virtual pode ser obtida de duas formas:
_segmentação_ e _paginação_. A paginação é, de longe, a técnica mais comum e
versátil, e vamos implementá-la no próximo capítulo. Ainda assim, algum uso de
segmentação continua necessário para que o código possa executar em diferentes
níveis de privilégio.

Gerenciar a memória é uma grande parte do que um sistema operacional faz. A
[paginação](#paging) e a [alocação de quadros de página](#page-frame-allocation)
tratam disso.

Segmentação e paginação são descritas no [@intel3a], capítulos 3 e 4.

## Memória Virtual por Meio de Segmentação? {#virtual-memory-through-segmentation}

Dá para dispensar a paginação por completo e usar só a segmentação para obter
memória virtual. Cada processo em modo usuário receberia o seu próprio segmento,
com endereço-base e limite configurados corretamente. Assim, nenhum processo
consegue ver a memória de outro. O problema é que a memória física de um
processo precisa ser contígua (ou, pelo menos, é muito conveniente que seja).
Ou precisamos saber de antemão quanta memória o programa vai exigir (improvável),
ou podemos mover os segmentos de memória para lugares onde possam crescer quando
o limite for atingido (caro, causa fragmentação -- pode resultar em "memória
insuficiente" mesmo havendo memória disponível de sobra). A paginação resolve
esses dois problemas.

Vale notar que, no x86\_64 (a versão de 64 bits da arquitetura x86), a
segmentação foi quase totalmente removida.

## Leitura Complementar {#further-reading-5}

- A LWN.net tem um artigo sobre memória virtual: <http://lwn.net/Articles/253361/>
- Gustavo Duarte também escreveu um artigo sobre memória virtual:
  <http://duartes.org/gustavo/blog/post/memory-translation-and-segmentation>
