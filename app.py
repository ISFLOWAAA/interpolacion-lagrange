"""Interfaz web (Streamlit) de la herramienta de interpolación de Lagrange.

Este archivo solo se ocupa de la pantalla: toda la matemática está en
modules/ y utils/.

Ejecutar con:  python -m streamlit run app.py
"""

import numpy as np
import plotly.graph_objects as go
import streamlit as st
import sympy as sp

from modules import errors, lagrange, validation
from modules.validation import ErrorValidacion
from utils import formato
from utils.functions import ExpresionInvalida, crear_funcion_numerica, interpretar_numero

MAXIMO_PUNTOS = 12
PUNTOS_GRAFICA = 600
SUBINDICES = str.maketrans("0123456789", "₀₁₂₃₄₅₆₇₈₉")

COLOR_FUNCION = "#60a5fa"
COLOR_POLINOMIO = "#fb923c"
COLOR_PUNTOS = "#c084fc"
COLOR_EVALUACION = "#4ade80"

ADVERTENCIA_EXTRAPOLACION = (
    "Advertencia: el punto seleccionado se encuentra fuera del intervalo definido por los "
    "puntos de interpolación. El resultado corresponde a una extrapolación y puede presentar "
    "un error elevado."
)

EJEMPLOS = {
    "cuadratica": {
        "funcion": "x^2", "xs": ["0", "1", "2"], "ys": ["0", "1", "4"],
        "auto_y": False, "x_eval": "1.5", "a": "0", "b": "2",
    },
    "seno": {
        "funcion": "sin(x)", "xs": ["0", "1", "2", "3"], "ys": ["", "", "", ""],
        "auto_y": True, "x_eval": "1.5", "a": "0", "b": "3",
    },
}

ESTILOS = """
<style>
.block-container {padding-top: 2.5rem; padding-bottom: 3rem; max-width: 780px;}
/* Controles grandes, fáciles de tocar en el celular */
.stButton button {min-height: 3rem; font-weight: 600;}
.stTextInput input, .stNumberInput input {min-height: 2.9rem; font-size: 1.05rem;}
/* Las fórmulas largas se desplazan horizontalmente */
.katex-display {overflow-x: auto; overflow-y: hidden; padding: 0.35rem 0;}
/* La tabla de puntos conserva sus tres columnas en pantallas pequeñas */
.st-key-tabla_puntos [data-testid="stHorizontalBlock"] {flex-wrap: nowrap !important; gap: 0.5rem;}
.st-key-tabla_puntos [data-testid="stColumn"] {min-width: 0 !important;}
</style>
"""


# ---------------------------------------------------------------- estado

def cargar_ejemplo(nombre):
    """Rellena el formulario con un ejemplo de prueba."""
    ejemplo = EJEMPLOS[nombre]
    estado = st.session_state
    estado["funcion"] = ejemplo["funcion"]
    estado["n_puntos"] = len(ejemplo["xs"])
    estado["auto_y"] = ejemplo["auto_y"]
    for i, (x, y) in enumerate(zip(ejemplo["xs"], ejemplo["ys"])):
        estado[f"x_{i}"] = x
        estado[f"y_{i}"] = y
    reiniciar_calculos({clave: ejemplo[clave] for clave in ("x_eval", "a", "b")})


def limpiar_formulario():
    """Deja todos los campos vacíos."""
    estado = st.session_state
    estado["funcion"] = ""
    estado["auto_y"] = False
    for i in range(MAXIMO_PUNTOS):
        estado[f"x_{i}"] = ""
        estado[f"y_{i}"] = ""
    reiniciar_calculos({})


def reiniciar_calculos(valores_iniciales):
    """Borra los resultados y fija los valores iniciales de las secciones de cálculo."""
    estado = st.session_state
    for clave in ("calculo", "x_eval", "x_directo", "a", "b"):
        estado.pop(clave, None)
    estado["iniciales"] = valores_iniciales


def comenzar():
    st.session_state["iniciado"] = True
    cargar_ejemplo("cuadratica")


def valor_inicial(clave, respaldo):
    """Asigna el valor inicial de un campo la primera vez que se muestra."""
    if clave not in st.session_state:
        st.session_state[clave] = st.session_state.get("iniciales", {}).get(clave, respaldo)


