"""Página web de la herramienta de interpolación de Lagrange (hecha con Streamlit).

Este archivo solo arma la pantalla. Los cálculos están en:
    modules/lagrange.py     polinomio e interpolación
    modules/errors.py       errores
    modules/validation.py   revisión de los datos
    utils/functions.py      lectura de la función que escribe el usuario
    utils/formato.py        presentación de números y polinomios

Para abrir la aplicación:  python -m streamlit run app.py

Cómo funciona Streamlit: cada vez que el usuario escribe algo o presiona un
botón, este archivo se ejecuta completo otra vez, de arriba hacia abajo.
Lo que debe recordarse entre una ejecución y otra se guarda en st.session_state.
"""

import numpy as np
import plotly.graph_objects as go
import streamlit as st
import sympy as sp

from modules import errors, lagrange, validation
from utils import formato
from utils.functions import ErrorEntrada, crear_funcion_numerica, evaluar_funcion, interpretar_numero

MAXIMO_PUNTOS = 12
PUNTOS_GRAFICA = 600

COLOR_FUNCION = "#60a5fa"
COLOR_POLINOMIO = "#fb923c"
COLOR_PUNTOS = "#c084fc"
COLOR_EVALUACION = "#4ade80"

ADVERTENCIA_EXTRAPOLACION = (
    "Advertencia: el punto seleccionado se encuentra fuera del intervalo definido por los "
    "puntos de interpolación. El resultado corresponde a una extrapolación y puede presentar "
    "un error elevado."
)

AYUDA_FUNCION = """
| Para escribir | Usa |
|---|---|
| Potencia x² | `x^2` o `x**2` |
| Producto 2x | `2x` o `2*x` |
| Seno, coseno, tangente | `sin(x)` `cos(x)` `tan(x)` |
| Exponencial eˣ | `exp(x)` o `e^x` |
| Logaritmo natural | `ln(x)` o `log(x)` |
| Logaritmo base 10 | `log10(x)` |
| Raíz cuadrada | `sqrt(x)` |
| Valor absoluto | `abs(x)` |
| Constantes | `pi`, `e` |
"""

# Ajustes de apariencia, pensados para el celular.
ESTILOS = """
<style>
.block-container {padding-top: 2.5rem; padding-bottom: 3rem; max-width: 780px;}
/* Botones y casillas grandes, fáciles de tocar */
.stButton button {min-height: 3rem; font-weight: 600;}
.stTextInput input, .stNumberInput input {min-height: 2.9rem; font-size: 1.05rem;}
/* Las fórmulas largas se pueden deslizar hacia los lados */
.katex-display {overflow-x: auto; overflow-y: hidden; padding: 0.35rem 0;}
/* La tabla de puntos mantiene sus tres columnas en pantallas pequeñas */
.st-key-tabla_puntos [data-testid="stHorizontalBlock"] {flex-wrap: nowrap !important; gap: 0.5rem;}
.st-key-tabla_puntos [data-testid="stColumn"] {min-width: 0 !important;}
</style>
"""


# ======================================================================
# Ejemplos y botones que rellenan el formulario
# ======================================================================

def rellenar_formulario(funcion, xs, ys, calcular_y):
    """Escribe datos en las casillas del formulario y borra los resultados anteriores."""
    st.session_state["funcion"] = funcion
    st.session_state["n_puntos"] = len(xs)
    st.session_state["auto_y"] = calcular_y
    for i in range(len(xs)):
        st.session_state[f"x_{i}"] = xs[i]
        st.session_state[f"y_{i}"] = ys[i]
    st.session_state.pop("calculo", None)


def ejemplo_cuadratica():
    rellenar_formulario("x^2", ["0", "1", "2"], ["0", "1", "4"], calcular_y=False)


def ejemplo_seno():
    rellenar_formulario("sin(x)", ["0", "1", "2", "3"], ["", "", "", ""], calcular_y=True)


def limpiar_formulario():
    rellenar_formulario("", ["", ""], ["", ""], calcular_y=False)


def comenzar():
    st.session_state["iniciado"] = True
    ejemplo_cuadratica()


# ======================================================================
# Ayudas para mostrar cosas en pantalla
# ======================================================================

def mostrar_resultado(titulo, formula, explicacion=None):
    """Muestra un resultado: título, valor en notación matemática y explicación breve."""
    st.markdown(f"**{titulo}**")
    st.latex(formula)
    if explicacion:
        st.caption(explicacion)


