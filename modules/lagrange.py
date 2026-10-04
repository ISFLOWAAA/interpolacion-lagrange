"""Interpolación polinómica de Lagrange.

Este archivo solo contiene la matemática; no sabe nada de la página web.

    Polinomio interpolante:   P(x)   = suma de  y_i * L_i(x)
    Polinomios base:          L_i(x) = producto de (x - x_j) / (x_i - x_j), para j distinto de i
"""

import numpy as np
import sympy as sp

from utils.functions import X


def polinomio_base(xs, i):
    """Polinomio base L_i(x): vale 1 en x_i y 0 en los demás puntos."""
    base = sp.Integer(1)
    for j, xj in enumerate(xs):
        if j != i:
            base = base * (X - xj) / (xs[i] - xj)
    return sp.expand(base)


def construir_polinomio(xs, ys):
    """Construye el polinomio interpolante.

    Devuelve el polinomio ya simplificado y la lista de polinomios base.
    """
    bases = [polinomio_base(xs, i) for i in range(len(xs))]
    polinomio = sp.Integer(0)
    for yi, base in zip(ys, bases):
        polinomio = polinomio + yi * base
    return sp.expand(polinomio), bases


def grado_polinomio(polinomio):
    """Grado del polinomio obtenido (puede ser menor que n)."""
    if polinomio == 0:
        return 0
    return int(sp.degree(polinomio, X))


def interpolar_directo(xs, ys, x_eval):
    """Calcula P(x_eval) sin construir el polinomio.

    Se sustituye x_eval directamente en la fórmula de Lagrange, así que cada
    L_i(x_eval) es un número. Devuelve el valor y los pasos del cálculo.
    """
    total = sp.Integer(0)
    pasos = []
    for i, (xi, yi) in enumerate(zip(xs, ys)):
        peso = sp.Integer(1)  # será L_i(x_eval)
        for j, xj in enumerate(xs):
            if j != i:
                peso = peso * (x_eval - xj) / (xi - xj)
        termino = yi * peso
        total = total + termino
        pasos.append({"i": i, "x": xi, "y": yi, "L": peso, "termino": termino})
    return total, pasos


def evaluar_en_malla(xs, ys, malla):
    """Calcula P(x) en muchos puntos a la vez (para la gráfica y el error máximo).

    Es la misma fórmula de interpolar_directo, pero con NumPy para que sea rápida.
    """
    xs = [float(x) for x in xs]
    ys = [float(y) for y in ys]
    malla = np.asarray(malla, dtype=float)
    resultado = np.zeros_like(malla)
    for i in range(len(xs)):
        peso = np.ones_like(malla)
        for j in range(len(xs)):
            if j != i:
                peso = peso * (malla - xs[j]) / (xs[i] - xs[j])
        resultado = resultado + ys[i] * peso
    return resultado