# ---------------------------------------------------------------- utilidades de pantalla

def mostrar_resultado(etiqueta, latex, explicacion=None):
    """Un resultado: título, valor en notación matemática y explicación breve."""
    st.markdown(f"**{etiqueta}**")
    st.latex(latex)
    if explicacion:
        st.caption(explicacion)


def tabla_markdown(xs, ys):
    filas = ["| Punto | x | f(x) |", "|:-:|--:|--:|"]
    for i, (x, y) in enumerate(zip(xs, ys)):
        filas.append(f"| {i + 1} | {formato.fmt_corto(x)} | {formato.fmt_corto(y)} |")
    return "\n".join(filas)


# ---------------------------------------------------------------- secciones

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


def seccion_datos():
    """Formulario de datos. Guarda el cálculo en st.session_state['calculo']."""
    st.subheader("1. Función")
    texto_funcion = st.text_input(
        "f(x) =", key="funcion", placeholder="Ejemplo: sin(x)   o   x^2 + 2x + 1",
        help="Opcional. Sin función no se puede calcular el valor real ni los errores.",
    )
    funcion, error_funcion = None, None
    try:
        funcion = validation.validar_funcion(texto_funcion)
    except ErrorValidacion as error:
        error_funcion = str(error)
        st.error(error_funcion)
    if funcion is not None:
        st.latex("f(x) = " + sp.latex(funcion))

    with st.expander("¿Cómo escribir la función?"):
        st.markdown(
            "| Para escribir | Usa |\n|---|---|\n"
            "| Potencia x² | `x^2` o `x**2` |\n"
            "| Producto 2x | `2x` o `2*x` |\n"
            "| Seno, coseno, tangente | `sin(x)` `cos(x)` `tan(x)` |\n"
            "| Exponencial eˣ | `exp(x)` o `e^x` |\n"
            "| Logaritmo natural | `ln(x)` o `log(x)` |\n"
            "| Logaritmo base 10 | `log10(x)` |\n"
            "| Raíz cuadrada | `sqrt(x)` |\n"
            "| Valor absoluto | `abs(x)` |\n"
            "| Constantes | `pi`, `e` |"
        )

    st.subheader("2. Número de puntos")
    cantidad = int(st.number_input(
        "Número de puntos (n + 1)", min_value=validation.MINIMO_PUNTOS,
        max_value=MAXIMO_PUNTOS, step=1, key="n_puntos",
    ))
    st.caption(f"Con {cantidad} puntos se obtiene un polinomio de grado n = {cantidad} − 1 = {cantidad - 1}.")

    st.subheader("3. Puntos")
    calcular_y = st.toggle(
        "Calcular f(x) automáticamente con la función", key="auto_y", disabled=funcion is None,
    ) and funcion is not None

    textos_x, textos_y = [], []
    proporciones = [1, 3, 3]
    with st.container(key="tabla_puntos"):
        encabezado = st.columns(proporciones)
        for columna, titulo in zip(encabezado, ("Punto", "x", "f(x)")):
            columna.markdown(f"**{titulo}**")
        for i in range(cantidad):
            subindice = str(i).translate(SUBINDICES)
            columnas = st.columns(proporciones, vertical_alignment="center")
            columnas[0].markdown(str(i + 1))
            texto_x = columnas[1].text_input(
                f"x{i}", key=f"x_{i}", placeholder=f"x{subindice}", label_visibility="collapsed",
            )
            textos_x.append(texto_x)
            if calcular_y:
                # Vista previa; el cálculo usa el valor con precisión completa.
                try:
                    vista = formato.fmt_corto(validation.evaluar_funcion_validada(funcion, interpretar_numero(texto_x)))
                except (ErrorValidacion, ExpresionInvalida):
                    vista = ""
                columnas[2].text_input(f"y{i}", value=vista, disabled=True, label_visibility="collapsed")
            else:
                textos_y.append(columnas[2].text_input(
                    f"y{i}", key=f"y_{i}", placeholder=f"y{subindice}", label_visibility="collapsed",
                ))

    firma = (texto_funcion, calcular_y, tuple(textos_x), tuple(textos_y))
    if st.button("Calcular interpolación", type="primary", width="stretch"):
        try:
            if error_funcion:
                raise ErrorValidacion(error_funcion)
            xs, ys = validation.validar_puntos(textos_x, None if calcular_y else textos_y, funcion)
            polinomio, bases = lagrange.construir_polinomio(xs, ys)
            st.session_state["calculo"] = {
                "xs": xs, "ys": ys, "funcion": funcion,
                "polinomio": polinomio, "bases": bases, "firma": firma,
            }
        except ErrorValidacion as error:
            st.session_state.pop("calculo", None)
            st.error(str(error))

    with st.expander("Ejemplos de prueba"):
        st.button("f(x) = x² con 3 puntos (error cero)", width="stretch",
                  on_click=cargar_ejemplo, args=("cuadratica",))
        st.button("f(x) = sin(x) con 4 puntos", width="stretch",
                  on_click=cargar_ejemplo, args=("seno",))
        st.button("Limpiar todos los campos", width="stretch", on_click=limpiar_formulario)

    return firma