def pedir_punto(etiqueta, clave, xs):
    """Casilla para escribir un punto x. Devuelve el número, o None si está mal escrito."""
    punto_inicial = formato.fmt_corto((xs[0] + xs[1]) / 2)
    texto = st.text_input(etiqueta, value=punto_inicial, key=clave)
    try:
        punto = validation.validar_numero(texto, "El punto")
    except ErrorEntrada as error:
        st.error(str(error))
        return None
    if validation.es_extrapolacion(xs, punto):
        st.warning(ADVERTENCIA_EXTRAPOLACION)
    return punto


# ======================================================================
# Pantalla de inicio
# ======================================================================

def pantalla_inicio():
    st.title("Interpolación de Lagrange")
    st.write(
        "Herramienta de interpolación polinómica de Lagrange. Ingresa **n + 1 puntos** y "
        "obtén el polinomio interpolante de grado **n**, sus valores, los errores de "
        "aproximación y la gráfica."
    )
    st.latex(r"P_n(x)=\sum_{i=0}^{n} y_i\,L_i(x) \qquad L_i(x)=\prod_{j\neq i}\frac{x-x_j}{x_i-x_j}")
    st.button("Comenzar", type="primary", width="stretch", on_click=comenzar)
    st.caption("Se abrirá con un ejemplo cargado: f(x) = x² con los puntos (0,0), (1,1) y (2,4).")


# ======================================================================
# Formulario de datos (pasos 1, 2 y 3)
# ======================================================================

def paso_funcion():
    """Paso 1: la función. Devuelve el texto escrito, la función y si es válida."""
    st.subheader("1. Función")
    texto = st.text_input(
        "f(x) =", key="funcion", placeholder="Ejemplo: sin(x)   o   x^2 + 2x + 1",
        help="Opcional. Sin función no se puede calcular el valor real ni los errores.",
    )

    funcion = None
    es_valida = True
    try:
        funcion = validation.validar_funcion(texto)  # None si la casilla está vacía
    except ErrorEntrada as error:
        st.error(str(error))
        es_valida = False

    if funcion is not None:
        st.latex("f(x) = " + sp.latex(funcion))
    with st.expander("¿Cómo escribir la función?"):
        st.markdown(AYUDA_FUNCION)
    return texto, funcion, es_valida


def paso_puntos(funcion):
    """Pasos 2 y 3: número de puntos y tabla. Devuelve los textos de x y de y.

    Si los valores de y se calculan con la función, devuelve None en lugar de los textos de y.
    """
    st.subheader("2. Número de puntos")
    cantidad = int(st.number_input(
        "Número de puntos (n + 1)", min_value=validation.MINIMO_PUNTOS,
        max_value=MAXIMO_PUNTOS, step=1, key="n_puntos",
    ))
    st.caption(f"Con {cantidad} puntos se obtiene un polinomio de grado n = {cantidad} − 1 = {cantidad - 1}.")

    st.subheader("3. Puntos")
    interruptor = st.toggle(
        "Calcular f(x) automáticamente con la función", key="auto_y", disabled=funcion is None,
    )
    calcular_y = interruptor and funcion is not None

    textos_x = []
    textos_y = []
    anchos = [1, 3, 3]  # ancho relativo de las columnas: Punto, x, f(x)
    with st.container(key="tabla_puntos"):
        encabezado = st.columns(anchos)
        encabezado[0].markdown("**Punto**")
        encabezado[1].markdown("**x**")
        encabezado[2].markdown("**f(x)**")

        for i in range(cantidad):
            fila = st.columns(anchos, vertical_alignment="center")
            fila[0].markdown(str(i + 1))
            texto_x = fila[1].text_input(f"x{i}", key=f"x_{i}", placeholder=f"x{i}", label_visibility="collapsed")
            textos_x.append(texto_x)

            if calcular_y:
                # Casilla bloqueada que muestra el valor de f(x) mientras se escribe x.
                try:
                    vista = formato.fmt_corto(evaluar_funcion(funcion, interpretar_numero(texto_x)))
                except ErrorEntrada:
                    vista = ""
                fila[2].text_input(f"y{i}", value=vista, disabled=True, label_visibility="collapsed")
            else:
                texto_y = fila[2].text_input(f"y{i}", key=f"y_{i}", placeholder=f"y{i}", label_visibility="collapsed")
                textos_y.append(texto_y)

    if calcular_y:
        return textos_x, None
    return textos_x, textos_y


