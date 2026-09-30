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

    conteos_sexo = datos_filtrados[COLUMNA_SEXO].value_counts()
    etiquetas_sexo = [
        sexo for sexo in sexos_disponibles if conteos_sexo.get(sexo, 0) > 0
    ]

    conteos_edad = datos_filtrados[COLUMNA_EDAD].value_counts()
    edades_presentes = set(conteos_edad.index)
    etiquetas_edad = [
        edad for edad in ORDEN_GRUPOS_EDAD if edad in edades_presentes
    ]
    etiquetas_edad.extend(sorted(edades_presentes.difference(ORDEN_GRUPOS_EDAD)))

    conteos_ciclo_vital = datos_filtrados[COLUMNA_CICLO_VITAL].value_counts()
    ciclos_presentes = set(conteos_ciclo_vital.index)
    etiquetas_ciclo_vital = [
        ciclo for ciclo in ORDEN_CICLO_VITAL if ciclo in ciclos_presentes
    ]
    etiquetas_ciclo_vital.extend(
        sorted(ciclos_presentes.difference(ORDEN_CICLO_VITAL))
    )

    if conteos_edad.empty:
        grupo_edad_predominante = "Sin datos"
        cantidad_grupo_predominante = 0
    else:
        grupo_edad_predominante = conteos_edad.index[0]
        cantidad_grupo_predominante = int(conteos_edad.iloc[0])

    if conteos_ciclo_vital.empty:
        ciclo_vital_predominante = "Sin datos"
        cantidad_ciclo_vital_predominante = 0
    else:
        ciclo_vital_predominante = conteos_ciclo_vital.index[0]
        cantidad_ciclo_vital_predominante = int(conteos_ciclo_vital.iloc[0])

    datos_graficas = {
        "sexo": {
            "etiquetas": etiquetas_sexo,
            "valores": [int(conteos_sexo[sexo]) for sexo in etiquetas_sexo]
        },
        "edad": {
            "etiquetas": etiquetas_edad,
            "valores": [int(conteos_edad[edad]) for edad in etiquetas_edad]
        },
        "ciclo_vital": {
            "etiquetas": etiquetas_ciclo_vital,
            "valores": [
                int(conteos_ciclo_vital[ciclo]) for ciclo in etiquetas_ciclo_vital
            ]
        }
    }

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
        datos_graficas=datos_graficas
    )


@app.route("/territorial")
def territorial():
    # Dimensión territorial (Integrante 2): la lógica está en dimension_territorial.py
    from flask import request
    from dimension_territorial import tablero_territorial

    contexto = tablero_territorial(request.args)
    return render_template("territorial.html", dim=dimension("territorial"), **contexto)


@app.route("/temporal")
def temporal():
    # Dimensión temporal (Integrante 3): la lógica está en dimension_temporal.py
    from flask import request
    from dimension_temporal import tablero_temporal

    contexto = tablero_temporal(request.args)
    return render_template("temporal.html", dim=dimension("temporal"), **contexto)


@app.route("/multivariada")
def multivariada():
    return render_template("multivariada.html", dim=dimension("multivariada"))


if __name__ == "__main__":
    app.run(debug=True)