def pestana_polinomio(calculo, decimales):
    xs, ys, polinomio, bases = calculo["xs"], calculo["ys"], calculo["polinomio"], calculo["bases"]
    n = len(xs) - 1
    latex_final = formato.latex_polinomio(polinomio, decimales)

    mostrar_resultado(
        "Polinomio interpolante", f"P_{{{n}}}(x) = {latex_final}",
        f"El polinomio se construyó con los {n + 1} puntos ingresados, por lo tanto es de grado n = {n} (a lo sumo).",
    )
    grado_real = lagrange.grado_polinomio(polinomio)
    if grado_real < n:
        st.info(
            f"El polinomio obtenido tiene grado {grado_real}, menor que {n}: los puntos "
            "ingresados ya pertenecen a un polinomio de grado menor."
        )

    with st.expander("Ver polinomios base Lᵢ(x)"):
        st.caption("Cada Lᵢ(x) vale 1 en xᵢ y 0 en los demás puntos.")
        for i, base in enumerate(bases):
            st.latex(
                f"L_{{{i}}}(x) = {formato.latex_base_producto(xs, i)} = "
                f"{formato.latex_polinomio(base, decimales)}"
            )

    with st.expander("Ver procedimiento"):
        st.markdown("**1.** Fórmula de Lagrange:")
        st.latex(r"P_n(x)=\sum_{i=0}^{n} y_i\,L_i(x), \qquad L_i(x)=\prod_{j\neq i}\frac{x-x_j}{x_i-x_j}")
        st.markdown("**2.** Se multiplica cada polinomio base por su valor yᵢ y se suman:")
        suma = " + ".join(f"({formato.latex_decimal(y, decimales)})\\,L_{{{i}}}(x)" for i, y in enumerate(ys))
        st.latex(f"P_{{{n}}}(x) = {suma}")
        st.markdown("**3.** Se desarrollan los productos y se agrupan los términos semejantes:")
        st.latex(f"P_{{{n}}}(x) = {latex_final}")


def pestana_directo(calculo, decimales):
    xs, ys = calculo["xs"], calculo["ys"]
    n = len(xs) - 1
    st.caption(
        "Calcula P(x*) sustituyendo x* directamente en la fórmula de Lagrange, "
        "sin desarrollar el polinomio."
    )
    valor_inicial("x_directo", formato.fmt_corto((xs[0] + xs[1]) / 2))
    texto = st.text_input("Punto a interpolar x*", key="x_directo")
    try:
        x_eval = validation.validar_numero(texto, "El punto a interpolar")
    except ErrorValidacion as error:
        st.error(str(error))
        return

    if validation.es_extrapolacion(xs, x_eval):
        st.warning(ADVERTENCIA_EXTRAPOLACION)
    valor, pasos = lagrange.interpolar_directo(xs, ys, x_eval)
    x_texto = formato.fmt_corto(x_eval)
    mostrar_resultado("Valor interpolado", f"P_{{{n}}}({x_texto}) = {formato.latex_decimal(valor, decimales)}")

    with st.expander("Ver procedimiento"):
        st.latex(
            rf"P_{{{n}}}({x_texto})=\sum_{{i=0}}^{{{n}}} y_i\prod_{{j\neq i}}\frac{{{x_texto}-x_j}}{{x_i-x_j}}"
        )
        st.dataframe(
            [
                {
                    "i": paso["i"],
                    "xᵢ": formato.fmt_corto(paso["x"]),
                    "yᵢ": formato.fmt_num(paso["y"], decimales),
                    "Lᵢ(x*)": formato.fmt_num(paso["L"], decimales),
                    "yᵢ · Lᵢ(x*)": formato.fmt_num(paso["termino"], decimales),
                }
                for paso in pasos
            ],
            hide_index=True, width="stretch",
        )
        st.markdown(f"La suma de la última columna es **{formato.fmt_num(valor, decimales)}**.")


