# Yahtzee con Montecarlo

Simulación del Yahtzee clásico para dos jugadores. El programa aplica las reglas de puntuación, compara tres estrategias y repite miles de partidas independientes para estimar el puntaje esperado de cada una. Las gráficas muestran cómo esa media se estabiliza al crecer el número de partidas: es la Ley de los Grandes Números aplicada a un juego de dados.

La guía del profesor está en la carpeta anterior a este programa:

- `simulacion_01.ipynb`: dos jugadores y bloqueo de dados por Montecarlo (32 máscaras y valor esperado).
- `Laboratorio Yahtzee.jsx`: tablero para que dos personas jueguen el turno.
- `Laboratorio Yahtzee Montecarlo.html`: enunciado del laboratorio y la idea de que cada cara sale con probabilidad 1/6.

Este programa usa ese cuaderno como punto de partida y deja escrito qué se cambió.

| Fase | Qué aporta respecto de la guía | Dónde está |
|------|--------------------------------|------------|
| USA | Las 32 máscaras y la estimación del valor esperado para decidir qué dados conservar | `src/guide_montecarlo.py` |
| MODIFICA | Bonus de 35, comodín de Yahtzee, corrección del último relanzamiento, semilla por partida, estrategias ávida y de sección superior | `src/scorecard.py`, `src/player.py` |
| CREA | Miles de partidas, comparación de políticas, CSV/JSON y convergencia del puntaje de la partida, además del experimento de una máscara que ya traía el cuaderno | `src/simulator.py`, `src/analysis.py` |

## Requisitos

- Python 3.10 o superior
- NumPy, Matplotlib y pytest (`requirements.txt`)

En Windows, si `python` abre la tienda de Microsoft, usa el intérprete del entorno virtual o `uv`.

## Instalación

Desde esta carpeta (`yahtzee_montecarlo`):

```powershell
uv venv --python 3.12
uv pip install -r requirements.txt
```

Con el lanzador de Python, el equivalente es:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

## Uso

```powershell
# Una partida, turno a turno
.\.venv\Scripts\python.exe main.py --demo --estrategia-1 avida --estrategia-2 seccion_superior --semilla 42

# Una comparación
.\.venv\Scripts\python.exe main.py --partidas 5000 --estrategia-1 aleatoria --estrategia-2 avida --semilla 42

# Las dos comparaciones del informe (10 000 partidas cada una)
.\.venv\Scripts\python.exe main.py --suite --partidas 10000 --semilla 42 --salida results/10000_partidas

# Réplica del experimento de convergencia del cuaderno (una máscara)
.\.venv\Scripts\python.exe main.py --convergencia-guia --semilla 42

# La política de la guía contra la ávida
.\.venv\Scripts\python.exe main.py -n 1000 --estrategia-1 montecarlo --estrategia-2 avida --sims-mascara 24 --semilla 44 --salida results/1000_partidas/montecarlo_vs_avida

# Pruebas de reglas, comodín y partida completa
.\.venv\Scripts\python.exe -m pytest
```

Estrategias: `montecarlo` (la de la guía), `aleatoria`, `avida`, `seccion_superior`. También se aceptan los alias `guia`, `random`, `greedy` y `upper`. `--sims-mascara` solo cambia la precisión de `montecarlo`; el valor usado en el informe es 24.

`--suite` escribe dos experimentos. El segundo usa la semilla indicada más uno, para que cada bloque sea reproducible y distinto del otro.

| Argumento | Valor por defecto | Función |
|-----------|-------------------|---------|
| `--partidas`, `-n` | 5000 | Partidas por pareja de estrategias |
| `--estrategia-1`, `--estrategia-2` | aleatoria, avida | Políticas de los dos jugadores |
| `--semilla` | 42 | Semilla maestra |
| `--salida` | `results` | Carpeta de CSV, JSON y PNG |
| `--demo` | — | Una sola partida comentada |
| `--sin-graficas` | — | Exporta datos y omite los PNG |
| `--progreso` | 1000 | Aviso cada tantas partidas; `0` lo apaga |
| `--sims-mascara` | 24 | Muestras por máscara de la estrategia `montecarlo` |
| `--convergencia-guia` | — | Replica el experimento de una máscara del cuaderno |

## Qué hace cada estrategia

