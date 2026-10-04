"""Lectura de las funciones y los números que escribe el usuario.

El texto se revisa ANTES de interpretarlo: solo puede contener números,
operaciones y los nombres de la lista NOMBRES_PERMITIDOS. Así nadie puede
ejecutar código escribiendo en la casilla de la función.
"""

import re

import numpy as np
import sympy as sp
from sympy.parsing.sympy_parser import (
    convert_xor,
    implicit_multiplication,
    parse_expr,
    rationalize,
    standard_transformations,
)

# La variable x de todas las fórmulas.
X = sp.Symbol("x")

# Cantidad de dígitos con que se calculan los valores que no son exactos.
PRECISION = 30

# Lo único que se puede escribir en una función, además de números y operaciones.
NOMBRES_PERMITIDOS = {
    "x": X,
    "pi": sp.pi,
    "e": sp.E,
    "sin": sp.sin, "sen": sp.sin, "cos": sp.cos, "tan": sp.tan,
    "asin": sp.asin, "acos": sp.acos, "atan": sp.atan,
    "sinh": sp.sinh, "cosh": sp.cosh, "tanh": sp.tanh,
    "exp": sp.exp,
    "log": sp.log, "ln": sp.log,
    "log10": lambda valor: sp.log(valor, 10),
    "sqrt": sp.sqrt,
    "abs": sp.Abs,
}

# Símbolos que se aceptan y se cambian por su forma estándar.
SIMBOLOS = {"²": "^2", "³": "^3", "**": "^", "×": "*", "·": "*", "÷": "/", "−": "-", "π": "pi", "√": "sqrt"}

# Reglas de lectura de SymPy:
#   convert_xor              ->  x^2 significa "x al cuadrado"
#   implicit_multiplication  ->  2x significa 2*x
#   rationalize              ->  0.1 se guarda exacto, como 1/10
REGLAS = standard_transformations + (convert_xor, implicit_multiplication, rationalize)


class ErrorEntrada(ValueError):
    """Dato mal escrito. El mensaje se muestra al usuario."""


def interpretar_funcion(texto):
    """Convierte un texto como 'x^2 + 2x + 1' en una función de SymPy."""
    texto = texto.lower().strip()
    texto = re.sub(r"^(f\s*\(\s*x\s*\)|y)\s*=", "", texto)  # quita "f(x) =" si lo escribieron
    for simbolo, reemplazo in SIMBOLOS.items():
        texto = texto.replace(simbolo, reemplazo)
    if not texto.strip():
        raise ErrorEntrada("la expresión está vacía.")

    # Revisión 1: solo números, letras minúsculas, operaciones, paréntesis y punto decimal.
    if not re.fullmatch(r"[0-9a-z+\-*/^(). ]+", texto):
        raise ErrorEntrada("contiene caracteres no permitidos.")
    if re.search(r"\.(?!\d)", texto):
        raise ErrorEntrada("hay un punto decimal mal ubicado.")

    # Revisión 2: todas las palabras deben estar en la lista de nombres permitidos.
    for nombre in re.findall(r"[a-z]+[0-9]*", texto):
        if nombre not in NOMBRES_PERMITIDOS:
            raise ErrorEntrada(f"nombre no reconocido: «{nombre}».")

    # Revisión 3: potencias gigantes (2^99999 o 9^9^9) dejarían el programa bloqueado.
    if re.search(r"\^\s*\(?\s*\d{4,}", texto) or re.search(r"\^\s*\(?\s*\d+\s*\)?\s*\^", texto):
        raise ErrorEntrada("el exponente es demasiado grande.")

    # Con el texto ya revisado, SymPy lo convierte en una expresión matemática.
    try:
        funcion = parse_expr(texto, local_dict=NOMBRES_PERMITIDOS, transformations=REGLAS)
    except Exception:
        raise ErrorEntrada("la expresión está incompleta o mal escrita.") from None

    if not isinstance(funcion, sp.Expr):
        raise ErrorEntrada("la expresión está incompleta (¿falta el paréntesis de una función?).")
    if funcion.has(sp.zoo, sp.nan, sp.oo):
        raise ErrorEntrada("la expresión contiene una división por cero.")
    return funcion


def interpretar_numero(texto):
    """Convierte un texto en un número.

    Acepta 0.5, 0,5, -3, 1/3, 1e-3 y también expresiones como pi/2 o sqrt(2).
    """
    texto = texto.strip().replace(",", ".").replace("−", "-")
    if not texto:
        raise ErrorEntrada("el campo está vacío.")

    # Decimales y fracciones se guardan exactos (0.5 -> 1/2).
    try:
        return sp.Rational(texto)
    except (TypeError, ValueError, ZeroDivisionError):
        pass

    # Si no es un número simple, puede ser una expresión como pi/2.
    valor = interpretar_funcion(texto)
    if valor.free_symbols:
        raise ErrorEntrada("debe ser un número, no puede contener x.")
    if not valor.is_Rational:
        valor = valor.evalf(PRECISION)
    if not (valor.is_real and valor.is_finite):
        raise ErrorEntrada("no es un número real.")
    return valor


def evaluar_funcion(funcion, valor):
    """Calcula f(valor) con alta precisión."""
    resultado = funcion.subs(X, valor)
    if not resultado.is_Rational:
        resultado = resultado.evalf(PRECISION)
    if not (resultado.is_real and resultado.is_finite):
        raise ErrorEntrada(
            f"La función no está definida en x = {float(valor):.10g} "
            "(por ejemplo, división por cero o logaritmo de un número no positivo)."
        )
    return resultado


def crear_funcion_numerica(funcion):
    """Devuelve una versión rápida de f para evaluar muchos puntos a la vez.

    Se usa en la gráfica y en el error máximo. Donde f no está definida
    el resultado es NaN ("no es un número").
    """
    funcion_rapida = sp.lambdify(X, funcion, "numpy")

    def evaluar(puntos):
        puntos = np.asarray(puntos, dtype=float)
        with np.errstate(all="ignore"):  # sin avisos por log(0), 1/0, etc.
            valores = np.asarray(funcion_rapida(puntos), dtype=float)
        # Una función constante devuelve un solo número: se repite para cada punto.
        valores = np.array(np.broadcast_to(valores, puntos.shape))
        valores[~np.isfinite(valores)] = np.nan
        return valores

    return evaluar
