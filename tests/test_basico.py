"""Pruebas de la lógica matemática.

Ejecutar desde la carpeta del proyecto:  python tests/test_basico.py
"""

import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import sympy as sp

from modules import errors, lagrange, validation
from utils import formato
from utils.functions import (
    X,
    ErrorEntrada,
    crear_funcion_numerica,
    evaluar_funcion,
    interpretar_funcion,
    interpretar_numero,
)


def debe_fallar(accion, *argumentos):
    """Comprueba que la acción rechaza los datos con ErrorEntrada."""
    try:
        accion(*argumentos)
    except ErrorEntrada:
        return
    raise AssertionError(f"No se detectó el error en {argumentos}")


def test_ejemplo_cuadratico():
    xs, ys = validation.validar_puntos(["0", "1", "2"], ["0", "1", "4"])
    polinomio, bases = lagrange.construir_polinomio(xs, ys)
    assert polinomio == X**2
    assert sum(bases) == 1
    assert formato.latex_polinomio(polinomio) == "x^{2}"
    valor, _ = lagrange.interpolar_directo(xs, ys, sp.Rational(3, 2))
    assert valor == sp.Rational(9, 4)
    assert errors.error_absoluto(sp.Rational(9, 4), valor) == 0


def test_interpretar_funciones():
    assert interpretar_funcion("x² + 2x + 1") == X**2 + 2 * X + 1
    assert interpretar_funcion("x**2 + 2*x + 1") == X**2 + 2 * X + 1
    assert interpretar_funcion("f(x) = e^x") == sp.exp(X)
    assert interpretar_funcion("ln(x)") == sp.log(X)
    assert interpretar_funcion("log10(x)") == sp.log(X, 10)
    assert interpretar_funcion("3(x+1)(x-1)") == 3 * (X + 1) * (X - 1)
    assert interpretar_funcion("x(x+1)") == X * (X + 1)
    assert interpretar_funcion("2pi x") == 2 * sp.pi * X
    assert interpretar_funcion("sen(x)") == sp.sin(X)
    assert interpretar_funcion("Sqrt(x) + abs(x)") == sp.sqrt(X) + sp.Abs(X)
    assert interpretar_funcion("1/(1+25x^2)") == 1 / (1 + 25 * X**2)
    assert interpretar_funcion("0.1x") == X / 10
    assert interpretar_numero("0,5") == sp.Rational(1, 2)
    assert interpretar_numero("1/3") == sp.Rational(1, 3)
    assert interpretar_numero("1e-3") == sp.Rational(1, 1000)
    assert interpretar_numero("-2") == -2
    assert abs(float(interpretar_numero("pi/2")) - math.pi / 2) < 1e-15


def test_entradas_peligrosas_o_invalidas():
    textos = [
        "__import__('os')", "x.real", "x.e", "open(x)", "import os", "lambda: 1", "x +", "1/0",
        "sin", "[1]", "x; x", "9^9^9", "2^99999", "x^(9^9)^9", "0,5x", "",
    ]
    for texto in textos:
        debe_fallar(interpretar_funcion, texto)
    for texto in ["abc", "x", "1/0", "", "sqrt(-1)"]:
        debe_fallar(interpretar_numero, texto)


def test_validaciones():
    debe_fallar(validation.validar_puntos, ["1", "1"], ["2", "3"])       # x repetido
    debe_fallar(validation.validar_puntos, ["0.5", "1/2"], ["2", "3"])   # x repetido con otra escritura
    debe_fallar(validation.validar_puntos, ["1", ""], ["2", "3"])        # casilla vacía
    debe_fallar(validation.validar_puntos, ["1", "abc"], ["2", "3"])     # no es un número
    debe_fallar(validation.validar_puntos, ["1"], ["2"])                 # menos de dos puntos
    debe_fallar(validation.validar_puntos, ["0", "1"], None, interpretar_funcion("log(x)"))  # log(0)
    debe_fallar(validation.validar_intervalo, "5", "1")
    assert validation.es_extrapolacion([sp.Integer(0), sp.Integer(2)], sp.Integer(3))
    assert not validation.es_extrapolacion([sp.Integer(0), sp.Integer(2)], sp.Integer(1))


def test_seno_y_error_maximo():
    funcion = interpretar_funcion("sin(x)")
    xs, ys = validation.validar_puntos(["0", "1", "2", "3"], None, funcion)
    valor, _ = lagrange.interpolar_directo(xs, ys, sp.Rational(3, 2))
    polinomio, _ = lagrange.construir_polinomio(xs, ys)
    assert abs(float(polinomio.subs(X, sp.Rational(3, 2)) - valor)) < 1e-15
    real = evaluar_funcion(funcion, sp.Rational(3, 2))
    assert abs(float(real) - math.sin(1.5)) < 1e-15
    assert abs(float(valor) - 0.975987) < 1e-6
    assert abs(float(errors.error_absoluto(real, valor)) - 0.021508) < 1e-6
    resultado = errors.error_maximo(crear_funcion_numerica(funcion), xs, ys, 0, 3, 2000)
    assert abs(resultado["error"] - 0.037226) < 1e-6
    assert lagrange.grado_polinomio(polinomio) == 3
    assert formato.latex_polinomio(polinomio) == "- 0.010393 x^{3} - 0.355643 x^{2} + 1.207507 x"


def test_presentacion():
    xs, ys = validation.validar_puntos(["0", "1", "2"], ["0", "1", "4"])
    _, bases = lagrange.construir_polinomio(xs, ys)
    assert formato.latex_polinomio(bases[0]) == r"\frac{x^{2}}{2} - \frac{3 x}{2} + 1"
    assert formato.latex_base_producto(xs, 0) == r"\frac{(x - 1)(x - 2)}{(0 - 1)(0 - 2)}"
    assert formato.latex_base_producto([sp.Integer(-1), sp.Integer(2)], 1) == r"\frac{(x - (-1))}{(2 - (-1))}"
    assert formato.fmt_num(0.5, 6) == "0.500000"
    assert formato.fmt_num(0.00000012345, 6) == "1.234500e-07"
    assert formato.latex_decimal(0.00000012345, 4) == r"1.2345 \times 10^{-7}"


def test_error_relativo_con_valor_real_cero():
    assert errors.error_relativo(sp.Integer(0), sp.Integer(1)) is None
    # cos(pi/2) es cero salvo por el redondeo de pi: el error relativo no está definido.
    real = evaluar_funcion(interpretar_funcion("cos(x)"), interpretar_numero("pi/2"))
    assert errors.error_relativo(real, sp.Float("0.05")) is None
    assert errors.error_porcentual(real, sp.Float("0.05")) is None


if __name__ == "__main__":
    for nombre, prueba in list(globals().items()):
        if nombre.startswith("test_"):
            prueba()
            print("OK ", nombre)
