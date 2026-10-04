"""Cálculo de errores de la interpolación."""

import numpy as np

from modules.lagrange import evaluar_en_malla


def error_absoluto(valor_real, valor_aproximado):
    """E_a = |f(x) - P_n(x)|"""
    return abs(valor_real - valor_aproximado)


def error_relativo(valor_real, valor_aproximado):
    """E_r = |f(x) - P_n(x)| / |f(x)|. Devuelve None si f(x) = 0."""
    if valor_real == 0:
        return None
    return error_absoluto(valor_real, valor_aproximado) / abs(valor_real)


def error_porcentual(valor_real, valor_aproximado):
    """E_r expresado en porcentaje. Devuelve None si f(x) = 0."""
    relativo = error_relativo(valor_real, valor_aproximado)
    return None if relativo is None else relativo * 100


def error_maximo(funcion_numerica, xs, ys, a, b, cantidad_puntos=2000):
    """Estima max |f(x) - P_n(x)| en [a, b] evaluando en puntos equiespaciados.

    Devuelve un diccionario con el error máximo, el x donde ocurre, la malla,
    los errores en cada punto y cuántos puntos se omitieron porque f no está
    definida en ellos.
    """
    malla = np.linspace(float(a), float(b), int(cantidad_puntos))
    errores = np.abs(funcion_numerica(malla) - evaluar_en_malla(xs, ys, malla))
    no_definidos = int(np.isnan(errores).sum())
    if no_definidos == len(malla):
        raise ValueError("La función no está definida en ningún punto del intervalo.")
    posicion = int(np.nanargmax(errores))
    return {
        "error": float(errores[posicion]),
        "x": float(malla[posicion]),
        "malla": malla,
        "errores": errores,
        "no_definidos": no_definidos,
    }