def pestana_evaluacion(calculo, decimales, resumen):
    xs, ys, funcion = calculo["xs"], calculo["ys"], calculo["funcion"]
    n = len(xs) - 1
    valor_inicial("x_eval", formato.fmt_corto((xs[0] + xs[1]) / 2))
    texto = st.text_input("Punto a evaluar x", key="x_eval")
    try:
        x_eval = validation.validar_numero(texto, "El punto a evaluar")
    except ErrorValidacion as error:
        st.error(str(error))
        return

    if validation.es_extrapolacion(xs, x_eval):
        st.warning(ADVERTENCIA_EXTRAPOLACION)
    x_texto = formato.fmt_corto(x_eval)
    aproximado, _ = lagrange.interpolar_directo(xs, ys, x_eval)
    aproximado_latex = formato.latex_decimal(aproximado, decimales)
    resumen.update(x_eval=x_eval, aproximado=aproximado)

    if funcion is None:
        mostrar_resultado("Valor aproximado", f"P_{{{n}}}({x_texto}) = {aproximado_latex}")
        st.info("Ingresa la función f(x) en el paso 1 para comparar con el valor real y calcular los errores.")
        return
    try:
        real = validation.evaluar_funcion_validada(funcion, x_eval)
    except ErrorValidacion as error:
        mostrar_resultado("Valor aproximado", f"P_{{{n}}}({x_texto}) = {aproximado_latex}")
        st.error(str(error))
        return

    absoluto = errors.error_absoluto(real, aproximado)
    relativo = errors.error_relativo(real, aproximado)
    porcentual = errors.error_porcentual(real, aproximado)
    resumen.update(real=real, absoluto=absoluto, relativo=relativo, porcentual=porcentual)
    real_latex = formato.latex_decimal(real, decimales)
    absoluto_latex = formato.latex_decimal(absoluto, decimales)

    mostrar_resultado("Valor real", f"f({x_texto}) = {real_latex}")
    mostrar_resultado("Valor aproximado", f"P_{{{n}}}({x_texto}) = {aproximado_latex}")
    mostrar_resultado(
        "Error absoluto", f"E_a = {absoluto_latex}",
        "Diferencia entre el valor real de la función y el valor aproximado obtenido por interpolación.",
    )
    if relativo is None:
        st.markdown("**Error relativo**")
        st.info("No está definido porque f(x) = 0 en este punto (se evitó una división entre cero).")
    else:
        mostrar_resultado(
            "Error relativo", f"E_r = {formato.latex_decimal(relativo, decimales)}",
            "Error absoluto dividido entre el valor real: mide el error en proporción al tamaño del valor.",
        )
        mostrar_resultado("Error relativo porcentual", rf"E_r(\%) = {formato.latex_decimal(porcentual, decimales)}\,\%")

    with st.expander("Ver procedimiento"):
        st.latex(rf"E_a = |f(x)-P_{{{n}}}(x)| = |{real_latex} - ({aproximado_latex})| = {absoluto_latex}")
        if relativo is not None:
            st.latex(
                rf"E_r = \frac{{E_a}}{{|f(x)|}} = \frac{{{absoluto_latex}}}{{|{real_latex}|}} = "
                f"{formato.latex_decimal(relativo, decimales)}"
            )
            st.latex(rf"E_r(\%) = E_r \times 100 = {formato.latex_decimal(porcentual, decimales)}\,\%")


