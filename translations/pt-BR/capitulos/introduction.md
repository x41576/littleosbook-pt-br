# Introdução {#introduction}

Este texto é um guia prático para escrever o seu próprio sistema operacional
x86. Ele foi pensado para ajudar o bastante nos detalhes técnicos, sem revelar
demais com exemplos e trechos de código. Procuramos reunir partes do vasto (e
muitas vezes excelente) conjunto de materiais e tutoriais disponíveis, na web e
fora dela, e acrescentar nossas próprias percepções sobre os problemas que
encontramos e com os quais penamos.

Este livro não trata da teoria por trás dos sistemas operacionais, nem de como
funciona algum sistema operacional (SO) específico. Para a teoria de SO,
recomendamos o livro _Modern Operating Systems_, de Andrew Tanenbaum
[@ostanenbaum]. Listas e detalhes sobre os sistemas operacionais atuais estão
disponíveis na Internet.

Os primeiros capítulos são bastante detalhados e explícitos, para colocar você
logo para programar. Os capítulos seguintes dão mais um panorama do que é
preciso fazer, pois cada vez mais a implementação e o projeto ficam por sua
conta, já que a essa altura o mundo do desenvolvimento de kernels deve lhe ser
mais familiar. Ao final de alguns capítulos há links de leitura
complementar, que podem ser interessantes e dar uma compreensão mais profunda
dos assuntos tratados.

Nos [capítulos 2](#first-steps) e [3](#getting-to-c) montamos nosso ambiente de
desenvolvimento e damos boot no kernel do nosso SO em uma máquina virtual,
chegando enfim a escrever código em C. Continuamos no [capítulo 4](#output),
escrevendo na tela e na porta serial, e depois mergulhamos na segmentação no
[capítulo 5](#segmentation) e nas interrupções e na entrada no [capítulo
6](#interrupts-and-input).

Depois disso temos um kernel de SO bastante funcional, embora básico. No
[capítulo 7](#the-road-to-user-mode) começamos o caminho até as aplicações em
modo usuário, com a memória virtual por meio da paginação ([capítulos
8](#a-short-introduction-to-virtual-memory) e [9](#paging)), a alocação de
memória ([capítulo 10](#page-frame-allocation)) e, por fim, a execução de uma
aplicação em modo usuário no [capítulo 11](#user-mode).

Nos três últimos capítulos discutimos os tópicos mais avançados: sistemas de
arquivos ([capítulo 12](#file-systems)), chamadas de sistema ([capítulo
13](#system-calls)) e multitarefa ([capítulo 14](#multitasking)).

## Sobre o Livro {#about-the-book}

O kernel do SO e este livro foram produzidos como parte de um curso individual
avançado no Instituto Real de Tecnologia (KTH) [@kth], em Estocolmo. Nós já
tínhamos feito cursos de teoria de SO, mas tínhamos pouca experiência prática
com o desenvolvimento de kernels. Para entender melhor, e mais a fundo, como a
teoria dos cursos anteriores se traduz na prática, decidimos criar um novo
curso, focado no desenvolvimento de um SO pequeno. Outro objetivo do curso era
escrever um tutorial completo sobre como desenvolver um SO pequeno basicamente
do zero, e este livro curto é o resultado.

A arquitetura x86 é, e há muito tempo tem sido, uma das arquiteturas de hardware
mais comuns. Não foi uma escolha difícil usá-la como alvo do SO, com sua grande
comunidade, seu extenso material de referência e seus emuladores maduros. A
documentação e as informações sobre os detalhes do hardware com o qual tivemos
de trabalhar nem sempre foram fáceis de encontrar ou de entender, apesar (ou
talvez por causa) da idade da arquitetura.

O SO foi desenvolvido em cerca de seis semanas de trabalho em tempo integral. A
implementação foi feita em muitos passos pequenos, e depois de cada passo o SO
era testado manualmente. Desenvolvendo desse modo incremental e iterativo,
costumava ser mais fácil achar os bugs introduzidos, já que só uma pequena parte
do código tinha mudado desde o último estado do código sabidamente bom.
Recomendamos que você trabalhe de maneira parecida.

Durante as seis semanas de desenvolvimento, quase todas as linhas de código
foram escritas por nós em conjunto (esse jeito de trabalhar também é chamado de
_programação em par_ (_pair programming_)). Acreditamos que esse estilo de
desenvolvimento nos poupou de muitos bugs, mas isso é difícil de provar
cientificamente.

## Quem Lê {#the-reader}

Quem lê este livro deve estar à vontade com UNIX/Linux, programação de sistemas,
a linguagem C e sistemas computacionais em geral (como a notação hexadecimal
[@wiki:hex]). Este livro pode ser um jeito de começar a aprender essas coisas,
mas será mais difícil, e desenvolver um sistema operacional já é um desafio por
si só. Mecanismos de busca e outros tutoriais costumam ajudar se você
empacar.

## Créditos, Agradecimentos e Reconhecimentos {#credits-thanks-and-acknowledgements}

Agradecemos à comunidade OSDev [@osdev] pela excelente wiki e pelos membros
prestativos, e a James Molloy pelo excelente tutorial de desenvolvimento de
kernel [@malloy]. Agradecemos também a Torbjörn Granlund, que nos orientou, pelas
perguntas perspicazes e pelas discussões interessantes.

Boa parte da formatação CSS do livro se baseia no trabalho de Scott Chacon para
o livro _Pro Git_, <http://progit.org/>.

## Quem Contribuiu {#contributors}
Somos muito gratos pelos patches que as pessoas nos enviam. As seguintes
pessoas contribuíram para este livro:

- [alexschneider](https://github.com/alexschneider)
- [Avidanborisov](https://github.com/Avidanborisov)
- [nirs](https://github.com/nirs)
- [kedarmhaswade](https://github.com/kedarmhaswade)
- [vamanea](https://github.com/vamanea)
- [ansjob](https://github.com/ansjob)

## Alterações e Correções {#changes-and-corrections}

Este livro está hospedado no GitHub -- se você tiver sugestões, comentários ou
correções, basta fazer um fork do livro, escrever suas alterações e nos enviar
um pull request. Teremos prazer em incorporar qualquer coisa que melhore este
livro.

## Issues e Onde Obter Ajuda {#issues-and-where-to-get-help}
Se você tiver problemas ao ler o livro, consulte as issues no GitHub para obter
ajuda: <https://github.com/littleosbook/littleosbook/issues>.

## Licença {#license}

Todo o conteúdo está sob a licença Creative Commons
Atribuição-NãoComercial-CompartilhaIgual 3.0,
<http://creativecommons.org/licenses/by-nc-sa/3.0/us/>. Os exemplos de código
estão em domínio público -- use-os como quiser. Referências a este livro são
sempre recebidas com carinho.
