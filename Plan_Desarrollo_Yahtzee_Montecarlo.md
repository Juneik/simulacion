# Plan de Desarrollo y Especificación Técnica
## Simulación del Juego de Yahtzee Clásico con Método de Montecarlo
### Documento de Contexto para Cursor AI

**Objetivo del documento:** Este archivo sirve como contexto completo y guía de implementación para que Cursor (u otro agente de código) desarrolle el proyecto de principio a fin: código fuente, análisis de resultados, documentación técnica y soporte para la presentación.

**Metodología pedagógica requerida:** USA → MODIFICA → CREA  
- **USA:** Usar una implementación base o reglas estándar.  
- **MODIFICA:** Mejorar la estrategia de decisión, el registro de estadísticas o la interfaz.  
- **CREA:** Añadir funcionalidades propias (gráficas de convergencia, comparación de estrategias, exportación de resultados, etc.).

---

## 1. Objetivo General

Comprender y aplicar el método de Montecarlo mediante una aplicación que simule el juego de Yahtzee clásico para 2 jugadores, permita ejecutar un gran número de simulaciones y explote los resultados aleatorios obtenidos para demostrar la **Ley de los Grandes Números**.

**Objetivos específicos:**
- Implementar las reglas oficiales del Yahtzee clásico (5 dados, hasta 3 lanzamientos por turno, 13 categorías).
- Simular partidas completas entre 2 jugadores (pueden ser humanos o agentes con estrategias).
- Ejecutar cientos o miles de partidas (Montecarlo).
- Analizar la convergencia del puntaje promedio hacia un valor esperado.
- Generar estadísticas, gráficas y conclusiones justificadas.

---

## 2. Reglas del Juego de Yahtzee (Especificación Exacta)

### 2.1 Mecánica de un turno
- Se lanzan **5 dados** de 6 caras.
- El jugador puede realizar hasta **3 lanzamientos** por turno.
- Después del 1.er y 2.º lanzamiento puede **mantener** (hold) cualquier subconjunto de dados y relanzar el resto.
- Al final del turno (después de 1, 2 o 3 lanzamientos) debe anotar el resultado en **exactamente una** categoría abierta.

### 2.2 Categorías de puntuación (13 en total)

**Sección Superior (Upper):**
| Categoría | Puntuación |
|-----------|------------|
| Ones      | Suma de los dados que muestran 1 |
| Twos      | Suma de los dados que muestran 2 |
| Threes    | Suma de los dados que muestran 3 |
| Fours     | Suma de los dados que muestran 4 |
| Fives     | Suma de los dados que muestran 5 |
| Sixes     | Suma de los dados que muestran 6 |

**Bonus Sección Superior:** Si el total de la sección superior ≥ 63 → +35 puntos.

**Sección Inferior (Lower):**
| Categoría          | Condición                          | Puntos |
|--------------------|------------------------------------|--------|
| Three of a Kind    | Al menos 3 dados iguales           | Suma de los 5 dados |
| Four of a Kind     | Al menos 4 dados iguales           | Suma de los 5 dados |
| Full House         | 3 de un número + 2 de otro         | 25 |
| Small Straight     | 4 números consecutivos             | 30 |
| Large Straight     | 5 números consecutivos             | 40 |
| Yahtzee            | 5 dados iguales                    | 50 |
| Chance             | Cualquier combinación              | Suma de los 5 dados |

### 2.3 Reglas especiales de Yahtzee adicional (Bonus y Joker)
- Si se obtiene un Yahtzee y la casilla Yahtzee ya tiene 50 puntos → se suman **+100 puntos** de bonus.
- El resultado debe anotarse en otra casilla según reglas de joker (versión simplificada recomendada para el proyecto):
  1. Si la casilla superior correspondiente al número está libre → debe usarse.
  2. Si está ocupada → puede usarse en cualquier casilla inferior abierta (como joker: Full House = 25, Small Straight = 30, Large Straight = 40, etc.).
- Si la casilla Yahtzee tiene 0, no se otorga el bonus de +100, pero se sigue la regla de joker para anotar.

