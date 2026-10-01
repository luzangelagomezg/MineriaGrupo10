from flask import Flask, render_template, request
import os
import pandas as pd

app = Flask(__name__)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
RUTA_DATOS = os.path.join(
    BASE_DIR,
    "data",
    "presuntos_homicidios_2015_2024.csv"
)

df = pd.read_csv(RUTA_DATOS)

COLUMNA_ANIO = "Año del hecho"
COLUMNA_SEXO = "Sexo de la victima"
COLUMNA_EDAD = "Grupo de edad quinquenal"
COLUMNA_CICLO_VITAL = "Ciclo Vital"

ORDEN_GRUPOS_EDAD = [
    "(00 a 04)", "(05 a 09)", "(10 a 14)", "(15 a 17)", "(18 a 19)",
    "(20 a 24)", "(25 a 29)", "(30 a 34)", "(35 a 39)", "(40 a 44)",
    "(45 a 49)", "(50 a 54)", "(55 a 59)", "(60 a 64)", "(65 a 69)",
    "(70 a 74)", "(75 a 79)", "(80 y más)", "Por determinar", "Sin información"
]

ORDEN_CICLO_VITAL = [
    "(00 a 05) Primera Infancia",
    "(06 a 11) Infancia",
    "(12 a 17) Adolescencia",
    "(18 a 28) Juventud",
    "(29 a 59) Adultez",
    "(Más de 60) Adulto Mayor",
    "Por determinar",
    "Sin información"
]

ORDEN_SEXO = ["Hombre", "Mujer", "Indeterminado", "Sin dato"]


def formato_numero(valor):
    return f"{valor:,}".replace(",", ".")


def formato_porcentaje(valor):
    return f"{valor:.2f}".replace(".", ",")


def analizar_variable(datos, columna, orden, etiqueta):
    valores = datos[columna].astype("object").where(datos[columna].notna(), "Sin dato")
    conteos = valores.value_counts()
    categorias = [categoria for categoria in orden if categoria in conteos.index]
    categorias.extend(sorted(set(conteos.index).difference(orden)))
    total = len(datos)

    filas = [
        {
            "categoria": categoria,
            "cantidad": int(conteos[categoria]),
            "cantidad_texto": formato_numero(conteos[categoria]),
            "porcentaje": float(conteos[categoria] / total * 100) if total else 0,
            "porcentaje_texto": formato_porcentaje(conteos[categoria] / total * 100)
            if total else "0,00"
        }
        for categoria in categorias
    ]

    if not filas:
        dominante = {"categoria": "Sin datos", "cantidad": 0, "cantidad_texto": "0", "porcentaje": 0, "porcentaje_texto": "0,00"}
        minoritaria = dominante
        interpretacion = "No hay víctimas registradas en este subconjunto para describir la distribución."
    else:
        dominante = max(filas, key=lambda fila: fila["cantidad"])
        minoritaria = min(filas, key=lambda fila: fila["cantidad"])
        if len(filas) == 1:
            interpretacion = (
                f"En este subconjunto solo aparece {dominante['categoria']} "
                f"({dominante['cantidad_texto']} víctimas; {dominante['porcentaje_texto']} %); "
                "por tanto, no hay otras categorías para comparar."
            )
        else:
            interpretacion = (
                f"La mayor concentración de víctimas registradas según {etiqueta} corresponde a "
                f"{dominante['categoria']} ({dominante['cantidad_texto']}; "
                f"{dominante['porcentaje_texto']} %); la menor participación corresponde a "
                f"{minoritaria['categoria']} ({minoritaria['cantidad_texto']}; "
                f"{minoritaria['porcentaje_texto']} %). La distribución incluye "
                f"{len(filas)} categorías."
            )

    ranking = sorted(filas, key=lambda fila: fila["cantidad"], reverse=True)
    menores = sorted(filas, key=lambda fila: fila["cantidad"])
    return {
        "categorias": filas,
        "valores": [fila["cantidad"] for fila in filas],
        "cantidades_texto": [fila["cantidad_texto"] for fila in filas],
        "porcentajes": [fila["porcentaje"] for fila in filas],
        "porcentajes_texto": [fila["porcentaje_texto"] for fila in filas],
        "dominante": dominante,
        "minoritaria": minoritaria,
        "principales": ranking[:3],
        "menores": menores[:2],
        "interpretacion": interpretacion
    }


