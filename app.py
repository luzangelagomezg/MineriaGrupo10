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
CATEGORIAS_INFORMATIVAS = {"Por determinar", "Sin información", "Sin dato"}


def formato_numero(valor):
    return f"{valor:,}".replace(",", ".")


def formato_porcentaje(valor):
    return f"{valor:.2f}".replace(".", ",")


def analizar_variable(datos, columna, orden, etiqueta, sexo_seleccionado="Todos", edad_analisis=None):
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

    filas_demograficas = [
        fila for fila in filas
        if fila["categoria"] not in CATEGORIAS_INFORMATIVAS
        and not (etiqueta == "sexo" and fila["categoria"] == "Sin dato")
    ]
    fila_sin_datos = {
        "categoria": "Sin datos", "cantidad": 0, "cantidad_texto": "0",
        "porcentaje": 0, "porcentaje_texto": "0,00"
    }
    dominante = max(filas_demograficas, key=lambda fila: fila["cantidad"]) if filas_demograficas else fila_sin_datos
    minoritaria = min(filas_demograficas, key=lambda fila: fila["cantidad"]) if filas_demograficas else fila_sin_datos
    ranking = sorted(filas_demograficas, key=lambda fila: fila["cantidad"], reverse=True)
    menores = sorted(filas_demograficas, key=lambda fila: fila["cantidad"])
    if etiqueta == "sexo":
        interpretacion = interpretar_sexo(filas, total, sexo_seleccionado)
    elif etiqueta == "grupo de edad":
        interpretacion = interpretar_edad(filas, total, conteos)
    else:
        grupo_edad = (
            edad_analisis["dominante"]["categoria"]
            if edad_analisis else dominante["categoria"]
        )
        interpretacion = interpretar_ciclo_vital(
            filas, total, conteos, grupo_edad
        )
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
        "diferencia_principales": ranking[0]["cantidad"] - ranking[1]["cantidad"] if len(ranking) > 1 else 0,
        "diferencia_principales_pp": ranking[0]["porcentaje"] - ranking[1]["porcentaje"] if len(ranking) > 1 else 0,
        "total": total,
        "interpretacion": interpretacion
    }


def texto_categorias(filas):
    return "; ".join(
        f"{fila['categoria']}: {fila['cantidad_texto']} ({fila['porcentaje_texto']} %)"
        for fila in filas
    )


def describir_categoria(fila):
    return f"{fila['categoria']}: {fila['cantidad_texto']} ({fila['porcentaje_texto']} %)"


def fila_categoria(filas, categoria):
    return next((fila for fila in filas if fila["categoria"] == categoria), None)


def interpretar_sexo(filas, total, sexo_seleccionado):
    if not total:
        return "No hay víctimas registradas para esta selección; no es posible comparar categorías de sexo."

    if sexo_seleccionado != "Todos":
        categoria = fila_categoria(filas, sexo_seleccionado)
        cantidad = categoria["cantidad_texto"] if categoria else "0"
        return (
            f"El filtro limita esta visualización a {sexo_seleccionado} "
            f"({cantidad} víctimas registradas). La composición por sexo no es comparable "
            "en este subconjunto porque el filtro restringe la variable a una categoría; "
            "consulte edad y ciclo vital para caracterizarlo."
        )

    ranking = sorted(
        (fila for fila in filas if fila["categoria"] != "Sin dato"),
        key=lambda fila: fila["cantidad"],
        reverse=True
    )
    if len(ranking) < 2:
        return f"El subconjunto contiene {formato_numero(total)} víctimas, pero no hay varias categorías de sexo determinadas para comparar."

    hombre = fila_categoria(filas, "Hombre")
    mujer = fila_categoria(filas, "Mujer")
    diferencia = abs(hombre["cantidad"] - mujer["cantidad"]) if hombre and mujer else 0
    diferencia_pp = abs(hombre["porcentaje"] - mujer["porcentaje"]) if hombre and mujer else 0
    relacion = hombre["cantidad"] / mujer["cantidad"] if hombre and mujer and mujer["cantidad"] else 0
    sin_dato = fila_categoria(filas, "Sin dato")
    texto_sin_dato = (
        f" Se conservan {sin_dato['cantidad_texto']} registros sin dato de sexo."
        if sin_dato else ""
    )
    return (
        f"De {formato_numero(total)} víctimas registradas, predomina {describir_categoria(ranking[0])}; "
        f"le sigue {describir_categoria(ranking[1])} y la categoría minoritaria es "
        f"{describir_categoria(ranking[-1])}.\n\nEntre hombres y mujeres hay una diferencia de "
        f"{formato_numero(diferencia)} registros y {formato_porcentaje(diferencia_pp)} puntos "
        f"porcentuales, con una relación aproximada de {formato_porcentaje(relacion)} a 1 "
        f"en los registros. La distribución está concentrada en la categoría predominante.{texto_sin_dato}"
    )


