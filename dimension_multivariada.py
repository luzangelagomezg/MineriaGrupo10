"""
Dimensión relacional y multivariada (Integrante 4)

Pregunta: ¿Qué diferencias o relaciones evidentes pueden identificarse al
analizar conjuntamente tres o más variables?

Este módulo carga las columnas que se cruzan en el tablero, agrupa en pocas
categorías el mecanismo de la lesión y el escenario del hecho (que vienen
escritos de muchas formas) y calcula los indicadores, las gráficas, las
combinaciones más frecuentes y las combinaciones atípicas.
"""
import os
import unicodedata

import pandas as pd

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
RUTA_DATOS = os.path.join(BASE_DIR, "data", "presuntos_homicidios_2015_2024.csv")

# Columnas originales del conjunto de datos que usa esta dimensión
COLUMNAS = {
    "Año del hecho": "anio",
    "Sexo de la victima": "sexo",
    "Ciclo Vital": "ciclo",
    "Dia del hecho": "dia",
    "Código Dane Departamento": "cod_depto",
    "Departamento del hecho DANE": "departamento",
    "Zona del Hecho": "zona",
    "Escenario del Hecho": "escenario",
    "Mecanismo Causal de la Lesión Fatal": "mecanismo",
    "Circunstancia del Hecho Detallada": "circunstancia",
}

SIN_INFO = "Sin información"
SEXOS = ["Hombre", "Mujer"]
CICLOS = [
    "(00 a 05) Primera Infancia",
    "(06 a 11) Infancia",
    "(12 a 17) Adolescencia",
    "(18 a 28) Juventud",
    "(29 a 59) Adultez",
    "(Más de 60) Adulto Mayor",
]
DIAS = ["lunes", "martes", "miércoles", "jueves", "viernes", "sábado", "domingo"]
FIN_DE_SEMANA = {"sábado", "domingo"}
ZONAS = ["Cabecera municipal", "Centro poblado", "Parte rural"]

FUEGO = "Arma de fuego"
CORTO = "Arma cortopunzante"
MECANISMOS = [FUEGO, CORTO, "Contundente", "Asfixia", "Explosivo", "Otro / por determinar"]

VIA = "Vía pública"
VIVIENDA = "Vivienda"
ESCENARIOS = [VIA, VIVIENDA, "Espacio abierto o rural", "Establecimiento", "Otro / sin información"]

MINIMO_INTERPRETACION = 300

_datos = None


def _clave(texto):
    """'Vía Pública' -> 'viapublica': sin tildes, mayúsculas ni espacios."""
    texto = unicodedata.normalize("NFKD", str(texto).lower())
    return "".join(c for c in texto if not unicodedata.combining(c)).replace(" ", "")


def _mecanismo(valor):
    """Agrupa las 24 formas de escribir el mecanismo en 6 categorías."""
    c = _clave(valor)
    if "fuego" in c:
        return FUEGO
    if c in ("cortopunzante", "cortante", "punzante"):
        return CORTO
    if "contundente" in c:
        return "Contundente"
    if "asfixia" in c or "extrangul" in c:
        return "Asfixia"
    if "explosiv" in c:
        return "Explosivo"
    return "Otro / por determinar"


def _escenario(valor):
    """Agrupa los 72 escenarios del hecho en 5 categorías."""
    c = _clave(valor)
    if "viapublica" in c or c.startswith(("calle", "carretera")) or "lugarpublico" in c:
        return VIA
    if c == "vivienda":
        return VIVIENDA
    if "airelibre" in c or "agropecuaria" in c or "baldio" in c or "minas" in c:
        return "Espacio abierto o rural"
    if "sininformacion" in c or c == "otros":
        return "Otro / sin información"
    return "Establecimiento"


def _zona(valor):
    for zona in ZONAS:
        if str(valor).startswith(zona):
            return zona
    return SIN_INFO


def _nombre_por_codigo(df, codigo, nombre):
    """Unifica 'Bogotá D.C.' y 'Bogotá, D.C.' (mismo criterio de la dimensión territorial)."""
    nombres = df.groupby(codigo)[nombre].agg(lambda s: s.value_counts().index[0])
    return df[codigo].map(nombres)


def cargar_datos():
    """Lee el CSV una sola vez (solo 10 columnas) y normaliza las categorías."""
    global _datos
    if _datos is not None:
        return _datos

    df = pd.read_csv(RUTA_DATOS, usecols=list(COLUMNAS)).rename(columns=COLUMNAS)
    df["departamento"] = _nombre_por_codigo(df, "cod_depto", "departamento")
    df["mecanismo"] = df["mecanismo"].map(_mecanismo)
    df["escenario"] = df["escenario"].map(_escenario)
    df["zona"] = df["zona"].map(_zona)
    df["dia"] = df["dia"].str.strip().str.lower()
    df["circunstancia"] = df["circunstancia"].str.strip().str.lower()
    df["sexo"] = df["sexo"].fillna(SIN_INFO)

    columnas = ["anio", "sexo", "ciclo", "dia", "departamento", "zona", "escenario", "mecanismo", "circunstancia"]
    _datos = df[columnas].astype({c: "category" for c in columnas if c != "anio"})
    return _datos