def texto_categorias(filas):
    return "; ".join(
        f"{fila['categoria']}: {fila['cantidad_texto']} ({fila['porcentaje_texto']} %)"
        for fila in filas
    )


def crear_resumen_general(datos):
    total = len(datos)
    analisis = {
        "sexo": analizar_variable(datos, COLUMNA_SEXO, ORDEN_SEXO, "sexo"),
        "edad": analizar_variable(datos, COLUMNA_EDAD, ORDEN_GRUPOS_EDAD, "grupo de edad"),
        "ciclo_vital": analizar_variable(datos, COLUMNA_CICLO_VITAL, ORDEN_CICLO_VITAL, "ciclo vital")
    }
    sexo = analisis["sexo"]
    edad = analisis["edad"]
    ciclo = analisis["ciclo_vital"]
    hombres = next((fila for fila in sexo["categorias"] if fila["categoria"] == "Hombre"), sexo["minoritaria"])
    mujeres = next((fila for fila in sexo["categorias"] if fila["categoria"] == "Mujer"), sexo["minoritaria"])
    anos = datos[COLUMNA_ANIO].dropna()
    periodo = f"{int(anos.min())}–{int(anos.max())}" if not anos.empty else "sin periodo"

    conclusion = (
        f"Predominan hombres ({hombres['porcentaje_texto']} %), las edades "
        f"{edad['dominante']['categoria']} ({edad['dominante']['porcentaje_texto']} %) "
        f"y {ciclo['dominante']['categoria']} ({ciclo['dominante']['porcentaje_texto']} %). "
        "Son porcentajes de registros, no estimaciones de riesgo."
    )
    respuesta = (
        f"En el conjunto completo {periodo} hay {formato_numero(total)} víctimas registradas. "
        f"Por sexo: {texto_categorias(sexo['categorias'])}. "
        f"La mayor concentración por edad corresponde a {edad['dominante']['categoria']} "
        f"({edad['dominante']['cantidad_texto']}; {edad['dominante']['porcentaje_texto']} %), "
        f"y la menor a {edad['minoritaria']['categoria']} "
        f"({edad['minoritaria']['cantidad_texto']}; {edad['minoritaria']['porcentaje_texto']} %). "
        f"Por ciclo vital predomina {ciclo['dominante']['categoria']} "
        f"({ciclo['dominante']['cantidad_texto']}; {ciclo['dominante']['porcentaje_texto']} %); "
        f"la menor participación corresponde a {ciclo['minoritaria']['categoria']} "
        f"({ciclo['minoritaria']['cantidad_texto']}; {ciclo['minoritaria']['porcentaje_texto']} %). "
        "Estas distribuciones describen los registros disponibles y no establecen causas."
    )

    conocimientos = [
        {
            "titulo": "Composición de las víctimas registradas según sexo.",
            "pregunta": "¿Cómo se distribuyen las víctimas registradas entre las categorías de sexo?",
            "variables": COLUMNA_SEXO,
            "procedimiento": f"Se agruparon los {formato_numero(total)} registros por sexo y se calculó cada participación sobre el total del conjunto.",
            "evidencia": texto_categorias(sexo["categorias"]),
            "hallazgo": f"La categoría predominante es {sexo['dominante']['categoria']} ({sexo['dominante']['cantidad_texto']}; {sexo['dominante']['porcentaje_texto']} %); la minoritaria es {sexo['minoritaria']['categoria']} ({sexo['minoritaria']['cantidad_texto']}; {sexo['minoritaria']['porcentaje_texto']} %).",
            "interpretacion": "La composición registrada se concentra en la categoría predominante; las participaciones representan la distribución de casos observados.",
            "utilidad": "Puede orientar cruces exploratorios posteriores con año, territorio y variables contextuales.",
            "limitacion": "Las cantidades no comparan el tamaño de cada grupo en la población ni permiten estimar riesgo o tasas."
        },
        {
            "titulo": "Concentración de las víctimas registradas según grupo de edad.",
            "pregunta": "¿En qué grupos quinquenales se concentra la mayor cantidad de víctimas registradas?",
            "variables": COLUMNA_EDAD,
            "procedimiento": f"Se agruparon los registros por grupo quinquenal, se contaron las categorías y se calculó su participación sobre {formato_numero(total)} registros.",
            "evidencia": f"Principales: {texto_categorias(edad['principales'])}. Menor cantidad: {texto_categorias(edad['menores'])}.",
            "hallazgo": f"La mayor cantidad corresponde a {edad['dominante']['categoria']} ({edad['dominante']['cantidad_texto']}; {edad['dominante']['porcentaje_texto']} %); la menor, a {edad['minoritaria']['categoria']} ({edad['minoritaria']['cantidad_texto']}; {edad['minoritaria']['porcentaje_texto']} %).",
            "interpretacion": "Los recuentos muestran cómo se distribuyen los casos entre intervalos etarios y qué intervalos reúnen más registros.",
            "utilidad": "Sirve para orientar análisis descriptivos más detallados por periodo, territorio o circunstancias del hecho.",
            "limitacion": "Los recuentos no consideran cuántas personas hay en cada grupo de edad; no expresan riesgo ni tasas comparativas."
        },
        {
            "titulo": "Distribución de las víctimas registradas según ciclo vital.",
            "pregunta": "¿Qué etapas del ciclo vital reúnen más y menos víctimas registradas?",
            "variables": COLUMNA_CICLO_VITAL,
            "procedimiento": f"Se agruparon los registros por ciclo vital y se calcularon cantidades y porcentajes respecto de {formato_numero(total)} registros.",
            "evidencia": f"Principales: {texto_categorias(ciclo['principales'])}. Menor cantidad: {texto_categorias(ciclo['menores'])}.",
            "hallazgo": f"Predomina {ciclo['dominante']['categoria']} ({ciclo['dominante']['cantidad_texto']}; {ciclo['dominante']['porcentaje_texto']} %); la menor cantidad corresponde a {ciclo['minoritaria']['categoria']} ({ciclo['minoritaria']['cantidad_texto']}; {ciclo['minoritaria']['porcentaje_texto']} %).",
            "interpretacion": "La distribución describe el peso de cada etapa dentro de los registros disponibles, incluidas las categorías informativas.",
            "utilidad": "Puede apoyar la selección de grupos para cruces exploratorios con información temporal, territorial o contextual.",
            "limitacion": "Las categorías no tienen necesariamente el mismo tamaño poblacional y los conteos no miden riesgo individual."
        }
    ]

    return {
        "periodo": periodo,
        "total": total,
        "total_texto": formato_numero(total),
        "hombres": hombres,
        "mujeres": mujeres,
        "sexo": sexo,
        "edad": edad,
        "ciclo_vital": ciclo,
        "conclusion": conclusion,
        "respuesta": respuesta,
        "variables": [COLUMNA_SEXO, COLUMNA_EDAD, COLUMNA_CICLO_VITAL, COLUMNA_ANIO],
        "conocimientos": conocimientos,
        "limitacion": (
            "Este análisis es descriptivo y se basa en registros de víctimas de presuntos homicidios. "
            "Las cantidades absolutas no permiten concluir que un grupo tenga mayor riesgo que otro; "
            "para estimar tasas o comparar riesgos se requieren denominadores poblacionales por sexo, "
            "edad y periodo. La presencia de categorías como Indeterminado, Por determinar y Sin información "
            "también delimita la completitud de algunas variables."
        ),
        "decision": (
            f"Como uso exploratorio, se podrían priorizar cruces temporales, territoriales y contextuales "
            f"para {edad['dominante']['categoria']} y {ciclo['dominante']['categoria']}, y revisar la "
            "completitud de las categorías informativas. Esto no basta por sí solo para recomendar una intervención."
        )
    }

