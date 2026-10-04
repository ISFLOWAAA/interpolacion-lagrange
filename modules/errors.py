"""Errores de la interpolación: absoluto, relativo, porcentual y máximo."""

import numpy as np

from modules.lagrange import evaluar_en_malla

# Un valor real más pequeño que esto se considera cero, para no dividir entre él.
CERO = 1e-12


def error_absoluto(valor_real, valor_aproximado):
    """E_a = |f(x) - P(x)|"""
    return abs(valor_real - valor_aproximado)


def error_relativo(valor_real, valor_aproximado):
    """E_r = |f(x) - P(x)| / |f(x)|. Devuelve None si f(x) es cero."""
    if abs(valor_real) < CERO:
        return None
    return error_absoluto(valor_real, valor_aproximado) / abs(valor_real)


def error_porcentual(valor_real, valor_aproximado):
    """Error relativo en porcentaje. Devuelve None si f(x) es cero."""
    relativo = error_relativo(valor_real, valor_aproximado)
    if relativo is None:
        return None
    return relativo * 100


def error_maximo(funcion_numerica, xs, ys, a, b, cantidad_puntos=2000):
    """Estima el mayor valor de |f(x) - P(x)| en el intervalo [a, b].

    Se calcula el error en muchos puntos repartidos por igual y se toma el mayor.
    """
    malla = np.linspace(float(a), float(b), int(cantidad_puntos))
    errores = np.abs(funcion_numerica(malla) - evaluar_en_malla(xs, ys, malla))

    # Los puntos donde f no está definida valen NaN y no se tienen en cuenta.
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