### 2.4 Fin del juego
- Cada jugador completa las 13 categorías (13 turnos).
- Se suman: total superior + bonus superior + total inferior + bonuses de Yahtzee.
- Gana el jugador con mayor puntaje.

**Referencia visual:** https://solitaired.com/yahtzee

---

## 3. Diseño de la Solución Propuesta

### 3.1 Arquitectura modular recomendada (Python)

```
yahtzee_montecarlo/
├── src/
│   ├── dice.py              # Clase Dice / DiceSet
│   ├── scorecard.py         # Clase Scorecard (categorías, scoring, bonus)
│   ├── player.py            # Clase Player + estrategias
│   ├── game.py              # Clase Game (2 jugadores, flujo de turnos)
│   ├── simulator.py         # Motor Montecarlo
│   └── analysis.py          # Generación de gráficas y estadísticas
├── main.py                  # Punto de entrada (simulación + análisis)
├── requirements.txt
├── README.md
└── docs/
    └── informe_tecnico.md   # Borrador del documento final
```

### 3.2 Componentes principales

| Módulo | Responsabilidad |
|--------|-----------------|
| `Dice` | Lanzar 1 dado, lanzar varios, mantener (hold) |
| `Scorecard` | Almacenar puntuaciones, validar categorías, calcular bonus y total |
| `Player` | Tiene scorecard + estrategia de decisión (qué dados mantener y qué categoría elegir) |
| `Game` | Orquesta una partida completa de 2 jugadores |
| `Simulator` | Ejecuta N partidas, recolecta resultados |
| `Analysis` | Calcula promedios acumulados, genera gráficas de convergencia (LLN) |

### 3.3 Estrategias de jugadores (para demostrar MODIFICA / CREA)

1. **Estrategia Aleatoria** (baseline): elige dados y categoría al azar entre las válidas.
2. **Estrategia Greedy Simple**: prioriza la categoría que más puntos da en el momento.
3. **Estrategia Upper Focus** (mejora): intenta completar la sección superior para obtener el bonus de 35.
4. (Opcional avanzado) Estrategia con probabilidad estimada de obtener ciertas combinaciones.

---

## 4. Metodología de Implementación

### Fase 1 – USA (Implementación base)
- Implementar dados, scorecard y scoring correcto.
- Partida funcional entre 2 jugadores con estrategia aleatoria.
- Validar que las reglas básicas se cumplen.

### Fase 2 – MODIFICA
- Mejorar la estrategia de al menos un jugador.
- Añadir registro detallado de cada partida (puntajes por categoría, número de Yahtzees, etc.).
- Permitir configurar número de simulaciones desde línea de comandos o archivo de configuración.

### Fase 3 – CREA
- Motor Montecarlo que ejecute 1.000, 10.000 o más partidas.
- Cálculo del puntaje promedio acumulado a medida que aumenta N.
- Gráficas de convergencia (demostración de la Ley de los Grandes Números).
- Comparación de dos estrategias diferentes.
- Exportación de resultados a CSV / JSON.
- Generación automática de estadísticas para el informe.

### Herramientas recomendadas
- Lenguaje: **Python 3.10+**
- Librerías: `numpy`, `matplotlib` o `plotly`, `pandas` (opcional)
- Control de versiones: Git + GitHub público
- Documentación: Markdown + conversión a PDF/DOCX

---

## 5. Explotación de Resultados (Enfoque Montecarlo + LLN)

El programa debe permitir demostrar la **Ley de los Grandes Números**:

> A medida que el número de simulaciones \( N \) aumenta, el promedio de los puntajes observados se aproxima al valor esperado teórico (o al valor de equilibrio de la estrategia utilizada).

**Salidas esperadas:**
- Tabla o gráfica: N vs. Puntaje promedio (convergencia).
- Histograma de puntajes finales.
- Frecuencia de aparición de Yahtzee, Full House, Large Straight, etc.
- Comparación de puntaje medio entre dos estrategias.
- Intervalos de confianza aproximados.

**Ejemplo de métricas a calcular:**
- Puntaje medio final
- Desviación estándar
- Porcentaje de partidas con bonus superior (≥63)
- Número medio de Yahtzees por partida

