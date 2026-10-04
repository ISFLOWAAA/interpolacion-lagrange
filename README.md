# Interpolación de Lagrange — herramienta web educativa

Aplicación web en Python para construir y estudiar el polinomio interpolante de
Lagrange: ingresar n + 1 puntos, obtener el polinomio de grado n, ver los
polinomios base, interpolar un punto, comparar con la función real, calcular
errores y ver la gráfica. Todo se usa desde el navegador, sin escribir código.

**Aplicación en línea:** <https://interpolador-lagrange.streamlit.app/>
(funciona en celular, tablet y computador, sin instalar nada)

**Código fuente:** <https://github.com/ISFLOWAAA/interpolacion-lagrange>

## Qué problema resuelve

En métodos numéricos es frecuente conocer una función solo en algunos puntos
(una tabla de datos) y necesitar su valor en un punto intermedio. La
interpolación de Lagrange construye un polinomio que pasa exactamente por esos
puntos y permite estimar el valor buscado. Hacerlo a mano es largo y propenso a
errores; esta herramienta lo calcula, muestra el procedimiento paso a paso y
mide qué tan buena es la aproximación frente a la función real.

## Tecnologías utilizadas

| Tecnología | Uso |
|---|---|
| Python 3 | Lenguaje del proyecto |
| Streamlit | Interfaz web adaptable a celulares |
| SymPy | Construcción exacta del polinomio y manejo de funciones |
| NumPy | Evaluación rápida en muchos puntos (error máximo y gráficas) |
| Plotly | Gráficas interactivas |

## Despliegue en internet

La aplicación se publica gratis en **Streamlit Community Cloud**, que instala
automáticamente lo indicado en `requirements.txt`:

1. Subir esta carpeta a un repositorio de GitHub.
2. Entrar a <https://share.streamlit.io> e iniciar sesión con la cuenta de GitHub.
3. Elegir **Create app → Deploy a public app from GitHub**.
4. Seleccionar el repositorio, la rama `main` y `app.py` como archivo principal.
5. En *App URL* escribir el nombre deseado y presionar **Deploy**.

En unos minutos queda disponible un enlace `https://<nombre>.streamlit.app` que
funciona en celular, tablet y computador sin instalar nada. Cada vez que se
sube un cambio a GitHub, la aplicación se actualiza sola.

## 1. Instalación

Se necesita Python 3.10 o superior. Desde la carpeta del proyecto:

```
python -m pip install -r requirements.txt
```

## 2. Ejecución

```
python -m streamlit run app.py
```

En Windows también basta con hacer doble clic en `ejecutar.bat`.

Se abrirá el navegador en `http://localhost:8501`. La primera vez Streamlit puede
pedir un correo en la consola: se puede dejar vacío y presionar Enter.

**Desde el celular:** con el computador y el celular en la misma red Wi-Fi, abrir
en el celular la dirección *Network URL* que aparece en la consola
(por ejemplo `http://192.168.1.20:8501`).

## 3. Estructura del proyecto

```
LAGRANGE/
├── app.py                 Interfaz web (Streamlit). No contiene matemática.
├── requirements.txt       Dependencias.
├── ejecutar.bat           Acceso directo para Windows.
├── modules/
│   ├── lagrange.py        Polinomios base, polinomio interpolante, interpolación directa.
│   ├── errors.py          Error absoluto, relativo, porcentual y máximo.
│   └── validation.py      Validación de los datos y mensajes de error.
├── utils/
│   ├── functions.py       Intérprete seguro de funciones y números (sin eval).
│   └── formato.py         Presentación de números y polinomios en LaTeX.
└── tests/
    └── test_basico.py     Pruebas de la lógica matemática.
```

**Arquitectura elegida.** Se usó Streamlit en lugar de Flask porque genera una
interfaz web adaptable a celulares solo con Python, sin HTML ni JavaScript. La
lógica matemática está separada de la interfaz: `modules/` y `utils/` no importan
Streamlit, así que se pueden probar o reutilizar por separado.

## 4. Fundamento matemático

Dados n + 1 puntos (x₀, y₀), …, (xₙ, yₙ) con valores de x distintos, existe un
único polinomio de grado a lo sumo n que pasa por todos ellos:

$$P_n(x)=\sum_{i=0}^{n}y_i\,L_i(x),\qquad L_i(x)=\prod_{\substack{j=0\\ j\neq i}}^{n}\frac{x-x_j}{x_i-x_j}$$

Cada polinomio base Lᵢ vale 1 en xᵢ y 0 en los demás puntos; por eso
Pₙ(xᵢ) = yᵢ.

**Interpolación directa.** Para obtener Pₙ(x\*) no hace falta desarrollar el
polinomio: se sustituye x\* en la fórmula y cada Lᵢ(x\*) se convierte en un número.

$$P_n(x^*)=\sum_{i=0}^{n}y_i\prod_{j\neq i}\frac{x^*-x_j}{x_i-x_j}$$

**Errores.**