# ---------- Formatos (colombianos) ----------
def formato(numero):
    return f"{int(numero):,}".replace(",", ".")


def porcentaje(valor):
    return f"{valor:.1f}".replace(".", ",") + " %"


def veces(valor):
    return f"{valor:.1f}".replace(".", ",")


def _pct(parte, total):
    return parte / total * 100 if total else 0.0


def _ciclo_corto(ciclo):
    """'(18 a 28) Juventud' -> 'Juventud'."""
    return str(ciclo).split(") ")[-1]


# ---------- Cálculos del tablero ----------
def _mecanismo_por_sexo_y_escenario(datos):
    """Visualización 1: % de cada mecanismo dentro de cada combinación sexo × escenario."""
    base = datos[datos["sexo"].isin(SEXOS) & (datos["escenario"] != "Otro / sin información")]
    tabla = pd.crosstab(
        [base["sexo"].astype(str), base["escenario"].astype(str)],
        base["mecanismo"].astype(str),
    )
    etiquetas, filas, totales = [], [], []
    for sexo in SEXOS:
        for escenario in ESCENARIOS[:4]:
            if (sexo, escenario) in tabla.index:
                fila = tabla.loc[(sexo, escenario)]
                etiquetas.append(f"{sexo} · {escenario}")
                filas.append(fila)
                totales.append(int(fila.sum()))
    series = [
        {
            "nombre": m,
            "valores": [round(_pct(f.get(m, 0), f.sum()), 1) for f in filas],
        }
        for m in MECANISMOS
    ]
    return {"etiquetas": etiquetas, "series": series, "totales": totales}


def _vivienda_por_ciclo_y_sexo(datos):
    """Visualización 2: % de víctimas asesinadas en la vivienda según ciclo vital y sexo."""
    base = datos[datos["sexo"].isin(SEXOS) & datos["ciclo"].isin(CICLOS)]
    tabla = pd.crosstab(
        [base["ciclo"].astype(str), base["sexo"].astype(str)],
        base["escenario"] == VIVIENDA,
    )
    series = []
    for sexo in SEXOS:
        valores, casos = [], []
        for ciclo in CICLOS:
            if (ciclo, sexo) in tabla.index:
                fila = tabla.loc[(ciclo, sexo)]
                total = int(fila.sum())
                valores.append(round(_pct(fila.get(True, 0), total), 1))
                casos.append(total)
            else:
                valores.append(None)
                casos.append(0)
        series.append({"nombre": sexo, "valores": valores, "casos": casos})
    return {"etiquetas": [_ciclo_corto(c) for c in CICLOS], "series": series}


def _mecanismo_por_dia(datos):
    """Visualización 3: víctimas por día de la semana y mecanismo (barras apiladas)."""
    base = datos[datos["dia"].isin(DIAS)]
    tabla = pd.crosstab(base["dia"].astype(str), base["mecanismo"].astype(str))
    tabla = tabla.reindex(index=DIAS, columns=MECANISMOS, fill_value=0)
    otros = tabla[MECANISMOS[2:]].sum(axis=1)
    return {
        "etiquetas": [d.capitalize() for d in DIAS],
        "series": [
            {"nombre": FUEGO, "valores": tabla[FUEGO].astype(int).tolist()},
            {"nombre": CORTO, "valores": tabla[CORTO].astype(int).tolist()},
            {"nombre": "Otros mecanismos", "valores": otros.astype(int).tolist()},
        ],
        "pct_corto": [round(_pct(tabla.loc[d, CORTO], tabla.loc[d].sum()), 1) for d in DIAS],
    }


def _combinaciones(datos, n=10):
    """Combinaciones sexo × ciclo vital × escenario × mecanismo con más registros."""
    total = len(datos)
    grupos = (
        datos.groupby(["sexo", "ciclo", "escenario", "mecanismo"], observed=True)
        .size()
        .sort_values(ascending=False)
        .head(n)
    )
    acumulado = 0
    filas = []
    for (sexo, ciclo, escenario, mecanismo), casos in grupos.items():
        acumulado += casos
        filas.append({
            "sexo": sexo,
            "ciclo": _ciclo_corto(ciclo),
            "escenario": escenario,
            "mecanismo": mecanismo,
            "casos": formato(casos),
            "porcentaje": porcentaje(_pct(casos, total)),
            "acumulado": porcentaje(_pct(acumulado, total)),
        })
    return filas


