"""Funciones para presentar números y polinomios (texto y LaTeX)."""

import sympy as sp

from utils.functions import X

# Las fracciones con denominador mayor se muestran como decimales.
_DENOMINADOR_MAXIMO = 1000
# Coeficientes decimales por debajo de este valor son ruido de redondeo.
_RUIDO = 1e-20


def fmt_num(valor, decimales=6):
    """Número con decimales fijos; notación científica si es muy pequeño o grande."""
    valor = float(valor)
    if valor != 0 and (abs(valor) < 10 ** (-decimales) or abs(valor) >= 1e12):
        return f"{valor:.{decimales}e}"
    return f"{valor:.{decimales}f}"


def fmt_corto(valor):
    """Número en forma compacta (sin ceros sobrantes), para datos de entrada."""
    return f"{float(valor):.10g}"


def latex_decimal(valor, decimales=6):
    """Igual que fmt_num, pero la notación científica se escribe como potencia de 10."""
    texto = fmt_num(valor, decimales)
    if "e" in texto:
        mantisa, exponente = texto.split("e")
        return rf"{mantisa} \times 10^{{{int(exponente)}}}"
    return texto


def _latex_magnitud(valor, decimales):
    """Valor absoluto de un coeficiente: entero o fracción si es exacto."""
    valor = abs(valor)
    if valor.is_Rational and valor.q <= _DENOMINADOR_MAXIMO:
        return str(valor.p) if valor.q == 1 else rf"\frac{{{valor.p}}}{{{valor.q}}}"
    return latex_decimal(valor, decimales)


def latex_polinomio(polinomio, decimales=6):
    """Polinomio en LaTeX, ordenado de mayor a menor grado."""
    coeficientes = sp.Poly(polinomio, X).all_coeffs()
    grado_maximo = len(coeficientes) - 1
    partes = []
    for posicion, coeficiente in enumerate(coeficientes):
        grado = grado_maximo - posicion
        if coeficiente == 0 or (not coeficiente.is_Rational and abs(coeficiente) < _RUIDO):
            continue
        variable = "" if grado == 0 else ("x" if grado == 1 else f"x^{{{grado}}}")
        magnitud = _latex_magnitud(coeficiente, decimales)
        if variable and abs(coeficiente) == 1:
            magnitud = ""
        signo = "-" if coeficiente < 0 else "+"
        if not partes:
            signo = "-" if coeficiente < 0 else ""
        partes.append(f"{signo} {magnitud}{variable}".strip())
    return " ".join(partes) if partes else "0"


def _resta(minuendo, valor):
    """Texto de 'minuendo - valor' sin dobles signos."""
    if valor == 0:
        return minuendo
    if valor > 0:
        return f"{minuendo} - {fmt_corto(valor)}"
    return f"{minuendo} + {fmt_corto(-valor)}"


def latex_base_producto(xs, indice):
    """Polinomio base L_i(x) escrito como cociente de productos."""
    otros = [xj for j, xj in enumerate(xs) if j != indice]
    numerador = "".join(f"({_resta('x', xj)})" for xj in otros)
    denominador = "".join(f"({_resta(fmt_corto(xs[indice]), xj)})" for xj in otros)
    return rf"\frac{{{numerador}}}{{{denominador}}}"