def pestana_error_maximo(calculo, decimales, resumen):
    xs, ys, funcion = calculo["xs"], calculo["ys"], calculo["funcion"]
    if funcion is None:
        st.info("Ingresa la función f(x) en el paso 1 para calcular el error máximo.")
        return

    valor_inicial("a", formato.fmt_corto(min(xs)))
    valor_inicial("b", formato.fmt_corto(max(xs)))
    columna_a, columna_b = st.columns(2)
    texto_a = columna_a.text_input("Extremo a", key="a")
    texto_b = columna_b.text_input("Extremo b", key="b")
    cantidad = int(st.number_input(
        "Cantidad de puntos de comparación", min_value=10, max_value=200000, value=2000, step=500,
        help="Mientras más puntos, mejor es la estimación del error máximo.",
    ))
    try:
        a, b = validation.validar_intervalo(texto_a, texto_b)
        resultado = errors.error_maximo(crear_funcion_numerica(funcion), xs, ys, a, b, cantidad)
    except (ErrorValidacion, ValueError) as error:
        st.error(str(error))
        return

    resumen.update(error_maximo=resultado["error"], x_maximo=resultado["x"], a=a, b=b)
    mostrar_resultado("Error máximo aproximado", rf"E_{{\max}} = {formato.latex_decimal(resultado['error'], decimales)}")
    mostrar_resultado(
        "Ocurre aproximadamente en", f"x = {formato.latex_decimal(resultado['x'], decimales)}",
        f"Se comparó |f(x) − P(x)| en {cantidad} puntos igualmente espaciados de "
        f"[{formato.fmt_corto(a)}, {formato.fmt_corto(b)}] y se tomó el mayor valor.",
    )
    if resultado["no_definidos"]:
        st.warning(f"La función no está definida en {resultado['no_definidos']} de los puntos; se omitieron.")
    if a < min(xs) or b > max(xs):
        st.warning("El intervalo incluye zonas fuera de los puntos de interpolación (extrapolación).")

    figura = go.Figure(go.Scatter(
        x=resultado["malla"], y=resultado["errores"], mode="lines",
        line=dict(color=COLOR_POLINOMIO, width=2), name="|f(x) − P(x)|",
    ))
    figura.add_trace(go.Scatter(
        x=[resultado["x"]], y=[resultado["error"]], mode="markers",
        marker=dict(color=COLOR_EVALUACION, size=11, symbol="diamond"), name="Error máximo",
    ))
    figura.update_layout(
        title="Error de interpolación |f(x) − P(x)|", xaxis_title="x", yaxis_title="Error",
        height=340, margin=dict(l=10, r=10, t=50, b=10),
        legend=dict(orientation="h", yanchor="top", y=-0.25),
    )
    st.plotly_chart(figura, width="stretch")