def _atipicos(datos, minimo=30, n=8):
    """Combinaciones atípicas: dentro de un grupo sexo × ciclo vital, un mecanismo
    que aparece al menos 3 veces más que en el total (razón ≥ 3, mínimo 30 casos)."""
    total = len(datos)
    if not total:
        return []
    general = datos["mecanismo"].value_counts(normalize=True)
    base = datos[datos["sexo"].isin(SEXOS) & datos["ciclo"].isin(CICLOS)]
    tabla = pd.crosstab([base["sexo"].astype(str), base["ciclo"].astype(str)], base["mecanismo"].astype(str))
    filas = []
    for (sexo, ciclo), fila in tabla.iterrows():
        grupo = fila.sum()
        for mecanismo, casos in fila.items():
            if casos < minimo or mecanismo == "Otro / por determinar" or general.get(mecanismo, 0) == 0:
                continue
            participacion = casos / grupo
            razon = participacion / general[mecanismo]
            if razon >= 3:
                filas.append({
                    "grupo": f"{sexo} · {_ciclo_corto(ciclo)}",
                    "mecanismo": mecanismo,
                    "casos": formato(casos),
                    "en_grupo": porcentaje(participacion * 100),
                    "en_total": porcentaje(general[mecanismo] * 100),
                    "razon": veces(razon),
                    "_orden": razon,
                })
    filas.sort(key=lambda f: f["_orden"], reverse=True)
    return filas[:n]