# Datos de cada dimensión: los usan el menú, la página de inicio y los encabezados
DIMENSIONES = [
    {
        "endpoint": "poblacional",
        "nombre": "Dimensión poblacional",
        "icono": "bi-people-fill",
        "integrante": 1,
        "pregunta": "¿Cómo está compuesta y distribuida la población analizada según sus principales características?",
    },
    {
        "endpoint": "territorial",
        "nombre": "Dimensión territorial",
        "icono": "bi-geo-alt-fill",
        "integrante": 2,
        "pregunta": "¿Cómo se distribuye la población y sus principales características entre los territorios disponibles?",
    },
    {
        "endpoint": "temporal",
        "nombre": "Dimensión temporal",
        "icono": "bi-graph-up-arrow",
        "integrante": 3,
        "pregunta": "¿Cómo ha cambiado el comportamiento de la población durante el periodo disponible?",
    },
    {
        "endpoint": "multivariada",
        "nombre": "Dimensión relacional y multivariada",
        "icono": "bi-diagram-3-fill",
        "integrante": 4,
        "pregunta": "¿Qué diferencias o relaciones evidentes pueden identificarse al analizar conjuntamente tres o más variables?",
    },
]


@app.context_processor
def datos_globales():
    return {"dimensiones": DIMENSIONES}