def interpretar_edad(filas, total, conteos):
    if not total:
        return "No hay víctimas registradas para esta selección; no es posible describir la distribución por edad."

    filas_edad = [fila for fila in filas if fila["categoria"] not in CATEGORIAS_INFORMATIVAS]
    if not filas_edad:
        especiales = [fila for fila in filas if fila["categoria"] in CATEGORIAS_INFORMATIVAS]
        return (
            "El subconjunto contiene víctimas, pero no hay categorías de edad determinadas para comparar. "
            f"Categorías informativas: {texto_categorias(especiales)}."
        )

    ranking = sorted(filas_edad, key=lambda fila: fila["cantidad"], reverse=True)
    menores = sorted(filas_edad, key=lambda fila: fila["cantidad"])
    principales = "; ".join(describir_categoria(fila) for fila in ranking[:3])
    comparacion = ""
    if len(ranking) > 1:
        diferencia = ranking[0]["cantidad"] - ranking[1]["cantidad"]
        diferencia_pp = ranking[0]["porcentaje"] - ranking[1]["porcentaje"]
        comparacion = (
            f" La diferencia entre los dos primeros es {formato_numero(diferencia)} registros "
            f"({formato_porcentaje(diferencia_pp)} puntos porcentuales)."
        )

    bloque = ["(18 a 19)", "(20 a 24)", "(25 a 29)", "(30 a 34)"]
    cantidad_bloque = int(sum(conteos.get(categoria, 0) for categoria in bloque))
    porcentaje_bloque = cantidad_bloque / total * 100
    resto = total - cantidad_bloque
    especiales = [fila for fila in filas if fila["categoria"] in CATEGORIAS_INFORMATIVAS]
    texto_especiales = (
        " Las categorías informativas se mantienen visibles: "
        + "; ".join(describir_categoria(fila) for fila in especiales)
        + "; no representan grupos etarios."
        if especiales else ""
    )
    return (
        f"Los grupos con más registros son {principales}.{comparacion}\n\nLos intervalos consecutivos "
        f"de 18 a 34 años reúnen {formato_numero(cantidad_bloque)} víctimas "
        f"({formato_porcentaje(porcentaje_bloque)} %), frente a {formato_numero(resto)} "
        f"({formato_porcentaje(resto / total * 100)} %) en el resto de las categorías. "
        f"Las menores cantidades se encuentran en {'; '.join(describir_categoria(fila) for fila in menores[:2])}.{texto_especiales} "
        "La distribución concentra registros en intervalos concretos, sin medir riesgo por edad."
    )


