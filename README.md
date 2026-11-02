# aberturas

Todo jogador de xadrez já ouviu que "tal abertura é boa para iniciante" ou que "a
Siciliana é coisa de quem joga forte". Eu queria ver isso em números. O Lichess publica
todas as partidas ranqueadas do site, mês a mês, sob licença CC0, e cada partida já vem
com o rating dos dois jogadores, o ritmo e o nome da abertura no cabeçalho. Então dá
para medir.

Este repositório lê essa base e soma, para cada abertura, quantas partidas as brancas
ganharam, empataram e perderam, separando por ritmo (bullet, blitz, rápida, clássica) e
por faixa de rating. A parte visual fica no meu site.

## O problema do tamanho

Um mês do Lichess hoje tem perto de 90 milhões de partidas e 29 GB compactados (uns 200
GB de texto). Não preciso de tudo isso: com alguns milhões de partidas por mês os
números já estabilizam.

O arquivo vem em Zstandard, e uma coisa boa do formato é que dá para cortá-lo em
qualquer ponto e descompactar o que veio até ali. Então o programa pede ao servidor só o
primeiro 1 GB de cada mês (um cabeçalho HTTP `Range`), descompacta em streaming e vai
somando, sem gravar o PGN em disco. Ele também não lê os lances: só o cabeçalho de cada
partida interessa.

O preço disso é que a amostra são as partidas dos primeiros dias de cada mês. Para o que
estou medindo, não vejo motivo para o começo do mês ser diferente do resto. Os meses
antigos (até uns 2016) são menores que 1 GB e entram inteiros. O arquivo de cada mês diz
se ele é amostra ou mês completo.

## Como cada partida é contada

- **Ritmo:** a mesma regra do Lichess, tempo estimado = base + 40 × incremento. Abaixo
  de 3 minutos é bullet, até 8 é blitz, até 25 é rápida, acima disso clássica. Ultrabullet
  e correspondência ficam de fora.
- **Faixa de rating:** a média dos dois jogadores, de 200 em 200. A faixa 800 junta todo
  mundo abaixo de 1000 e a 2400 junta todo mundo acima.
- **Abertura:** o nome que o Lichess dá, em dois níveis. "Sicilian Defense: Najdorf
  Variation, English Attack" conta para a família *Sicilian Defense* e para a variante
  *Sicilian Defense: Najdorf Variation*.
- **Descarto** partidas abandonadas antes de começar, sem rating ou sem abertura
  reconhecida.

Além do placar, cada célula guarda a soma do **resultado esperado pelo Elo**:

```
E = 1 / (1 + 10^((rating das pretas − rating das brancas) / 400))
```

É isso que permite comparar aberturas de forma justa. Se quem joga a abertura X costuma
ser mais forte que o adversário, ela vai ter um aproveitamento alto mesmo que não ajude
em nada. Comparando o resultado real com o esperado, sobra o efeito da abertura (ou
pelo menos do tipo de jogador que a escolhe). Essa análise vem na próxima etapa.

## Os dados gerados

Um arquivo por mês em `meses/`, com uma linha por combinação de abertura, ritmo e faixa:

```json
["Sicilian Defense", "blitz", 1800, 18460, 1737, 18356, 18907.46]
```

Na ordem: abertura, ritmo, faixa, vitórias das brancas, empates, vitórias das pretas e
soma do esperado das brancas. Essa linha é de setembro de 2026: na Siciliana em blitz,
entre jogadores de 1800 a 2000, as brancas fizeram 50,1% dos pontos quando o Elo previa
49,0%.

Aberturas com poucas partidas no mês (menos de 50 na família, menos de 1000 na
variante) ficam de fora, senão o arquivo do mês passa de 1,5 MB só com variantes que
quase ninguém joga. `meses/indice.json` lista os meses prontos.

Somados, os meses passam de 150 MB, pesado demais para o site ler a cada visita. Para ver
como a popularidade das aberturas mudou, `evolucao.json` junta tudo por ano: quantas
partidas cada abertura teve em cada ritmo e faixa, e o total de partidas de cada um. Só
entram as aberturas que chegaram a 1% das partidas de algum ano, ritmo e faixa.

Um cuidado aqui: entre 2017 e 2021 o Lichess revisou os nomes das aberturas. Saíram coisas
como "Philidor Defense #3", "Queen's Gambit Refused" e "Indian Game", e o Petrov virou
"Russian Game". O resumo junta os nomes antigos à família atual (a lista está em
`evolucao.py`). Não dá para consertar tudo, porque algumas partidas mudaram de família de
verdade, e não só de nome: o Gambito Englund, por exemplo, quase dobra de um mês para o
outro em dezembro de 2020. Nas aberturas grandes, a diferença que sobra é de alguns
décimos de ponto percentual.

## Usando

Requer Python 3.11 ou mais novo. A única dependência é o `zstandard`.

```bash
pip install -e ".[dev]"
pytest

python -m aberturas mes 2026-09                     # amostra de 1 GB de um mês
python -m aberturas mes 2026-09 --limite-gb 0       # o mês inteiro (demora)
python -m aberturas mes 2026-09 --arquivo x.pgn.zst # de um arquivo já baixado
python -m aberturas pendentes --desde 2013-01       # todos os meses que faltam
python -m aberturas evolucao                        # refaz o evolucao.json
```

No meu computador, 1 GB levou uns 16 minutos, quase tudo esperando o download. No
GitHub Actions o mesmo mês sai em uns 2 minutos.

Um GitHub Action roda todo dia 6, quando o mês anterior já saiu, e faz commit do
arquivo novo e o `evolucao.json` refeito. Disparado na mão, ele preenche o histórico do mais novo para o mais
antigo, com um commit por mês: se a rodada estourar o limite de tempo do GitHub, o que
já foi feito fica salvo e a próxima continua de onde parou.