def dimension(endpoint):
    return next(d for d in DIMENSIONES if d["endpoint"] == endpoint)


@app.route("/")
def inicio():
    return render_template("index.html")


@app.route("/poblacional")
def poblacional():
    anios_disponibles = sorted(int(anio) for anio in df[COLUMNA_ANIO].dropna().unique())
    sexos_disponibles = [
        sexo for sexo in ("Hombre", "Mujer", "Indeterminado")
        if sexo in df[COLUMNA_SEXO].dropna().unique()
    ]

    anio_solicitado = request.args.get("anio", "Todos")
    if anio_solicitado != "Todos" and anio_solicitado not in {
        str(anio) for anio in anios_disponibles
    }:
        anio_solicitado = "Todos"

    sexo_solicitado = request.args.get("sexo", "Todos")
    if sexo_solicitado != "Todos" and sexo_solicitado not in sexos_disponibles:
        sexo_solicitado = "Todos"

    datos_filtrados = df.copy()
    if anio_solicitado != "Todos":
        datos_filtrados = datos_filtrados.loc[
            datos_filtrados[COLUMNA_ANIO] == int(anio_solicitado)
        ].copy()
    if sexo_solicitado != "Todos":
        datos_filtrados = datos_filtrados.loc[
            datos_filtrados[COLUMNA_SEXO] == sexo_solicitado
        ].copy()

    total_registros = len(datos_filtrados)
    analisis_filtrado = {
        "sexo": analizar_variable(datos_filtrados, COLUMNA_SEXO, ORDEN_SEXO, "sexo"),
        "edad": analizar_variable(datos_filtrados, COLUMNA_EDAD, ORDEN_GRUPOS_EDAD, "grupo de edad"),
        "ciclo_vital": analizar_variable(datos_filtrados, COLUMNA_CICLO_VITAL, ORDEN_CICLO_VITAL, "ciclo vital")
    }
    grupo_edad_predominante = analisis_filtrado["edad"]["dominante"]["categoria"]
    cantidad_grupo_predominante = analisis_filtrado["edad"]["dominante"]["cantidad"]
    ciclo_vital_predominante = analisis_filtrado["ciclo_vital"]["dominante"]["categoria"]
    cantidad_ciclo_vital_predominante = analisis_filtrado["ciclo_vital"]["dominante"]["cantidad"]

    datos_graficas = {
        nombre: {
            "etiquetas": [fila["categoria"] for fila in analisis["categorias"]],
            "valores": analisis["valores"],
            "porcentajes": analisis["porcentajes"],
            "cantidades_texto": analisis["cantidades_texto"],
            "porcentajes_texto": analisis["porcentajes_texto"],
            "interpretacion": analisis["interpretacion"]
        }
        for nombre, analisis in analisis_filtrado.items()
    }
    resumen_general = crear_resumen_general(df)

    return render_template(
        "poblacional.html",
        dim=dimension("poblacional"),
        total_registros=total_registros,
        grupo_edad_predominante=grupo_edad_predominante,
        cantidad_grupo_predominante=cantidad_grupo_predominante,
        ciclo_vital_predominante=ciclo_vital_predominante,
        cantidad_ciclo_vital_predominante=cantidad_ciclo_vital_predominante,
        anios_disponibles=anios_disponibles,
        sexos_disponibles=sexos_disponibles,
        anio_seleccionado=anio_solicitado,
        sexo_seleccionado=sexo_solicitado,
        datos_graficas=datos_graficas,
        resumen_general=resumen_general
    )


@app.route("/territorial")
def territorial():
    return render_template("territorial.html", dim=dimension("territorial"))


@app.route("/temporal")
def temporal():
    return render_template("temporal.html", dim=dimension("temporal"))


@app.route("/multivariada")
def multivariada():
    return render_template("multivariada.html", dim=dimension("multivariada"))


if __name__ == "__main__":
    app.run(debug=True)