def interpretar_ciclo_vital(filas, total, conteos, grupo_edad):
    if not total:
        return "No hay víctimas registradas para esta selección; no es posible describir la distribución por ciclo vital."

    filas_ciclo = [fila for fila in filas if fila["categoria"] not in CATEGORIAS_INFORMATIVAS]
    if not filas_ciclo:
        especiales = [fila for fila in filas if fila["categoria"] in CATEGORIAS_INFORMATIVAS]
        return (
            "El subconjunto contiene víctimas, pero no hay ciclos vitales determinados para comparar. "
            f"Categorías informativas: {texto_categorias(especiales)}."
        )

    ranking = sorted(filas_ciclo, key=lambda fila: fila["cantidad"], reverse=True)
    menores = sorted(filas_ciclo, key=lambda fila: fila["cantidad"])
    principales = "; ".join(describir_categoria(fila) for fila in ranking[:2])
    if len(ranking) > 1:
        diferencia = ranking[0]["cantidad"] - ranking[1]["cantidad"]
        diferencia_pp = ranking[0]["porcentaje"] - ranking[1]["porcentaje"]
        cantidad_dos = ranking[0]["cantidad"] + ranking[1]["cantidad"]
        comparacion = (
            f"La diferencia entre ambas es {formato_numero(diferencia)} registros "
            f"({formato_porcentaje(diferencia_pp)} puntos porcentuales); juntas suman "
            f"{formato_numero(cantidad_dos)} ({formato_porcentaje(cantidad_dos / total * 100)} %)."
        )
    else:
        cantidad_dos = ranking[0]["cantidad"]
        comparacion = "Solo hay una categoría de ciclo vital determinada para comparar."
    verbo_predominio = "Predominan" if len(ranking) > 1 else "Predomina"
    texto_menores = (
        f"Las categorías con menos registros son {'; '.join(describir_categoria(fila) for fila in menores[:2])}."
        if len(menores) > 1 else
        f"La única etapa determinada es {describir_categoria(menores[0])}."
    )
    cantidad_ja = int(conteos.get("(18 a 28) Juventud", 0) + conteos.get("(29 a 59) Adultez", 0))
    especiales = [fila for fila in filas if fila["categoria"] in CATEGORIAS_INFORMATIVAS]
    texto_especiales = (
        " Las categorías informativas presentes son "
        + "; ".join(describir_categoria(fila) for fila in especiales)
        + "."
        if especiales else ""
    )
    return (
        f"{verbo_predominio} {principales}. {comparacion}\n\n"
        f"Al sumar Juventud y Adultez se obtienen {formato_numero(cantidad_ja)} registros "
        f"({formato_porcentaje(cantidad_ja / total * 100)} %); {texto_menores}{texto_especiales} "
        f"El grupo quinquenal predominante es {grupo_edad}; la categoría de ciclo más frecuente "
        f"es {ranking[0]['categoria']}. No hay contradicción: los quinquenios son intervalos "
        "estrechos y los ciclos agrupan rangos de edad más amplios."
    )