---

## 6. Estructura del Documento Técnico Final

El informe técnico (PDF, DOCX o HTML) debe contener **como mínimo**:

1. **Introducción**
   - Contexto del método de Montecarlo.
   - Descripción breve del juego de Yahtzee.
   - Objetivo del trabajo.

2. **Metodología**
   - Diseño de la solución.
   - Reglas implementadas.
   - Estrategias de los jugadores.
   - Número de simulaciones realizadas.
   - Herramientas y lenguaje utilizados.
   - Descripción de la metodología USA – MODIFICA – CREA.

3. **Resultados**
   - Tablas de estadísticas.
   - Gráficas de convergencia (LLN).
   - Comparación de estrategias.
   - Análisis de frecuencias.

4. **Conclusiones**
   - Justificación de que se cumple la Ley de los Grandes Números.
   - Reflexión sobre las mejoras realizadas.
   - Limitaciones y posibles mejoras futuras.

5. **Referencias bibliográficas**
   - Al menos 4-5 fuentes (reglas oficiales, artículos sobre Montecarlo, documentación de librerías, etc.).

---

## 7. Guía para el Video de Presentación (máx. 5 minutos)

Contenido obligatorio:
1. Explicar el proceso de aprendizaje con la metodología **USA, MODIFICA y CREA**.
2. Presentar las principales modificaciones y mejoras realizadas sobre una solución base.
3. Justificar, a partir de los resultados obtenidos (gráficas de convergencia), por qué se cumple la **Teoría de los Grandes Números** en el juego de Yahtzee utilizando simulación de Montecarlo.

**Sugerencia de estructura:**
- 0:00–1:00 → Presentación y metodología USA-MODIFICA-CREA
- 1:00–3:00 → Demostración del programa y mejoras
- 3:00–4:30 → Resultados y justificación de la LLN
- 4:30–5:00 → Conclusiones

---

## 8. Entregables y Nomenclatura

| Entregable              | Formato                  | Nombre sugerido                     |
|-------------------------|--------------------------|-------------------------------------|
| Código fuente           | Repositorio GitHub       | `yahtzee-montecarlo` (público)      |
| Documento técnico       | PDF / DOCX / HTML        | `Apellido_Nombre_Montecarlo.pdf`    |
| Video de presentación   | Enlace (YouTube, Drive…) | Máximo 5 minutos                    |

---

## 9. Instrucciones Directas para Cursor

**Al implementar el proyecto, Cursor debe:**

1. Crear la estructura de carpetas y archivos indicada.
2. Implementar primero las clases base (`Dice`, `Scorecard`) con pruebas unitarias simples.
3. Desarrollar el flujo de una partida completa.
4. Implementar al menos dos estrategias de jugador.
5. Crear el simulador Montecarlo con capacidad de ejecutar ≥ 1.000 partidas.
6. Generar gráficas de convergencia del puntaje promedio.
7. Escribir un `README.md` claro con instrucciones de ejecución.
8. Preparar un borrador del informe técnico en Markdown siguiendo la estructura de la sección 6.
9. Incluir comentarios en el código que expliquen las decisiones de diseño relacionadas con la metodología USA-MODIFICA-CREA.

**Prioridad de implementación:**
1. Correctitud de las reglas de scoring.
2. Capacidad de simular muchas partidas rápidamente.
3. Generación de resultados visuales que demuestren la Ley de los Grandes Números.
4. Código limpio, modular y documentado.

---

## 10. Referencias Recomendadas

1. Reglas oficiales de Yahtzee (Hasbro / solitaired.com).
2. Método de Montecarlo – concepto y aplicación en juegos de azar.
3. Ley de los Grandes Números (Bernoulli / Kolmogorov).
4. Documentación de NumPy y Matplotlib.
5. Artículos o repositorios de simulación de Yahtzee con Montecarlo (ej. Medium, GitHub).

---

**Fin del documento de contexto.**

Este plan está diseñado para que Cursor pueda desarrollar de forma autónoma el código, las gráficas y el borrador del informe técnico. Se recomienda proporcionar este archivo completo como contexto inicial al agente.