def calcular(funcion, funcion_valida, textos_x, textos_y, datos):
    """Revisa los datos, construye el polinomio y lo guarda para mostrar los resultados."""
    st.session_state.pop("calculo", None)
    if not funcion_valida:
        st.error("Corrige la función antes de calcular.")
        return
    try:
        xs, ys = validation.validar_puntos(textos_x, textos_y, funcion)
    except ErrorEntrada as error:
        st.error(str(error))
        return

    polinomio, bases = lagrange.construir_polinomio(xs, ys)
    st.session_state["calculo"] = {
        "xs": xs, "ys": ys, "funcion": funcion,
        "polinomio": polinomio, "bases": bases,
        "datos": datos,  # para avisar si el usuario cambia algo después de calcular
    }


def botones_de_ejemplo():
    with st.expander("Ejemplos de prueba"):
        st.button("f(x) = x² con 3 puntos (error cero)", width="stretch", on_click=ejemplo_cuadratica)
        st.button("f(x) = sin(x) con 4 puntos", width="stretch", on_click=ejemplo_seno)
        st.button("Limpiar todos los campos", width="stretch", on_click=limpiar_formulario)


# ======================================================================
# Pestañas de resultados
# ======================================================================

def pestana_polinomio(calculo, decimales):
    xs, ys = calculo["xs"], calculo["ys"]
    polinomio, bases = calculo["polinomio"], calculo["bases"]
    n = len(xs) - 1
    polinomio_latex = formato.latex_polinomio(polinomio, decimales)

    mostrar_resultado(
        "Polinomio interpolante", f"P_{{{n}}}(x) = {polinomio_latex}",
        f"El polinomio se construyó con los {n + 1} puntos ingresados, por lo tanto es de grado n = {n} (a lo sumo).",
    )
    grado = lagrange.grado_polinomio(polinomio)
    if grado < n:
        st.info(
            f"El polinomio obtenido tiene grado {grado}, menor que {n}: los puntos "
            "ingresados ya pertenecen a un polinomio de grado menor."
        )

    with st.expander("Ver polinomios base Lᵢ(x)"):
        st.caption("Cada Lᵢ(x) vale 1 en xᵢ y 0 en los demás puntos.")
        for i, base in enumerate(bases):
            como_producto = formato.latex_base_producto(xs, i)
            desarrollado = formato.latex_polinomio(base, decimales)
            st.latex(f"L_{{{i}}}(x) = {como_producto} = {desarrollado}")

    with st.expander("Ver procedimiento"):
        st.markdown("**1.** Fórmula de Lagrange:")
        st.latex(r"P_n(x)=\sum_{i=0}^{n} y_i\,L_i(x), \qquad L_i(x)=\prod_{j\neq i}\frac{x-x_j}{x_i-x_j}")
        st.markdown("**2.** Se multiplica cada polinomio base por su valor yᵢ y se suman:")
        sumandos = [f"({formato.latex_decimal(y, decimales)})\\,L_{{{i}}}(x)" for i, y in enumerate(ys)]
        st.latex(f"P_{{{n}}}(x) = " + " + ".join(sumandos))
        st.markdown("**3.** Se desarrollan los productos y se agrupan los términos semejantes:")
        st.latex(f"P_{{{n}}}(x) = {polinomio_latex}")


def pestana_directo(calculo, decimales):
    xs, ys = calculo["xs"], calculo["ys"]
    n = len(xs) - 1
    st.caption("Calcula P(x*) sustituyendo x* directamente en la fórmula de Lagrange, sin desarrollar el polinomio.")

    x = pedir_punto("Punto a interpolar x*", "x_directo", xs)
    if x is None:
        return
    valor, pasos = lagrange.interpolar_directo(xs, ys, x)
    x_texto = formato.fmt_corto(x)
    mostrar_resultado("Valor interpolado", f"P_{{{n}}}({x_texto}) = {formato.latex_decimal(valor, decimales)}")

    with st.expander("Ver procedimiento"):
        st.latex(rf"P_{{{n}}}({x_texto})=\sum_{{i=0}}^{{{n}}} y_i\prod_{{j\neq i}}\frac{{{x_texto}-x_j}}{{x_i-x_j}}")
        tabla = []
        for paso in pasos:
            tabla.append({
                "i": paso["i"],
                "xᵢ": formato.fmt_corto(paso["x"]),
                "yᵢ": formato.fmt_num(paso["y"], decimales),
                "Lᵢ(x*)": formato.fmt_num(paso["L"], decimales),
                "yᵢ · Lᵢ(x*)": formato.fmt_num(paso["termino"], decimales),
            })
        st.dataframe(tabla, hide_index=True, width="stretch")
        st.markdown(f"La suma de la última columna es **{formato.fmt_num(valor, decimales)}**.")


