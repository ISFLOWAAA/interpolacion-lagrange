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
    ExpresionInvalida,
    crear_funcion_numerica,
    evaluar_funcion,
    interpretar_funcion,
    interpretar_numero,
)


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
    assert interpretar_funcion("f(x) = e^x") == sp.exp(X)
    assert interpretar_funcion("ln(x)") == sp.log(X)
    assert interpretar_funcion("3(x+1)(x-1)") == 3 * (X + 1) * (X - 1)
    assert interpretar_funcion("sen(x)") == sp.sin(X)
    assert interpretar_numero("0,5") == sp.Rational(1, 2)
    assert interpretar_numero("1/3") == sp.Rational(1, 3)
    assert interpretar_numero("1e-3") == sp.Rational(1, 1000)


def test_entradas_peligrosas_o_invalidas():
    for texto in ["__import__('os')", "x.real", "open(x)", "x +", "1/0", "sin", "[1]", "x; x"]:
        try:
            interpretar_funcion(texto)
        except ExpresionInvalida:
            continue
        raise AssertionError(f"Se aceptó una entrada inválida: {texto}")


def test_validaciones():
    casos = [
        (["1", "1"], ["2", "3"]),      # x repetido
        (["1", ""], ["2", "3"]),       # campo vacío
        (["1", "abc"], ["2", "3"]),    # no numérico
        (["1"], ["2"]),                # menos de dos puntos
    ]
    for textos_x, textos_y in casos:
        try:
            validation.validar_puntos(textos_x, textos_y)
        except validation.ErrorValidacion:
            continue
        raise AssertionError(f"No se detectó el error en {textos_x}")
    try:
        validation.validar_puntos(["0", "1"], None, interpretar_funcion("log(x)"))
    except validation.ErrorValidacion:
        pass
    else:
        raise AssertionError("log(0) debería fallar")
    assert validation.es_extrapolacion([sp.Integer(0), sp.Integer(2)], sp.Integer(3))


def test_seno_y_error_maximo():
    funcion = interpretar_funcion("sin(x)")
    xs, ys = validation.validar_puntos(["0", "1", "2", "3"], None, funcion)
    valor, _ = lagrange.interpolar_directo(xs, ys, sp.Rational(3, 2))
    polinomio, _ = lagrange.construir_polinomio(xs, ys)
    assert abs(float(polinomio.subs(X, sp.Rational(3, 2)) - valor)) < 1e-15
    real = evaluar_funcion(funcion, sp.Rational(3, 2))
    assert abs(float(real) - math.sin(1.5)) < 1e-15
    assert 0 < float(errors.error_absoluto(real, valor)) < 0.05
    resultado = errors.error_maximo(crear_funcion_numerica(funcion), xs, ys, 0, 3, 2001)
    assert 0 < resultado["error"] < 0.05
    assert errors.error_relativo(sp.Integer(0), sp.Integer(1)) is None
    assert lagrange.grado_polinomio(polinomio) == 3


if __name__ == "__main__":
    for nombre, prueba in list(globals().items()):
        if nombre.startswith("test_"):
            prueba()
            print("OK ", nombre)