- **Montecarlo (guía).** Estima el valor de las 32 formas de conservar dados y se queda con la de mayor promedio. Es el método del cuaderno, con el último relanzamiento corregido y con la tarjeta de bonuses.
- **Aleatoria.** Conserva cada dado con probabilidad 1/2 y anota una casilla legal al azar. Es la línea base, sin leer la tirada.
- **Ávida (MODIFICA).** Conserva tríos, parejas o la escalera más larga, se planta ante un Yahtzee, una escalera grande o un puntaje alto en el último relanzamiento, y anota la casilla legal de más puntos.
- **Sección superior (MODIFICA).** Busca al menos tres dados de cada número para acercarse a los 63 puntos del bonus de 35. Solo desvía la tirada a la sección inferior cuando el puntaje inmediato es alto (25 o más).

La ávida y la de sección superior no calculan el valor esperado del juego completo. La de la guía sí estima el del turno, con la máscara fija durante la simulación.

## Menú de Windows

Doble clic en `Ejecutar Yahtzee.bat`. El primer menú usa la semilla 42, así que cada opción repite el mismo resultado. La opción 5 abre un segundo menú, sin semilla fija: cada corrida es distinta y se guarda en `results/sin_semilla/`, sin reemplazar las figuras del informe. Desde ese menú, la opción 5 vuelve al modo con semilla. La opción 6 cierra la ventana.

| Opción | Partidas | Carpeta con semilla |
|--------|----------|---------------------|
| 1 | 1 | se muestra en la ventana |
| 2 | 100 | `results/100_partidas` |
| 3 | 10 000 | `results/10000_partidas` |
| 4 | 100 000 | `results/100000_partidas` |

## Resultados que ya están generados

La carpeta `results/10000_partidas/` contiene una ejecución de 10 000 partidas por pareja (semillas 42 y 43):

| Comparación | Media | Bonus superior | Victorias |
|-------------|------:|---------------:|----------:|
| Aleatoria | 45,93 | 0 % | 2 / 10 000 |
| Ávida | 201,69 | 2,1 % | 9 998 / 10 000 |
| Ávida (otra muestra) | 201,39 | 2,1 % | 4 791 / 10 000 |
| Sección superior | 200,47 | 36,1 % | 5 146 / 10 000 |
| Montecarlo (guía), 1 000 partidas | 198,10 | 0,6 % | 529 / 1 000 |
| Ávida, en ese mismo enfrentamiento | 203,25 | 2,2 % | 463 / 1 000 |

En el segundo experimento hubo 63 empates. En el de Montecarlo contra ávida, guardado en `results/1000_partidas/`, hubo 8. La misma semilla con 100 y con 100 000 partidas deja las medias en el mismo lugar: la aleatoria pasa de 43,04 a 46,07 y la ávida de 195,75 a 202,59. La convergencia de una máscara, la del cuaderno, está en `results/convergencia_ev_guia.png`: el valor esperado pasa de 17,80 con 10 muestras a 17,29 con 10 000, y desde 1 000 muestras ya no se mueve de forma apreciable. El detalle de las 10 000 partidas está en `results/10000_partidas/suite_resumen.json`. Cada comparación incluye:

- `convergencia.png` — media acumulada frente a N
- `desviacion_lln.png` — distancia de esa media a la media final de la muestra
- `histograma.png` — distribución del puntaje
- `comparacion_estrategias.png` — componentes del puntaje
- `frecuencia_categorias.png` — puntos medios por casilla
- `partidas.csv` y `resumen.json`

El borrador del informe, con estas cifras y la lectura de las gráficas, está en `docs/informe_tecnico.md`.

## Estructura

```
yahtzee_montecarlo/
├── main.py
├── requirements.txt
├── src/
│   ├── dice.py
│   ├── scorecard.py
│   ├── player.py
│   ├── game.py
│   ├── simulator.py
│   └── analysis.py
├── tests/
├── results/
└── docs/
    └── informe_tecnico.md
```

## Reglas implementadas

Cinco dados, hasta tres lanzamientos y trece categorías. El bonus superior suma 35 si la sección alta llega a 63. Un Yahtzee adicional suma 100 solo cuando la casilla Yahtzee ya vale 50. En ese caso, y también si esa casilla quedó en cero, la tirada se anota como comodín: primero en la casilla superior del número; si está ocupada, en una casilla inferior abierta (full 25, escalera pequeña 30, escalera grande 40); si no queda ninguna, se anota cero en otra casilla superior.

## Reproducibilidad

Cada partida recibe una semilla derivada de la semilla maestra y empieza con tarjetas vacías. Dadas las estrategias, las partidas son independientes y de la misma distribución. Repetir el comando con la misma semilla y el mismo `N` reproduce puntajes, tablas y figuras.