def pestana_evaluacion(calculo, decimales, resumen):
    """Valor real, valor aproximado y errores en un punto.

    Devuelve el punto evaluado como (x, P(x)) para dibujarlo en la gráfica,
    o None si el punto está mal escrito.
    """
    xs, ys, funcion = calculo["xs"], calculo["ys"], calculo["funcion"]
    n = len(xs) - 1

    x = pedir_punto("Punto a evaluar x", "x_eval", xs)
    if x is None:
        return None
    x_texto = formato.fmt_corto(x)
    aproximado, _ = lagrange.interpolar_directo(xs, ys, x)
    aproximado_latex = formato.latex_decimal(aproximado, decimales)
    resumen.append(("Punto evaluado", f"x = {x_texto}"))
    resumen.append(("Valor aproximado P(x)", formato.fmt_num(aproximado, decimales)))

    # El valor real solo se puede calcular si hay función y está definida en x.
    real = None
    if funcion is None:
        st.info("Ingresa la función f(x) en el paso 1 para comparar con el valor real y calcular los errores.")
    else:
        try:
            real = evaluar_funcion(funcion, x)
        except ErrorEntrada as error:
            st.error(str(error))
    if real is None:
        mostrar_resultado("Valor aproximado", f"P_{{{n}}}({x_texto}) = {aproximado_latex}")
        return x, aproximado

    absoluto = errors.error_absoluto(real, aproximado)
    relativo = errors.error_relativo(real, aproximado)
    porcentual = errors.error_porcentual(real, aproximado)
    real_latex = formato.latex_decimal(real, decimales)
    absoluto_latex = formato.latex_decimal(absoluto, decimales)

    mostrar_resultado("Valor real", f"f({x_texto}) = {real_latex}")
    mostrar_resultado("Valor aproximado", f"P_{{{n}}}({x_texto}) = {aproximado_latex}")
    mostrar_resultado(
        "Error absoluto", f"E_a = {absoluto_latex}",
        "Diferencia entre el valor real de la función y el valor aproximado obtenido por interpolación.",
    )
    resumen.append(("Valor real f(x)", formato.fmt_num(real, decimales)))
    resumen.append(("Error absoluto", formato.fmt_num(absoluto, decimales)))

    if relativo is None:
        st.markdown("**Error relativo**")
        st.info("No está definido porque f(x) = 0 en este punto (se evitó una división entre cero).")
        resumen.append(("Error relativo", "no definido, f(x) = 0"))
        return x, aproximado

    relativo_latex = formato.latex_decimal(relativo, decimales)
    porcentual_latex = formato.latex_decimal(porcentual, decimales)
    mostrar_resultado(
        "Error relativo", f"E_r = {relativo_latex}",
        "Error absoluto dividido entre el valor real: mide el error en proporción al tamaño del valor.",
    )
    mostrar_resultado("Error relativo porcentual", rf"E_r(\%) = {porcentual_latex}\,\%")
    resumen.append(("Error relativo", formato.fmt_num(relativo, decimales)))
    resumen.append(("Error relativo porcentual", formato.fmt_num(porcentual, decimales) + " %"))

    with st.expander("Ver procedimiento"):
        st.latex(rf"E_a = |f(x)-P_{{{n}}}(x)| = |{real_latex} - ({aproximado_latex})| = {absoluto_latex}")
        st.latex(rf"E_r = \frac{{E_a}}{{|f(x)|}} = \frac{{{absoluto_latex}}}{{|{real_latex}|}} = {relativo_latex}")
        st.latex(rf"E_r(\%) = E_r \times 100 = {porcentual_latex}\,\%")
    return x, aproximado