def pestana_grafica(calculo, resumen):
    xs, ys, funcion = calculo["xs"], calculo["ys"], calculo["funcion"]
    n = len(xs) - 1
    x_nodos = [float(x) for x in xs]
    y_nodos = [float(y) for y in ys]
    x_eval = resumen.get("x_eval")

    # Rango horizontal: los puntos, el punto evaluado y un pequeño margen.
    extremos = x_nodos + ([float(x_eval)] if x_eval is not None else [])
    margen = 0.1 * (max(extremos) - min(extremos))
    malla = np.linspace(min(extremos) - margen, max(extremos) + margen, PUNTOS_GRAFICA)
    valores_polinomio = lagrange.evaluar_en_malla(xs, ys, malla)

    figura = go.Figure()
    if funcion is not None:
        figura.add_trace(go.Scatter(
            x=malla, y=crear_funcion_numerica(funcion)(malla), mode="lines",
            line=dict(color=COLOR_FUNCION, width=3), name="Función f(x)",
        ))
    figura.add_trace(go.Scatter(
        x=malla, y=valores_polinomio, mode="lines",
        line=dict(color=COLOR_POLINOMIO, width=2, dash="dash"), name=f"Polinomio P{str(n).translate(SUBINDICES)}(x)",
    ))
    figura.add_trace(go.Scatter(
        x=x_nodos, y=y_nodos, mode="markers",
        marker=dict(color=COLOR_PUNTOS, size=11, line=dict(color="white", width=1.5)),
        name="Puntos de interpolación",
    ))
    if x_eval is not None:
        figura.add_trace(go.Scatter(
            x=[float(x_eval)], y=[float(resumen["aproximado"])], mode="markers",
            marker=dict(color=COLOR_EVALUACION, size=13, symbol="diamond", line=dict(color="white", width=1.5)),
            name="Punto evaluado",
        ))

    # Escala vertical basada en el polinomio, para que una asíntota de f no la deforme.
    minimo, maximo = float(valores_polinomio.min()), float(valores_polinomio.max())
    holgura = 0.15 * (maximo - minimo) or 1.0
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

    def numero(clave):
        return formato.latex_decimal(resumen[clave], decimales)

    st.markdown("**Datos ingresados**")
    st.markdown(tabla_markdown(xs, ys))
    st.markdown(f"**Grado del polinomio:** n = {n}")
    mostrar_resultado("Polinomio interpolante", f"P_{{{n}}}(x) = {formato.latex_polinomio(calculo['polinomio'], decimales)}")

    if "x_eval" not in resumen:
        st.info("Ingresa un punto válido en «Evaluación y errores» para completar el resumen.")
        return
    lineas = [
        rf"x &= {formato.fmt_corto(resumen['x_eval'])} && \text{{(punto evaluado)}}",
        rf"P_{{{n}}}(x) &= {numero('aproximado')} && \text{{(valor aproximado)}}",
    ]
    if "real" in resumen:
        lineas.insert(1, rf"f(x) &= {numero('real')} && \text{{(valor real)}}")
        lineas.append(rf"E_a &= {numero('absoluto')} && \text{{(error absoluto)}}")
        if resumen["relativo"] is None:
            lineas.append(r"E_r &\ \text{no definido} && (f(x)=0)")
        else:
            lineas.append(rf"E_r &= {numero('relativo')} && \text{{(error relativo)}}")
            lineas.append(rf"E_r(\%) &= {numero('porcentual')}\,\% && \text{{(error porcentual)}}")
    if "error_maximo" in resumen:
        intervalo = f"[{formato.fmt_corto(resumen['a'])},\\ {formato.fmt_corto(resumen['b'])}]"
        lineas.append(rf"E_{{\max}} &= {numero('error_maximo')} && \text{{en }} {intervalo}")
        lineas.append(rf"x_{{\max}} &\approx {numero('x_maximo')} && \text{{(donde ocurre)}}")
    st.markdown("**Evaluación y errores**")
    st.latex(r"\begin{aligned}" + r" \\ ".join(lineas) + r"\end{aligned}")
    if "real" not in resumen:
        st.caption("Sin función f(x) no se calculan el valor real ni los errores.")


# ---------------------------------------------------------------- programa principal

def main():
    st.set_page_config(page_title="Interpolación de Lagrange", page_icon="📈", layout="centered")
    st.markdown(ESTILOS, unsafe_allow_html=True)

    if not st.session_state.get("iniciado"):
        pantalla_inicio()
        return

    st.title("Interpolación de Lagrange")
    firma_actual = seccion_datos()

    calculo = st.session_state.get("calculo")
    if calculo is None:
        return

    st.divider()
    st.subheader("4. Cálculos y resultados")
    if calculo["firma"] != firma_actual:
        st.warning("Los datos cambiaron. Presiona «Calcular interpolación» para actualizar los resultados.")
    decimales = int(st.number_input("Decimales a mostrar", min_value=1, max_value=15, value=6, step=1))

    resumen = {}  # valores que cada pestaña aporta al resumen final y a la gráfica
    pestanas = st.tabs(["Polinomio", "Interpolar directo", "Evaluación y errores", "Error máximo", "Gráfica", "Resultados"])
    with pestanas[0]:
        pestana_polinomio(calculo, decimales)
    with pestanas[1]:
        pestana_directo(calculo, decimales)
    with pestanas[2]:
        pestana_evaluacion(calculo, decimales, resumen)
    with pestanas[3]:
        pestana_error_maximo(calculo, decimales, resumen)
    with pestanas[4]:
        pestana_grafica(calculo, resumen)
    with pestanas[5]:
        pestana_resumen(calculo, decimales, resumen)


main()
