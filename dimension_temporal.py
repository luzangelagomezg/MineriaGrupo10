"""
Dimensión temporal (Integrante 3)

Pregunta: ¿Cómo ha cambiado el comportamiento de la población
durante el periodo disponible?

Este módulo carga solo las columnas necesarias del conjunto de datos,
limpia las variables de tiempo y calcula los indicadores, las series
de las gráficas y las interpretaciones del tablero temporal.
"""
import os

import pandas as pd

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
RUTA_DATOS = os.path.join(BASE_DIR, "data", "presuntos_homicidios_2015_2024.csv")

# Columnas originales del conjunto de datos que usa esta dimensión
COL_ANIO = "Año del hecho"
COL_MES = "Mes del hecho"
COL_DIA = "Dia del hecho"
COL_HORA = "Rango de Hora del Hecho X 3 Horas"
COL_SEXO = "Sexo de la victima"
COL_DEPTO = "Departamento del hecho DANE"

COLUMNAS = [COL_ANIO, COL_MES, COL_DIA, COL_HORA, COL_SEXO, COL_DEPTO]

MESES = [
    "enero", "febrero", "marzo", "abril", "mayo", "junio",
    "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre",
]
DIAS = ["lunes", "martes", "miércoles", "jueves", "viernes", "sábado", "domingo"]
FRANJAS = [
    "00:00 a 02:59", "03:00 a 05:59", "06:00 a 08:59", "09:00 a 11:59",
    "12:00 a 14:59", "15:00 a 17:59", "18:00 a 20:59", "21:00 a 23:59",
]
SIN_INFO = "Sin información"

# El mismo departamento aparece escrito de dos formas en los datos
CORRECCION_DEPTOS = {"Bogotá D.C.": "Bogotá, D.C.", "Quindio": "Quindío"}

_datos = None


def cargar_datos():
    """Lee el CSV una sola vez (solo 6 columnas) y normaliza las variables de tiempo."""
    global _datos
    if _datos is not None:
        return _datos

    df = pd.read_csv(RUTA_DATOS, usecols=COLUMNAS)

    # Meses y días vienen en mayúscula y minúscula ("Enero" y "enero")
    df["mes"] = df[COL_MES].astype(str).str.strip().str.lower()
    df["dia"] = df[COL_DIA].astype(str).str.strip().str.lower()

    # Las franjas vienen como "(18:00 a 20:59)", "18:00 a 20:59" o "09:00 A 11:59"
    df["franja"] = (
        df[COL_HORA].astype(str).str.strip().str.strip("()")
        .str.replace(" A ", " a ", regex=False)
    )
    df.loc[~df["franja"].isin(FRANJAS), "franja"] = SIN_INFO

    df["anio"] = df[COL_ANIO].astype(int)
    df["sexo"] = df[COL_SEXO].fillna(SIN_INFO)
    df["departamento"] = df[COL_DEPTO].fillna(SIN_INFO).replace(CORRECCION_DEPTOS)

    # Tipo "category" para que ocupe poca memoria en el servidor
    _datos = df[["anio", "mes", "dia", "franja", "sexo", "departamento"]].astype(
        {"mes": "category", "dia": "category", "franja": "category",
         "sexo": "category", "departamento": "category"}
    )
    return _datos


def formato(numero):
    """12345 -> '12.345' (formato colombiano)."""
    return f"{int(numero):,}".replace(",", ".")


def porcentaje(valor):
    return f"{valor:.1f}".replace(".", ",") + " %"