def pestana_error_maximo(calculo, decimales, resumen):
    xs, ys, funcion = calculo["xs"], calculo["ys"], calculo["funcion"]
    if funcion is None:
        st.info("Ingresa la función f(x) en el paso 1 para calcular el error máximo.")
        return

    columna_a, columna_b = st.columns(2)
    texto_a = columna_a.text_input("Extremo a", value=formato.fmt_corto(min(xs)), key="a")
    texto_b = columna_b.text_input("Extremo b", value=formato.fmt_corto(max(xs)), key="b")
    cantidad = int(st.number_input(
        "Cantidad de puntos de comparación", min_value=10, max_value=200000, value=2000, step=500,
        help="Mientras más puntos, mejor es la estimación del error máximo.",
    ))
    try:
        a, b = validation.validar_intervalo(texto_a, texto_b)
        resultado = errors.error_maximo(crear_funcion_numerica(funcion), xs, ys, a, b, cantidad)
    except ValueError as error:  # ErrorEntrada también es un ValueError
        st.error(str(error))
        return

    intervalo = f"[{formato.fmt_corto(a)}, {formato.fmt_corto(b)}]"
    mostrar_resultado("Error máximo aproximado", rf"E_{{\max}} = {formato.latex_decimal(resultado['error'], decimales)}")
    mostrar_resultado(
        "Ocurre aproximadamente en", f"x = {formato.latex_decimal(resultado['x'], decimales)}",
        f"Se comparó |f(x) − P(x)| en {cantidad} puntos igualmente espaciados de {intervalo} y se tomó el mayor valor.",
    )
    resumen.append((f"Error máximo en {intervalo}", formato.fmt_num(resultado["error"], decimales)))
    resumen.append(("Ocurre aproximadamente en", "x = " + formato.fmt_num(resultado["x"], decimales)))

    if resultado["no_definidos"] > 0:
        st.warning(f"La función no está definida en {resultado['no_definidos']} de los puntos; se omitieron.")
    if a < min(xs) or b > max(xs):
        st.warning("El intervalo incluye zonas fuera de los puntos de interpolación (extrapolación).")

    # Gráfica del error a lo largo del intervalo, con el máximo marcado.
    figura = go.Figure()
    figura.add_trace(go.Scatter(
        x=resultado["malla"], y=resultado["errores"], mode="lines", name="|f(x) − P(x)|",
        line=dict(color=COLOR_POLINOMIO, width=2),
    ))
    figura.add_trace(go.Scatter(
        x=[resultado["x"]], y=[resultado["error"]], mode="markers", name="Error máximo",
        marker=dict(color=COLOR_EVALUACION, size=11, symbol="diamond"),
    ))
    figura.update_layout(
        title="Error de interpolación |f(x) − P(x)|", xaxis_title="x", yaxis_title="Error",
        height=340, margin=dict(l=10, r=10, t=50, b=10),
        legend=dict(orientation="h", yanchor="top", y=-0.25),
    )
    st.plotly_chart(figura, width="stretch")


def pestana_grafica(calculo, punto_evaluado):
    xs, ys, funcion = calculo["xs"], calculo["ys"], calculo["funcion"]
    n = len(xs) - 1
    x_puntos = [float(x) for x in xs]
    y_puntos = [float(y) for y in ys]

    # Rango horizontal: de un extremo al otro de los puntos, con un pequeño margen.
    limites = list(x_puntos)
    if punto_evaluado is not None:
        limites.append(float(punto_evaluado[0]))
    margen = 0.1 * (max(limites) - min(limites))
    malla = np.linspace(min(limites) - margen, max(limites) + margen, PUNTOS_GRAFICA)
    valores_polinomio = lagrange.evaluar_en_malla(xs, ys, malla)

    figura = go.Figure()
    if funcion is not None:
        figura.add_trace(go.Scatter(
            x=malla, y=crear_funcion_numerica(funcion)(malla), mode="lines", name="Función f(x)",
            line=dict(color=COLOR_FUNCION, width=3),
        ))
    figura.add_trace(go.Scatter(
        x=malla, y=valores_polinomio, mode="lines", name=f"Polinomio P{n}(x)",
        line=dict(color=COLOR_POLINOMIO, width=2, dash="dash"),
    ))
    figura.add_trace(go.Scatter(
        x=x_puntos, y=y_puntos, mode="markers", name="Puntos de interpolación",
        marker=dict(color=COLOR_PUNTOS, size=11, line=dict(color="white", width=1.5)),
    ))
    if punto_evaluado is not None:
        figura.add_trace(go.Scatter(
            x=[float(punto_evaluado[0])], y=[float(punto_evaluado[1])], mode="markers", name="Punto evaluado",
            marker=dict(color=COLOR_EVALUACION, size=13, symbol="diamond", line=dict(color="white", width=1.5)),
        ))

    # La escala vertical se ajusta al polinomio, para que una función que se
    # va a infinito (como 1/x cerca de 0) no aplaste el resto de la gráfica.
    minimo = float(valores_polinomio.min())
    maximo = float(valores_polinomio.max())
    holgura = 0.15 * (maximo - minimo)
    if holgura == 0:
        holgura = 1.0
    figura.update_layout(
        title="Función f(x) y polinomio interpolante", xaxis_title="x", yaxis_title="y",
        yaxis_range=[minimo - holgura, maximo + holgura],
        height=460, margin=dict(l=10, r=10, t=50, b=10),
        legend=dict(orientation="h", yanchor="top", y=-0.2),
    )
    st.plotly_chart(figura, width="stretch")
    st.caption("Mientras más cerca esté la línea punteada de la línea continua, mejor es la aproximación.")


