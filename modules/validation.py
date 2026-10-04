"""Validación de los datos ingresados por el usuario.

Todas las funciones lanzan ErrorValidacion con un mensaje fácil de entender.
"""

import sympy as sp

from utils.formato import fmt_corto
from utils.functions import (
    ExpresionInvalida,
    FuncionNoDefinida,
    evaluar_funcion,
    interpretar_funcion,
    interpretar_numero,
)

MINIMO_PUNTOS = 2
_TOLERANCIA_IGUALDAD = sp.Float("1e-20")


class ErrorValidacion(ValueError):
    """Dato incorrecto; el mensaje se muestra tal cual al usuario."""


def validar_funcion(texto):
    """Devuelve la función interpretada, o None si el campo está vacío."""
    if not texto.strip():
        return None
    try:
        return interpretar_funcion(texto)
    except ExpresionInvalida as error:
        raise ErrorValidacion(f"La función no es válida: {error}") from None


def validar_numero(texto, nombre):
    """Convierte un campo de texto en número. `nombre` describe el campo."""
    if not texto.strip():
        raise ErrorValidacion(f"{nombre} está vacío.")
    try:
        return interpretar_numero(texto)
    except ExpresionInvalida:
        raise ErrorValidacion(f"{nombre} no es un número válido («{texto.strip()}»).") from None


def evaluar_funcion_validada(funcion, valor):
    """Evalúa f en un punto y traduce el fallo a un mensaje claro."""
    try:
        return evaluar_funcion(funcion, valor)
    except FuncionNoDefinida:
        raise ErrorValidacion(
            f"La función no está definida en x = {fmt_corto(valor)} "
            "(por ejemplo, división por cero o logaritmo de un número no positivo)."
        ) from None


def validar_puntos(textos_x, textos_y=None, funcion=None):
    """Valida los puntos y devuelve (xs, ys).

    Si textos_y es None, los valores de y se calculan con la función.
    """
    if len(textos_x) < MINIMO_PUNTOS:
        raise ErrorValidacion("Se necesitan al menos dos puntos para construir el polinomio.")

    xs = [validar_numero(texto, f"El valor de x del punto {i + 1}") for i, texto in enumerate(textos_x)]

    for i in range(len(xs)):
        for j in range(i):
            if abs(sp.N(xs[i] - xs[j], 30)) < _TOLERANCIA_IGUALDAD:
                raise ErrorValidacion(
                    f"El valor x = {fmt_corto(xs[i])} está repetido (puntos {j + 1} y {i + 1}). "
                    "Todos los valores de x deben ser distintos."
                )

    if textos_y is None:
        if funcion is None:
            raise ErrorValidacion("Para calcular f(x) automáticamente debes ingresar una función válida.")
        ys = [evaluar_funcion_validada(funcion, x) for x in xs]
    else:
        ys = [validar_numero(texto, f"El valor de f(x) del punto {i + 1}") for i, texto in enumerate(textos_y)]
    return xs, ys


def validar_intervalo(texto_a, texto_b):
    """Valida el intervalo [a, b] con a < b."""
    a = validar_numero(texto_a, "El extremo a")
    b = validar_numero(texto_b, "El extremo b")
    if not a < b:
        raise ErrorValidacion("El intervalo no es válido: a debe ser menor que b.")
    return a, b


def es_extrapolacion(xs, x_eval):
    """True si x_eval está fuera del intervalo que cubren los puntos."""
    return bool(x_eval < min(xs) or x_eval > max(xs))
