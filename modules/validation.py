"""Revisión de los datos que escribe el usuario.

Si un dato está mal, se lanza ErrorEntrada con un mensaje fácil de entender.
"""

from utils.formato import fmt_corto
from utils.functions import ErrorEntrada, evaluar_funcion, interpretar_funcion, interpretar_numero

MINIMO_PUNTOS = 2


def validar_funcion(texto):
    """Devuelve la función interpretada, o None si la casilla está vacía."""
    if not texto.strip():
        return None
    try:
        return interpretar_funcion(texto)
    except ErrorEntrada as error:
        raise ErrorEntrada(f"La función no es válida: {error}") from None


def validar_numero(texto, nombre):
    """Convierte una casilla en número. `nombre` dice qué casilla es, para el mensaje."""
    if not texto.strip():
        raise ErrorEntrada(f"{nombre} está vacío.")
    try:
        return interpretar_numero(texto)
    except ErrorEntrada:
        raise ErrorEntrada(f"{nombre} no es un número válido («{texto.strip()}»).") from None


def validar_puntos(textos_x, textos_y, funcion=None):
    """Revisa los puntos y los devuelve como números: (xs, ys).

    Si textos_y es None, los valores de y se calculan con la función.
    """
    if len(textos_x) < MINIMO_PUNTOS:
        raise ErrorEntrada("Se necesitan al menos dos puntos para construir el polinomio.")

    xs = []
    for i, texto in enumerate(textos_x):
        x = validar_numero(texto, f"El valor de x del punto {i + 1}")
        if x in xs:
            raise ErrorEntrada(
                f"El valor x = {fmt_corto(x)} está repetido (puntos {xs.index(x) + 1} y {i + 1}). "
                "Todos los valores de x deben ser distintos."
            )
        xs.append(x)

    if textos_y is None:
        if funcion is None:
            raise ErrorEntrada("Para calcular f(x) automáticamente debes ingresar una función válida.")
        ys = [evaluar_funcion(funcion, x) for x in xs]
    else:
        ys = [validar_numero(texto, f"El valor de f(x) del punto {i + 1}") for i, texto in enumerate(textos_y)]
    return xs, ys


def validar_intervalo(texto_a, texto_b):
    """Revisa el intervalo [a, b] y lo devuelve como números."""
    a = validar_numero(texto_a, "El extremo a")
    b = validar_numero(texto_b, "El extremo b")
    if a >= b:
        raise ErrorEntrada("El intervalo no es válido: a debe ser menor que b.")
    return a, b


def es_extrapolacion(xs, x_eval):
    """True si x_eval está fuera del rango que cubren los puntos."""
    return bool(x_eval < min(xs) or x_eval > max(xs))
