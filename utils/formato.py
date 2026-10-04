"""Presentación de números y polinomios en pantalla (texto y LaTeX)."""

import sympy as sp

# Una fracción con denominador mayor que este se muestra como decimal.
DENOMINADOR_MAXIMO = 1000


def fmt_num(valor, decimales=6):
    """Número con decimales fijos. Si es muy pequeño o muy grande usa notación científica."""
    valor = float(valor)
    muy_pequeno = valor != 0 and abs(valor) < 10 ** (-decimales)
    muy_grande = abs(valor) >= 1e12
    if muy_pequeno or muy_grande:
        return f"{valor:.{decimales}e}"
    return f"{valor:.{decimales}f}"


def fmt_corto(valor):
    """Número sin ceros sobrantes (0.5 en vez de 0.500000). Se usa para los datos."""
    return f"{float(valor):.10g}"


def latex_decimal(valor, decimales=6):
    """Como fmt_num, pero escribe 1.5e-07 en la forma 1.5 × 10^-7."""
    texto = fmt_num(valor, decimales)
    if "e" in texto:
        mantisa, exponente = texto.split("e")
        return rf"{mantisa} \times 10^{{{int(exponente)}}}"
    return texto


def latex_polinomio(polinomio, decimales=6):
    """Polinomio en LaTeX.

    Los coeficientes que son fracciones sencillas se dejan exactos (1/2);
    los demás se redondean a la cantidad de decimales pedida.
    """
    redondeos = {}
    for numero in polinomio.atoms(sp.Number):
        es_fraccion_sencilla = numero.is_Rational and numero.q <= DENOMINADOR_MAXIMO
        if not es_fraccion_sencilla:
            redondeos[numero] = sp.Float(round(float(numero), decimales))
    return sp.latex(polinomio.xreplace(redondeos))


def _entre_parentesis_si_negativo(valor):
    texto = fmt_corto(valor)
    return f"({texto})" if valor < 0 else texto


def latex_base_producto(xs, i):
    """Polinomio base L_i(x) escrito como en la fórmula, antes de desarrollarlo."""
    numerador = ""
    denominador = ""
    for j, xj in enumerate(xs):
        if j != i:
            numerador += f"(x - {_entre_parentesis_si_negativo(xj)})"
            denominador += f"({fmt_corto(xs[i])} - {_entre_parentesis_si_negativo(xj)})"
    return rf"\frac{{{numerador}}}{{{denominador}}}"