def tablero_temporal(parametros):
    """Recibe los filtros de la URL (request.args) y devuelve todo lo que usa la plantilla."""
    df = cargar_datos()

    sexos = [s for s in ("Hombre", "Mujer", "Indeterminado") if s in set(df["sexo"])]
    departamentos = sorted(d for d in df["departamento"].unique() if d != SIN_INFO)

    sexo = parametros.get("sexo", "Todos")
    if sexo not in sexos:
        sexo = "Todos"
    depto = parametros.get("departamento", "Todos")
    if depto not in departamentos:
        depto = "Todos"

    datos = df
    if sexo != "Todos":
        datos = datos[datos["sexo"] == sexo]
    if depto != "Todos":
        datos = datos[datos["departamento"] == depto]

    total = len(datos)
    anios = list(range(int(df["anio"].min()), int(df["anio"].max()) + 1))

    # ---------- Serie anual y variación entre años ----------
    por_anio = datos.groupby("anio").size().reindex(anios, fill_value=0)
    variacion = (por_anio.pct_change() * 100).replace([float("inf"), -float("inf")], None)
    tabla_anios = []
    for anio in anios:
        cambio = variacion.get(anio)
        tabla_anios.append({
            "anio": anio,
            "casos": formato(por_anio[anio]),
            "variacion": None if pd.isna(cambio) else round(float(cambio), 1),
        })

    # ---------- Serie mensual (suma de todos los años) ----------
    por_mes = datos[datos["mes"].isin(MESES)].groupby("mes", observed=True).size()
    por_mes = por_mes.reindex(MESES, fill_value=0)

    # ---------- Día de la semana ----------
    por_dia = datos[datos["dia"].isin(DIAS)].groupby("dia", observed=True).size()
    por_dia = por_dia.reindex(DIAS, fill_value=0)

    # ---------- Día x franja horaria (solo registros con hora conocida) ----------
    con_hora = datos[(datos["franja"] != SIN_INFO) & (datos["dia"].isin(DIAS))]
    cruce = (
        pd.crosstab(con_hora["dia"].astype(str), con_hora["franja"].astype(str))
        .reindex(index=DIAS, columns=FRANJAS, fill_value=0)
    )
    maximo_celda = int(cruce.values.max()) if cruce.size else 0
    mapa_calor = []
    for dia in DIAS:
        fila = []
        for franja in FRANJAS:
            valor = int(cruce.loc[dia, franja])
            intensidad = valor / maximo_celda if maximo_celda else 0
            fila.append({"valor": formato(valor), "intensidad": round(intensidad, 3)})
        mapa_calor.append({"dia": dia.capitalize(), "celdas": fila})
    pct_sin_hora = (1 - len(con_hora) / total) * 100 if total else 0

    # ---------- Comparación entre periodos ----------
    mitad = anios[len(anios) // 2]  # 2020
    periodo_1 = por_anio[por_anio.index < mitad]
    periodo_2 = por_anio[por_anio.index >= mitad]
    prom_1 = periodo_1.mean() if len(periodo_1) else 0
    prom_2 = periodo_2.mean() if len(periodo_2) else 0
    cambio_periodos = ((prom_2 - prom_1) / prom_1 * 100) if prom_1 else 0

    # ---------- Indicadores ----------
    hay_datos = total > 0
    anio_max = int(por_anio.idxmax()) if hay_datos else None
    anio_min = int(por_anio.idxmin()) if hay_datos else None
    primero, ultimo = por_anio.iloc[0], por_anio.iloc[-1]
    variacion_total = ((ultimo - primero) / primero * 100) if primero else 0
    mes_max = por_mes.idxmax() if por_mes.sum() else "Sin datos"
    mes_min = por_mes.idxmin() if por_mes.sum() else "Sin datos"
    dia_max = por_dia.idxmax() if por_dia.sum() else "Sin datos"
    fin_semana = (por_dia["sábado"] + por_dia["domingo"]) / por_dia.sum() * 100 if por_dia.sum() else 0
    franjas_conocidas = con_hora["franja"].astype(str).value_counts()
    noche = (
        (franjas_conocidas.get("18:00 a 20:59", 0) + franjas_conocidas.get("21:00 a 23:59", 0))
        / franjas_conocidas.sum() * 100 if franjas_conocidas.sum() else 0
    )

    indicadores = {
        "total": formato(total),
        "anio_max": anio_max,
        "anio_max_casos": formato(por_anio.max()) if hay_datos else "0",
        "anio_min": anio_min,
        "anio_min_casos": formato(por_anio.min()) if hay_datos else "0",
        "variacion_total": round(float(variacion_total), 1),
        "primer_anio": anios[0],
        "ultimo_anio": anios[-1],
        "mes_max": mes_max.capitalize(),
        "mes_max_casos": formato(por_mes.max()),
        "dia_max": dia_max.capitalize(),
        "fin_semana": porcentaje(fin_semana),
    }

    # ---------- Interpretaciones (se recalculan con los filtros) ----------
    mayor_salto = variacion.dropna()
    if hay_datos and len(mayor_salto):
        anio_salto = int(mayor_salto.idxmax())
        anio_caida = int(mayor_salto.idxmin())
        texto_anual = (
            f"Entre {anios[0]} y {anios[-1]} los casos pasaron de {formato(primero)} a "
            f"{formato(ultimo)} ({'+' if variacion_total >= 0 else ''}{porcentaje(variacion_total)}). "
            f"El año con más víctimas fue {anio_max} ({formato(por_anio.max())}) y el de menos fue "
            f"{anio_min} ({formato(por_anio.min())}). El mayor aumento anual se dio en {anio_salto} "
            f"({'+' if mayor_salto.max() >= 0 else ''}{porcentaje(mayor_salto.max())}) y la mayor "
            f"disminución en {anio_caida} ({porcentaje(mayor_salto.min())})."
        )
    else:
        texto_anual = "No hay registros para la combinación de filtros seleccionada."

    if por_mes.sum():
        texto_mensual = (
            f"Sumando los {len(anios)} años, {mes_max} concentra la mayor cantidad de víctimas "
            f"({formato(por_mes.max())}) y {mes_min} la menor ({formato(por_mes.min())}). "
            f"La diferencia entre ambos es de {porcentaje((por_mes.max() - por_mes.min()) / por_mes.min() * 100 if por_mes.min() else 0)}. "
            "Febrero tiene menos días, por eso conviene compararlo con cuidado."
        )
    else:
        texto_mensual = "No hay registros para la combinación de filtros seleccionada."

    if por_dia.sum():
        texto_semanal = (
            f"El día con más víctimas es el {dia_max} ({formato(por_dia.max())}). Sábado y domingo "
            f"son 2 de los 7 días de la semana (28,6 %), pero reúnen el {porcentaje(fin_semana)} de los casos."
        )
    else:
        texto_semanal = "No hay registros para la combinación de filtros seleccionada."

    if len(con_hora):
        celda = cruce.stack().idxmax()
        texto_horario = (
            f"Entre los registros con hora conocida, el {porcentaje(noche)} ocurrió entre las 18:00 y "
            f"las 23:59. La combinación más frecuente es {celda[0]} de {celda[1]} "
            f"({formato(cruce.stack().max())} casos). Ojo: el {porcentaje(pct_sin_hora)} de los "
            "registros filtrados no tiene hora, así que este mapa describe solo una parte de los datos."
        )
    else:
        texto_horario = "No hay registros con hora conocida para la combinación de filtros seleccionada."

    texto_periodos = (
        f"El promedio anual de {anios[0]}–{mitad - 1} fue de {formato(round(prom_1))} víctimas y el de "
        f"{mitad}–{anios[-1]} fue de {formato(round(prom_2))}, un cambio de "
        f"{'+' if cambio_periodos >= 0 else ''}{porcentaje(cambio_periodos)} entre los dos quinquenios."
    )

    graficas = {
        "anual": {"etiquetas": anios, "valores": [int(v) for v in por_anio]},
        "mensual": {"etiquetas": [m.capitalize() for m in MESES], "valores": [int(v) for v in por_mes]},
        "semanal": {"etiquetas": [d.capitalize() for d in DIAS], "valores": [int(v) for v in por_dia]},
    }

    return {
        "sexos_disponibles": sexos,
        "departamentos_disponibles": departamentos,
        "sexo_seleccionado": sexo,
        "departamento_seleccionado": depto,
        "hay_filtros": sexo != "Todos" or depto != "Todos",
        "indicadores": indicadores,
        "tabla_anios": tabla_anios,
        "mapa_calor": mapa_calor,
        "franjas": FRANJAS,
        "periodos": {
            "etiqueta_1": f"{anios[0]}–{mitad - 1}",
            "etiqueta_2": f"{mitad}–{anios[-1]}",
            "promedio_1": formato(round(prom_1)),
            "promedio_2": formato(round(prom_2)),
            "cambio": round(float(cambio_periodos), 1),
        },
        "interpretaciones": {
            "anual": texto_anual,
            "mensual": texto_mensual,
            "semanal": texto_semanal,
            "horario": texto_horario,
            "periodos": texto_periodos,
        },
        "graficas": graficas,
    }