| Error | Fórmula |
|---|---|
| Absoluto | Eₐ = \|f(x) − Pₙ(x)\| |
| Relativo | Eᵣ = \|f(x) − Pₙ(x)\| / \|f(x)\| (no definido si f(x) = 0) |
| Relativo porcentual | Eᵣ × 100 |
| Máximo en [a, b] | E_max = máx \|f(x) − Pₙ(x)\|, estimado en N puntos equiespaciados (N configurable, 2000 por defecto) |

El error máximo es una **estimación**: se toma el mayor error entre los N puntos
evaluados, por lo que el máximo verdadero puede ser ligeramente mayor.

**Precisión.** Los datos decimales o fraccionarios (0.5, 1/3) se guardan como
fracciones exactas, así que el polinomio se construye sin error de redondeo.
Los valores irracionales (por ejemplo sin(1)) se calculan con 30 dígitos. Las
gráficas y el error máximo usan precisión doble de NumPy. La cantidad de
decimales mostrados es configurable (1 a 15).

## 5. Ejemplo de uso

1. Presionar **Comenzar**. Se carga el ejemplo f(x) = x² con (0,0), (1,1), (2,4).
2. Presionar **Calcular interpolación**.
3. Pestaña **Polinomio**: se obtiene P₂(x) = x². En «Ver polinomios base» aparecen
   L₀ = ½x² − 3⁄2x + 1, L₁ = −x² + 2x, L₂ = ½x² − ½x.
4. Pestaña **Evaluación y errores** con x = 1.5: f(1.5) = 2.25, P₂(1.5) = 2.25,
   Eₐ = 0, porque el polinomio coincide con la función.
5. Pestaña **Error máximo** en [0, 2]: E_max ≈ 4 × 10⁻¹⁶, es decir, cero dentro
   de la precisión numérica del computador.

Para ver errores distintos de cero, abrir «Ejemplos de prueba» y cargar
**f(x) = sin(x) con 4 puntos**: en x = 1.5 se obtiene P₃ ≈ 0.975987 frente a
sin(1.5) ≈ 0.997495 (Eₐ ≈ 0.021508, Eᵣ ≈ 2.16 %), y el error máximo en [0, 3]
es ≈ 0.037226 cerca de x ≈ 2.61.

## 6. Cómo escribir la función

| Para escribir | Usar |
|---|---|
| Potencia | `x^2` o `x**2` |
| Producto | `2x` o `2*x` |
| Trigonométricas | `sin(x)`, `cos(x)`, `tan(x)`, `asin(x)`, `acos(x)`, `atan(x)` |
| Exponencial | `exp(x)` o `e^x` |
| Logaritmos | `ln(x)` o `log(x)` (natural), `log10(x)` |
| Raíz y valor absoluto | `sqrt(x)`, `abs(x)` |
| Constantes | `pi`, `e` |

Los campos numéricos aceptan `0.5`, `0,5`, `1/3`, `pi/2`, `sqrt(2)` o `1e-3`.

**Seguridad.** No se usa `eval()`. El texto se analiza con el módulo `ast` y solo
se aceptan números, la variable x, las operaciones + − × ÷ ^ y las funciones de
la tabla anterior; cualquier otra cosa se rechaza con un mensaje de error.

## 7. Validaciones implementadas

- Campos vacíos y valores no numéricos (indicando el punto afectado).
- Valores de x repetidos.
- Menos de dos puntos.
- Función mal escrita, con nombres o caracteres no permitidos.
- División por cero en la expresión.
- Función no definida en un punto (por ejemplo ln(0) o sqrt(−1)).
- Intervalo inválido (a ≥ b) o función no definida en todo el intervalo.
- f(x) = 0 al calcular el error relativo (se informa en vez de dividir).
- Extrapolación: advertencia cuando el punto está fuera del rango de los datos.
- Aviso si los datos cambian después de calcular.

## 8. Explicación de cada módulo

**`utils/functions.py`** — `interpretar_funcion` convierte el texto en una
expresión de SymPy; `interpretar_numero` hace lo mismo para los campos numéricos;
`evaluar_funcion` evalúa f en un punto con alta precisión;
`crear_funcion_numerica` produce una versión rápida para evaluar miles de puntos.

**`modules/lagrange.py`** — `polinomio_base` calcula Lᵢ(x);
`construir_polinomio` devuelve Pₙ(x) simplificado y la lista de Lᵢ;
`interpolar_directo` calcula Pₙ(x\*) sin construir el polinomio y devuelve los
pasos; `evaluar_en_malla` evalúa Pₙ en muchos puntos; `grado_polinomio` da el
grado real.

**`modules/errors.py`** — `error_absoluto`, `error_relativo`, `error_porcentual`
y `error_maximo`.

**`modules/validation.py`** — `validar_funcion`, `validar_numero`,
`validar_puntos`, `validar_intervalo` y `es_extrapolacion`. Todas lanzan
`ErrorValidacion` con un mensaje listo para mostrar.

**`utils/formato.py`** — convierte números y polinomios a texto y LaTeX.

**`app.py`** — la pantalla: inicio, datos (función, número de puntos, tabla) y
seis pestañas de resultados (Polinomio, Interpolar directo, Evaluación y errores,
Error máximo, Gráfica, Resultados).

## 9. Pruebas

```
python tests/test_basico.py
```