def crear_resumen_general(datos):
    total = len(datos)
    sexo = analizar_variable(datos, COLUMNA_SEXO, ORDEN_SEXO, "sexo")
    edad = analizar_variable(datos, COLUMNA_EDAD, ORDEN_GRUPOS_EDAD, "grupo de edad")
    ciclo = analizar_variable(
        datos, COLUMNA_CICLO_VITAL, ORDEN_CICLO_VITAL, "ciclo vital",
        edad_analisis=edad
    )
    hombres = next((fila for fila in sexo["categorias"] if fila["categoria"] == "Hombre"), sexo["minoritaria"])
    mujeres = next((fila for fila in sexo["categorias"] if fila["categoria"] == "Mujer"), sexo["minoritaria"])
    indeterminado = fila_categoria(sexo["categorias"], "Indeterminado")
    indeterminado = indeterminado or {"categoria": "Indeterminado", "cantidad": 0, "cantidad_texto": "0", "porcentaje_texto": "0,00"}
    diferencia_sexo = abs(hombres["cantidad"] - mujeres["cantidad"])
    diferencia_sexo_pp = abs(hombres["porcentaje"] - mujeres["porcentaje"])
    relacion_hombre_mujer = hombres["cantidad"] / mujeres["cantidad"] if mujeres["cantidad"] else 0

    grupos_18_34 = ["(18 a 19)", "(20 a 24)", "(25 a 29)", "(30 a 34)"]
    categorias_edad = {fila["categoria"]: fila for fila in edad["categorias"]}
    cantidad_18_34 = sum(categorias_edad.get(grupo, {}).get("cantidad", 0) for grupo in grupos_18_34)
    porcentaje_18_34 = cantidad_18_34 / total * 100 if total else 0
    resto_edad = total - cantidad_18_34
    porcentaje_resto_edad = resto_edad / total * 100 if total else 0

    categoria_edad = {fila["categoria"]: fila for fila in edad["categorias"]}
    dos_principales_ciclos = ciclo["principales"][:2]
    cantidad_dos_ciclos = sum(fila["cantidad"] for fila in dos_principales_ciclos)
    porcentaje_dos_ciclos = cantidad_dos_ciclos / total * 100 if total else 0
    categorias_ciclo = {fila["categoria"]: fila for fila in ciclo["categorias"]}
    cantidad_juventud_adultez = sum(
        categorias_ciclo.get(categoria, {}).get("cantidad", 0)
        for categoria in ("(18 a 28) Juventud", "(29 a 59) Adultez")
    )
    porcentaje_juventud_adultez = cantidad_juventud_adultez / total * 100 if total else 0
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
            "pregunta": "¿Qué categorías de sexo componen los registros y qué tan concentrada está su participación?",
            "variables": COLUMNA_SEXO,
            "procedimiento": f"Se agruparon los {formato_numero(total)} registros por sexo, se dividió cada cantidad por el total y se compararon hombres y mujeres en cantidades y puntos porcentuales. La relación hombre/mujer se calculó dividiendo sus recuentos.",
            "evidencia": f"{texto_categorias(sexo['categorias'])}. Diferencia hombres-mujeres: {formato_numero(diferencia_sexo)} registros y {formato_porcentaje(diferencia_sexo_pp)} puntos porcentuales. Relación descriptiva: {formato_porcentaje(relacion_hombre_mujer)} a 1.",
            "hallazgo": f"La distribución está fuertemente concentrada en hombres ({hombres['porcentaje_texto']} % del total); mujeres representan {mujeres['porcentaje_texto']} % e Indeterminado {indeterminado['porcentaje_texto']} %.",
            "interpretacion": f"La brecha de {formato_numero(diferencia_sexo)} registros y {formato_porcentaje(diferencia_sexo_pp)} puntos porcentuales describe una composición desigual de los casos observados. La relación aproximada {formato_porcentaje(relacion_hombre_mujer)} a 1 compara recuentos del dataset, no las poblaciones de cada sexo.",
            "utilidad": "Puede orientar cruces exploratorios posteriores con año, territorio y variables contextuales.",
            "limitacion": "Sin conocer cuántos hombres y mujeres integran la población de referencia en cada periodo, esta diferencia de registros no permite comparar frecuencias poblacionales ni atribuir causas."
        },
        {
            "titulo": "Concentración de las víctimas registradas según grupo de edad.",
            "pregunta": "¿Cómo se distribuyen los registros entre los grupos quinquenales y qué concentración forman los intervalos de 18 a 34 años?",
            "variables": COLUMNA_EDAD,
            "procedimiento": f"Se contaron los registros por intervalo quinquenal y se calcularon porcentajes sobre {formato_numero(total)}. Se ordenaron los grupos por cantidad, se restaron los recuentos y participaciones de los dos primeros, y se sumaron 18–19, 20–24, 25–29 y 30–34 para compararlos con el resto.",
            "evidencia": f"Tres grupos principales: {texto_categorias(edad['principales'])}. Brecha entre los dos primeros: {formato_numero(edad['diferencia_principales'])} registros ({formato_porcentaje(edad['diferencia_principales_pp'])} puntos porcentuales). Intervalos 18–34: {formato_numero(cantidad_18_34)} ({formato_porcentaje(porcentaje_18_34)} %); resto: {formato_numero(resto_edad)} ({formato_porcentaje(porcentaje_resto_edad)} %). Menores grupos etarios determinados: {texto_categorias(edad['menores'])}. Categorías informativas: {texto_categorias([fila for fila in edad['categorias'] if fila['categoria'] in CATEGORIAS_INFORMATIVAS])}.",
            "hallazgo": f"El mayor recuento se concentra en {edad['dominante']['categoria']}, seguido por {edad['principales'][1]['categoria']} y {edad['principales'][2]['categoria']}. En conjunto, los intervalos consecutivos de 18 a 34 años contienen más de la mitad de los registros ({formato_porcentaje(porcentaje_18_34)} %).",
            "interpretacion": f"La distribución se concentra en varios grupos jóvenes-adultos consecutivos, no únicamente en la barra modal. La brecha de {formato_numero(edad['diferencia_principales'])} entre los dos primeros es menor que los recuentos de ambos, y los grupos menos frecuentes/categorías informativas se mantienen diferenciados.",
            "utilidad": "Sirve para orientar análisis descriptivos más detallados por periodo, territorio o circunstancias del hecho.",
            "limitacion": "El bloque 18–34 reúne intervalos definidos, pero sus recuentos no están ajustados por la cantidad de personas de esas edades; Por determinar y Sin información no son edades y reducen la precisión de la clasificación disponible."
        },
        {
            "titulo": "Distribución de las víctimas registradas según ciclo vital.",
            "pregunta": "¿Qué etapas del ciclo vital concentran los registros y cómo se compara su distribución con los intervalos quinquenales?",
            "variables": COLUMNA_CICLO_VITAL,
            "procedimiento": f"Se agruparon los {formato_numero(total)} registros por ciclo, se calcularon participaciones sobre el total, se compararon las dos etapas mayores en cantidad y puntos porcentuales, y se sumaron Juventud y Adultez. Las categorías informativas se conservaron aparte.",
            "evidencia": f"Distribución completa: {texto_categorias(ciclo['categorias'])}. Las dos etapas principales reúnen {formato_numero(cantidad_dos_ciclos)} ({formato_porcentaje(porcentaje_dos_ciclos)} %), con una diferencia de {formato_numero(ciclo['diferencia_principales'])} registros ({formato_porcentaje(ciclo['diferencia_principales_pp'])} puntos porcentuales). Juventud+Adultez: {formato_numero(cantidad_juventud_adultez)} ({formato_porcentaje(porcentaje_juventud_adultez)} %). Menores etapas definidas: {texto_categorias(ciclo['menores'])}.",
            "hallazgo": f"Adultez y Juventud concentran conjuntamente {formato_porcentaje(porcentaje_juventud_adultez)} % de los registros. Adultez encabeza la distribución con {ciclo['dominante']['cantidad_texto']} y supera a Juventud en {formato_numero(ciclo['diferencia_principales'])} registros; Por determinar y Sin información se reportan aparte.",
            "interpretacion": f"El ciclo vital resume intervalos amplios: su predominio en Adultez no contradice que el grupo quinquenal modal sea {edad['dominante']['categoria']}. Un quinquenio representa un tramo estrecho, mientras Adultez agrupa varios rangos; ambas lecturas describen niveles distintos de agregación.",
            "utilidad": "Puede apoyar la selección de grupos para cruces exploratorios con información temporal, territorial o contextual.",
            "limitacion": "Los ciclos agrupan rangos de distinta amplitud y no son comparables como grupos poblacionales del mismo tamaño; Por determinar y Sin información no identifican una etapa vital."
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
    analisis_sexo = analizar_variable(
        datos_filtrados, COLUMNA_SEXO, ORDEN_SEXO, "sexo",
        sexo_seleccionado=sexo_solicitado
    )
    analisis_edad = analizar_variable(
        datos_filtrados, COLUMNA_EDAD, ORDEN_GRUPOS_EDAD, "grupo de edad"
    )
    analisis_ciclo = analizar_variable(
        datos_filtrados, COLUMNA_CICLO_VITAL, ORDEN_CICLO_VITAL, "ciclo vital",
        edad_analisis=analisis_edad
    )
    analisis_filtrado = {
        "sexo": analisis_sexo,
        "edad": analisis_edad,
        "ciclo_vital": analisis_ciclo
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
    # Dimensión relacional y multivariada (Integrante 4): la lógica está en dimension_multivariada.py
    from dimension_multivariada import tablero_multivariado

    contexto = tablero_multivariado(request.args)
    return render_template("multivariada.html", dim=dimension("multivariada"), **contexto)


if __name__ == "__main__":
    app.run(debug=True)