def tablero_multivariado(parametros):
    """Recibe los filtros de la URL (request.args) y devuelve todo lo que usa la plantilla."""
    df = cargar_datos()

    anios = sorted(int(a) for a in df["anio"].unique())
    departamentos = sorted(d for d in df["departamento"].unique() if d != SIN_INFO)

    anio = parametros.get("anio", "Todos")
    if not str(anio).isdigit() or int(anio) not in anios:
        anio = "Todos"
    depto = parametros.get("departamento", "Todos")
    if depto not in departamentos:
        depto = "Todos"
    zona = parametros.get("zona", "Todos")
    if zona not in ZONAS:
        zona = "Todos"

    datos = df
    if anio != "Todos":
        datos = datos[datos["anio"] == int(anio)]
    if depto != "Todos":
        datos = datos[datos["departamento"] == depto]
    if zona != "Todos":
        datos = datos[datos["zona"] == zona]

    total = len(datos)
    hay_datos = total > 0

    # ---------- Indicadores ----------
    hombres = datos[datos["sexo"] == "Hombre"]
    mujeres = datos[datos["sexo"] == "Mujer"]
    viv_h = _pct((hombres["escenario"] == VIVIENDA).sum(), len(hombres))
    viv_m = _pct((mujeres["escenario"] == VIVIENDA).sum(), len(mujeres))

    con_dia = datos[datos["dia"].isin(DIAS)]
    finde = con_dia[con_dia["dia"].isin(FIN_DE_SEMANA)]
    semana = con_dia[~con_dia["dia"].isin(FIN_DE_SEMANA)]
    corto_finde = _pct((finde["mecanismo"] == CORTO).sum(), len(finde))
    corto_semana = _pct((semana["mecanismo"] == CORTO).sum(), len(semana))
    # Riñas promedio por día: fin de semana (2 días) frente a entre semana (5 días)
    rinas_finde = (finde["circunstancia"] == "riña").sum() / 2
    rinas_semana = (semana["circunstancia"] == "riña").sum() / 5

    combinaciones = _combinaciones(datos)
    lider = combinaciones[0] if combinaciones else None

    indicadores = {
        "total": formato(total),
        "viv_mujeres": porcentaje(viv_m),
        "viv_hombres": porcentaje(viv_h),
        "brecha_vivienda": veces(viv_m / viv_h) if viv_h else "—",
        "combinacion": (
            f"{lider['sexo']} · {lider['ciclo']} · {lider['escenario']} · {lider['mecanismo']}"
            if lider else "Sin datos"
        ),
        "combinacion_pct": lider["porcentaje"] if lider else "0,0 %",
        "combinacion_casos": lider["casos"] if lider else "0",
        "corto_finde": porcentaje(corto_finde),
        "corto_semana": porcentaje(corto_semana),
        "rinas_razon": veces(rinas_finde / rinas_semana) if rinas_semana else "—",
    }

    graficas = {
        "sexo_escenario": _mecanismo_por_sexo_y_escenario(datos),
        "ciclo_vivienda": _vivienda_por_ciclo_y_sexo(datos),
        "dias": _mecanismo_por_dia(datos),
    }

    # ---------- Interpretaciones (se recalculan con los filtros) ----------
    # Con muy pocos registros los porcentajes cambian mucho con un solo caso
    muestra_pequena = total < MINIMO_INTERPRETACION
    vacio = (
        f"Con los filtros elegidos hay {formato(total)} registros; se necesitan al menos "
        f"{formato(MINIMO_INTERPRETACION)} para interpretar los porcentajes. Amplía los filtros."
    )

    g1 = graficas["sexo_escenario"]
    if not muestra_pequena and len(mujeres) and len(hombres):
        valores = {s["nombre"]: dict(zip(g1["etiquetas"], s["valores"])) for s in g1["series"]}
        m_viv = f"Mujer · {VIVIENDA}"
        h_via = f"Hombre · {VIA}"
        texto_1 = (
            f"El arma de fuego explica el {porcentaje(valores[FUEGO].get(h_via, 0))} de los hombres asesinados en la "
            f"vía pública, pero solo el {porcentaje(valores[FUEGO].get(m_viv, 0))} de las mujeres asesinadas en la "
            f"vivienda. En ese último grupo ganan peso el arma cortopunzante "
            f"({porcentaje(valores[CORTO].get(m_viv, 0))}), el mecanismo contundente "
            f"({porcentaje(valores['Contundente'].get(m_viv, 0))}) y la asfixia "
            f"({porcentaje(valores['Asfixia'].get(m_viv, 0))}), mecanismos que exigen contacto cercano con la víctima."
        )
    else:
        texto_1 = vacio

    g2 = graficas["ciclo_vivienda"]
    if not muestra_pequena:
        h_vals, m_vals = g2["series"][0]["valores"], g2["series"][1]["valores"]
        brechas = [
            (i, m_vals[i] - h_vals[i]) for i in range(len(CICLOS))
            if h_vals[i] is not None and m_vals[i] is not None
        ]
        maximo_m = max((i for i in range(len(CICLOS)) if m_vals[i] is not None), key=lambda i: m_vals[i], default=None)
        if brechas and maximo_m is not None:
            i_brecha, brecha = max(brechas, key=lambda b: b[1])
            texto_2 = (
                f"En todos los ciclos vitales con datos, la proporción de mujeres asesinadas en la vivienda supera o "
                f"iguala a la de los hombres. La brecha más amplia está en {g2['etiquetas'][i_brecha].lower()} "
                f"(mujeres {porcentaje(m_vals[i_brecha])} frente a hombres {porcentaje(h_vals[i_brecha])}; "
                f"{veces(brecha)} puntos). El valor más alto para las mujeres se da en "
                f"{g2['etiquetas'][maximo_m].lower()} ({porcentaje(m_vals[maximo_m])})."
            ) if all(b >= 0 for _, b in brechas) else (
                f"La brecha más amplia entre mujeres y hombres está en {g2['etiquetas'][i_brecha].lower()} "
                f"(mujeres {porcentaje(m_vals[i_brecha])} frente a hombres {porcentaje(h_vals[i_brecha])})."
            )
        else:
            texto_2 = vacio
    else:
        texto_2 = vacio

    g3 = graficas["dias"]
    if not muestra_pequena and len(con_dia):
        totales_dia = [sum(s["valores"][i] for s in g3["series"]) for i in range(7)]
        pico = max(range(7), key=lambda i: totales_dia[i])
        valle = min(range(7), key=lambda i: totales_dia[i])
        texto_3 = (
            f"{g3['etiquetas'][pico]} es el día con más víctimas ({formato(totales_dia[pico])}) y "
            f"{g3['etiquetas'][valle].lower()} el de menos ({formato(totales_dia[valle])}). El fin de semana también "
            f"cambia el mecanismo: el arma cortopunzante pasa del {porcentaje(corto_semana)} de las víctimas entre "
            f"semana al {porcentaje(corto_finde)} en sábado y domingo (domingo: {porcentaje(g3['pct_corto'][6])})."
        )
    else:
        texto_3 = vacio

    return {
        "anios_disponibles": anios,
        "departamentos_disponibles": departamentos,
        "zonas_disponibles": ZONAS,
        "anio_seleccionado": str(anio),
        "departamento_seleccionado": depto,
        "zona_seleccionada": zona,
        "hay_filtros": anio != "Todos" or depto != "Todos" or zona != "Todos",
        "muestra_pequena": muestra_pequena,
        "indicadores": indicadores,
        "combinaciones": combinaciones,
        "atipicos": [] if muestra_pequena else _atipicos(datos),
        "interpretaciones": {"sexo_escenario": texto_1, "ciclo_vivienda": texto_2, "dias": texto_3},
        "graficas": graficas,
    }
