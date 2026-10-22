"""Simulación de Yahtzee clásico con el método de Montecarlo.

La organización del paquete sigue la metodología USA → MODIFICA → CREA:
- USA: ``dice`` y ``scorecard`` implementan las reglas base.
- MODIFICA: ``player`` añade estrategias de decisión por encima del juego aleatorio.
- CREA: ``simulator`` y ``analysis`` estiman valores esperados y muestran
  la Ley de los Grandes Números.
"""

__version__ = "1.0.0"
