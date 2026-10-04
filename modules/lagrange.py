"""Interpolación polinómica de Lagrange.

Este módulo solo contiene matemática: no depende de la interfaz web.

    P_n(x) = sum_{i=0}^{n} y_i * L_i(x)
    L_i(x) = prod_{j != i} (x - x_j) / (x_i - x_j)
"""

import numpy as np
import sympy as sp

from utils.functions import X


def polinomio_base(xs, indice):
    """Polinomio base L_i(x), expandido."""
    base = sp.Integer(1)
    for j, xj in enumerate(xs):
        if j != indice:
            base *= (X - xj) / (xs[indice] - xj)
    return sp.expand(base)


def construir_polinomio(xs, ys):
    """Construye el polinomio interpolante.

    Devuelve (polinomio expandido, lista de polinomios base L_i).
    """
    bases = [polinomio_base(xs, i) for i in range(len(xs))]
    polinomio = sp.expand(sum(yi * base for yi, base in zip(ys, bases)))
    return polinomio, bases


def grado_polinomio(polinomio, tolerancia=1e-12):
    """Grado real del polinomio (puede ser menor que n si los puntos lo permiten)."""
    coeficientes = sp.Poly(polinomio, X).all_coeffs()
    escala = max(1, max(abs(c) for c in coeficientes))
    for posicion, coeficiente in enumerate(coeficientes):
        if abs(coeficiente) > tolerancia * escala:
            return len(coeficientes) - 1 - posicion
    return 0


def interpolar_directo(xs, ys, x_eval):
    """Calcula P_n(x_eval) con la fórmula de Lagrange, sin construir el polinomio.

    Devuelve (valor, pasos), donde cada paso guarda L_i(x_eval) y el término
    y_i * L_i(x_eval) para poder mostrar el procedimiento.
    """
    total = sp.Integer(0)
    pasos = []
    for i, (xi, yi) in enumerate(zip(xs, ys)):
        peso = sp.Integer(1)
        for j, xj in enumerate(xs):
            if j != i:
                peso *= (x_eval - xj) / (xi - xj)
        termino = yi * peso
        total += termino
        pasos.append({"i": i, "x": xi, "y": yi, "L": peso, "termino": termino})
    return total, pasos


def evaluar_en_malla(xs, ys, malla):
    """Evalúa P_n en muchos puntos a la vez (NumPy), con la fórmula directa."""
    xs = np.array([float(x) for x in xs])
    ys = np.array([float(y) for y in ys])
    malla = np.asarray(malla, dtype=float)
    resultado = np.zeros_like(malla)
    for i in range(len(xs)):
        peso = np.ones_like(malla)
        for j in range(len(xs)):
            if j != i:
                peso *= (malla - xs[j]) / (xs[i] - xs[j])
        resultado += ys[i] * peso
    return resultado
