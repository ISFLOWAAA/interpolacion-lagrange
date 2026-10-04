"""Interpretación segura de expresiones matemáticas escritas por el usuario.

No se usa eval(): el texto se convierte en un árbol sintáctico con el módulo
``ast`` y solo se aceptan números, la variable x, operaciones aritméticas y
las funciones de la lista FUNCIONES. Cualquier otra cosa se rechaza.
"""

import ast
import re

import numpy as np
import sympy as sp

# Variable simbólica única de toda la aplicación.
X = sp.Symbol("x")

# Dígitos con los que se hacen los cálculos que no son exactos.
PRECISION = 30

# Funciones y constantes que el usuario puede escribir.
FUNCIONES = {
    "sin": sp.sin, "sen": sp.sin, "cos": sp.cos, "tan": sp.tan,
    "asin": sp.asin, "acos": sp.acos, "atan": sp.atan,
    "sinh": sp.sinh, "cosh": sp.cosh, "tanh": sp.tanh,
    "exp": sp.exp, "log": sp.log, "ln": sp.log,
    "log10": lambda valor: sp.log(valor, 10),
    "sqrt": sp.sqrt, "abs": sp.Abs,
}
CONSTANTES = {"pi": sp.pi, "e": sp.E}

# Símbolos "bonitos" que se traducen a la sintaxis estándar.
_REEMPLAZOS = {
    "²": "**2", "³": "**3", "^": "**", "×": "*", "·": "*", "÷": "/",
    "−": "-", "π": "pi", "√": "sqrt",
}

_PATRON_TOKEN = re.compile(
    r"(?P<num>\d+\.?\d*|\.\d+)|(?P<nombre>[a-z_][a-z0-9_]*)|(?P<op>\*\*|[-+*/(),])"
)
_PATRON_DECIMAL = re.compile(r"[+-]?(\d+(\.\d+)?|\.\d+)(e[+-]?\d+)?", re.IGNORECASE)
_PREFIJO = re.compile(r"^\s*(f\s*\(\s*x\s*\)|y)\s*=")

_OPERADORES = {
    ast.Add: lambda a, b: a + b,
    ast.Sub: lambda a, b: a - b,
    ast.Mult: lambda a, b: a * b,
    ast.Div: lambda a, b: a / b,
}
_EXPONENTE_MAXIMO = 1000


class ExpresionInvalida(ValueError):
    """El texto no es una expresión matemática permitida."""


class FuncionNoDefinida(ValueError):
    """La función no tiene un valor real finito en el punto pedido."""


def _tokenizar(texto):
    """Divide el texto en números, nombres y operadores."""
    tokens = []
    posicion = 0
    while posicion < len(texto):
        if texto[posicion].isspace():
            posicion += 1
            continue
        coincidencia = _PATRON_TOKEN.match(texto, posicion)
        if not coincidencia:
            raise ExpresionInvalida(f"carácter no permitido: «{texto[posicion]}».")
        tokens.append((coincidencia.lastgroup, coincidencia.group()))
        posicion = coincidencia.end()
    return tokens


def _multiplicacion_implicita(tokens):
    """Inserta el * que se omite al escribir, por ejemplo 2x o 3(x+1)."""
    salida = []
    for tipo, valor in tokens:
        if salida:
            tipo_previo, valor_previo = salida[-1]
            termina_factor = (
                tipo_previo == "num"
                or valor_previo == ")"
                or (tipo_previo == "nombre" and valor_previo not in FUNCIONES)
            )
            empieza_factor = (
                tipo == "nombre"
                or valor == "("
                or (tipo == "num" and tipo_previo != "num")
            )
            if termina_factor and empieza_factor:
                salida.append(("op", "*"))
        salida.append((tipo, valor))
    return salida