def pestana_resumen(calculo, decimales, resumen):
    xs, ys = calculo["xs"], calculo["ys"]
    n = len(xs) - 1

    st.markdown("**Datos ingresados**")
    tabla = "| Punto | x | f(x) |\n|:-:|--:|--:|\n"
    for i in range(len(xs)):
        tabla += f"| {i + 1} | {formato.fmt_corto(xs[i])} | {formato.fmt_corto(ys[i])} |\n"
    st.markdown(tabla)

    st.markdown(f"**Grado del polinomio:** n = {n}")
    mostrar_resultado("Polinomio interpolante", f"P_{{{n}}}(x) = {formato.latex_polinomio(calculo['polinomio'], decimales)}")

    # Las otras pestañas fueron agregando sus resultados a la lista `resumen`.
    st.markdown("**Evaluación y errores**")
    if not resumen:
        st.info("Ingresa un punto válido en «Evaluación y errores» para completar el resumen.")
        return
    tabla = "| Resultado | Valor |\n|---|--:|\n"
    for nombre, valor in resumen:
        tabla += f"| {nombre} | {valor} |\n"
    st.markdown(tabla)
    if calculo["funcion"] is None:
        st.caption("Sin función f(x) no se calculan el valor real ni los errores.")


# ======================================================================
# Programa principal
# ======================================================================

def main():
    st.set_page_config(page_title="Interpolación de Lagrange", page_icon="📈", layout="centered")
    st.markdown(ESTILOS, unsafe_allow_html=True)

    if not st.session_state.get("iniciado"):
        pantalla_inicio()
        return

    # --- Datos ---
    st.title("Interpolación de Lagrange")
    texto_funcion, funcion, funcion_valida = paso_funcion()
    textos_x, textos_y = paso_puntos(funcion)
    datos = (texto_funcion, textos_x, textos_y)

    if st.button("Calcular interpolación", type="primary", width="stretch"):
        calcular(funcion, funcion_valida, textos_x, textos_y, datos)
    botones_de_ejemplo()

    # --- Resultados (solo después de calcular) ---
    calculo = st.session_state.get("calculo")
    if calculo is None:
        return

    st.divider()
    st.subheader("4. Cálculos y resultados")
    if calculo["datos"] != datos:
        st.warning("Los datos cambiaron. Presiona «Calcular interpolación» para actualizar los resultados.")
    decimales = int(st.number_input("Decimales a mostrar", min_value=1, max_value=15, value=6, step=1))

    resumen = []  # filas (nombre, valor) que se muestran en la pestaña «Resultados»
    pestanas = st.tabs(["Polinomio", "Interpolar directo", "Evaluación y errores", "Error máximo", "Gráfica", "Resultados"])
    with pestanas[0]:
        pestana_polinomio(calculo, decimales)
    with pestanas[1]:
        pestana_directo(calculo, decimales)
    with pestanas[2]:
        punto_evaluado = pestana_evaluacion(calculo, decimales, resumen)
    with pestanas[3]:
        pestana_error_maximo(calculo, decimales, resumen)
    with pestanas[4]:
        pestana_grafica(calculo, punto_evaluado)
    with pestanas[5]:
        pestana_resumen(calculo, decimales, resumen)


main()
