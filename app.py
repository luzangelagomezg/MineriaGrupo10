from flask import Flask, render_template

app = Flask(__name__)

# Datos de cada dimensión: los usan el menú, la página de inicio y los encabezados
DIMENSIONES = [
    {
        "endpoint": "poblacional",
        "nombre": "Dimensión poblacional",
        "icono": "bi-people-fill",
        "integrante": 1,
        "pregunta": "¿Cómo está compuesta y distribuida la población analizada según sus principales características?",
        "resumen": "Sexo, edad, ciclo vital, escolaridad y pertenencia étnica de las víctimas.",
    },
    {
        "endpoint": "territorial",
        "nombre": "Dimensión territorial",
        "icono": "bi-geo-alt-fill",
        "integrante": 2,
        "pregunta": "¿Cómo se distribuye la población y sus principales características entre los territorios disponibles?",
        "resumen": "Departamentos, municipios y zonas urbanas o rurales donde ocurren los hechos.",
    },
    {
        "endpoint": "temporal",
        "nombre": "Dimensión temporal",
        "icono": "bi-graph-up-arrow",
        "integrante": 3,
        "pregunta": "¿Cómo ha cambiado el comportamiento de la población durante el periodo disponible?",
        "resumen": "Evolución por año, mes, día de la semana y rango horario entre 2015 y 2024.",
    },
    {
        "endpoint": "multivariada",
        "nombre": "Dimensión relacional y multivariada",
        "icono": "bi-diagram-3-fill",
        "integrante": 4,
        "pregunta": "¿Qué diferencias o relaciones evidentes pueden identificarse al analizar conjuntamente tres o más variables?",
        "resumen": "Cruces entre sexo, edad, mecanismo, territorio y periodo.",
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
    return render_template("poblacional.html", dim=dimension("poblacional"))


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