def _convertir(nodo):
    """Convierte un nodo del árbol sintáctico en una expresión de SymPy."""
    if isinstance(nodo, ast.Constant) and type(nodo.value) in (int, float):
        # Los decimales se guardan como fracciones exactas (0.1 -> 1/10).
        return sp.Rational(str(nodo.value))
    if isinstance(nodo, ast.Name):
        if nodo.id == "x":
            return X
        if nodo.id in CONSTANTES:
            return CONSTANTES[nodo.id]
        if nodo.id in FUNCIONES:
            raise ExpresionInvalida(f"la función {nodo.id} debe llevar paréntesis, por ejemplo {nodo.id}(x).")
        raise ExpresionInvalida(f"nombre no reconocido: «{nodo.id}».")
    if isinstance(nodo, ast.UnaryOp) and isinstance(nodo.op, (ast.USub, ast.UAdd)):
        valor = _convertir(nodo.operand)
        return -valor if isinstance(nodo.op, ast.USub) else valor
    if isinstance(nodo, ast.BinOp):
        izquierda, derecha = _convertir(nodo.left), _convertir(nodo.right)
        if isinstance(nodo.op, ast.Pow):
            if derecha.is_number and abs(derecha) > _EXPONENTE_MAXIMO:
                raise ExpresionInvalida("el exponente es demasiado grande.")
            return sp.Pow(izquierda, derecha)
        if type(nodo.op) in _OPERADORES:
            return _OPERADORES[type(nodo.op)](izquierda, derecha)
    if isinstance(nodo, ast.Call) and isinstance(nodo.func, ast.Name) and not nodo.keywords:
        if nodo.func.id not in FUNCIONES:
            raise ExpresionInvalida(f"función no reconocida: «{nodo.func.id}».")
        argumentos = [_convertir(argumento) for argumento in nodo.args]
        try:
            return FUNCIONES[nodo.func.id](*argumentos)
        except TypeError:
            raise ExpresionInvalida(f"número incorrecto de argumentos en {nodo.func.id}().") from None
    raise ExpresionInvalida("la expresión contiene elementos no permitidos.")


def interpretar_funcion(texto):
    """Convierte un texto como 'x^2 + 2x + 1' en una expresión de SymPy."""
    texto = _PREFIJO.sub("", texto).strip().lower()
    if not texto:
        raise ExpresionInvalida("la expresión está vacía.")
    for original, reemplazo in _REEMPLAZOS.items():
        texto = texto.replace(original, reemplazo)

    tokens = _multiplicacion_implicita(_tokenizar(texto))
    try:
        arbol = ast.parse(" ".join(valor for _, valor in tokens), mode="eval")
    except SyntaxError:
        raise ExpresionInvalida("la expresión está incompleta o mal escrita.") from None

    expresion = sp.sympify(_convertir(arbol.body))
    if expresion.has(sp.zoo, sp.nan, sp.oo, -sp.oo):
        raise ExpresionInvalida("la expresión contiene una división por cero.")
    return expresion


def interpretar_numero(texto):
    """Convierte un texto en un número real.

    Acepta decimales con punto o coma (0.5 / 0,5), notación científica (1e-3)
    y expresiones constantes como 1/3, pi/2 o sqrt(2). Los valores racionales
    se conservan exactos; el resto se calcula con PRECISION dígitos.
    """
    texto = texto.strip().replace("−", "-")
    if not texto:
        raise ExpresionInvalida("el campo está vacío.")
    candidato = texto.replace(",", ".")
    if _PATRON_DECIMAL.fullmatch(candidato):
        return sp.Rational(candidato)

    expresion = interpretar_funcion(texto)
    if expresion.free_symbols:
        raise ExpresionInvalida("debe ser un número, no puede contener x.")
    valor = expresion if expresion.is_Rational else expresion.evalf(PRECISION)
    if not (valor.is_real and valor.is_finite):
        raise ExpresionInvalida("no es un número real.")
    return valor


def _es_cero_por_redondeo(expresion, valor, resultado):
    """True si el resultado es solo el redondeo de un punto irracional.

    Un punto como pi/2 se guarda con PRECISION dígitos, así que cos(pi/2) da
    ~1e-31 en lugar de 0. Se compara el resultado con la incertidumbre que
    produce ese redondeo: |f'(x)| * |x| * 10^-PRECISION.
    """
    try:
        pendiente = sp.diff(expresion, X).subs(X, valor).evalf(PRECISION)
        return bool(abs(resultado) <= abs(pendiente * valor) * sp.Float(10) ** (3 - PRECISION))
    except (TypeError, ValueError):
        return False


def evaluar_funcion(expresion, valor):
    """Evalúa f en un punto con alta precisión."""
    valor = sp.sympify(valor)
    resultado = expresion.subs(X, valor)
    if not resultado.is_Rational:
        resultado = resultado.evalf(PRECISION)
    if not (resultado.is_real and resultado.is_finite):
        raise FuncionNoDefinida("la función no está definida en ese punto.")
    if not valor.is_Rational and _es_cero_por_redondeo(expresion, valor, resultado):
        return sp.Integer(0)
    return resultado


def crear_funcion_numerica(expresion):
    """Devuelve una versión de f que evalúa arreglos de NumPy.

    Donde la función no está definida el resultado es NaN.
    """
    funcion = sp.lambdify(X, expresion, "numpy")

    def evaluar(valores):
        valores = np.asarray(valores, dtype=float)
        with np.errstate(all="ignore"):
            resultado = np.asarray(funcion(valores), dtype=float)
        resultado = np.array(np.broadcast_to(resultado, valores.shape))
        resultado[~np.isfinite(resultado)] = np.nan
        return resultado

    return evaluar
