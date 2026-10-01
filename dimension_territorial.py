"""
Dimensión territorial (Integrante 2)

Pregunta: ¿Cómo se distribuye la población y sus principales características
entre los territorios disponibles?

Este módulo carga solo las columnas territoriales del conjunto de datos,
unifica los nombres de departamentos y municipios con su código DANE y
calcula los indicadores, las series de las gráficas y las interpretaciones
del tablero territorial.
"""
import os

import pandas as pd

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
RUTA_DATOS = os.path.join(BASE_DIR, "data", "presuntos_homicidios_2015_2024.csv")

# Columnas originales del conjunto de datos que usa esta dimensión
COLUMNAS = {
    "Año del hecho": "anio",
    "Sexo de la victima": "sexo",
    "Código Dane Departamento": "cod_depto",
    "Departamento del hecho DANE": "departamento",
    "Código Dane Municipio": "cod_mpio",
    "Municipio del hecho DANE": "municipio",
    "Zona del Hecho": "zona",
}

SIN_INFO = "Sin información"
RURAL = "Parte rural"
ZONAS = ["Cabecera municipal", "Centro poblado", RURAL, SIN_INFO]

_datos = None


def _nombre_por_codigo(df, codigo, nombre):
    """Cada código DANE queda con el nombre que más se repite.

    Así "Bogotá D.C." y "Bogotá, D.C." o "Quindio" y "Quindío" quedan
    como un solo territorio.
    """
    nombres = df.groupby(codigo)[nombre].agg(lambda s: s.value_counts().index[0])
    return df[codigo].map(nombres)


def _zona(valor):
    """Resume la zona: 'Centro poblado(corregimiento...' y 'Centro poblado (corregimiento...' son la misma."""
    for zona in ZONAS[:3]:
        if str(valor).startswith(zona):
            return zona
    return SIN_INFO


def cargar_datos():
    """Lee el CSV una sola vez (solo 7 columnas) y normaliza los territorios."""
    global _datos
    if _datos is not None:
        return _datos

    df = pd.read_csv(RUTA_DATOS, usecols=list(COLUMNAS)).rename(columns=COLUMNAS)
    df["departamento"] = _nombre_por_codigo(df, "cod_depto", "departamento")
    df["municipio"] = _nombre_por_codigo(df, "cod_mpio", "municipio")
    df["zona"] = df["zona"].map(_zona)
    df["sexo"] = df["sexo"].fillna(SIN_INFO)

    # Tipo "category" para que ocupe poca memoria en el servidor
    _datos = df[["anio", "sexo", "departamento", "cod_mpio", "municipio", "zona"]].astype(
        {"sexo": "category", "departamento": "category", "municipio": "category", "zona": "category"}
    )
    return _datos


def formato(numero):
    """12345 -> '12.345' (formato colombiano)."""
    return f"{int(numero):,}".replace(",", ".")


def porcentaje(valor):
    return f"{valor:.1f}".replace(".", ",") + " %"


def lista(nombres):
    """['a', 'b', 'c'] -> 'a, b y c'."""
    nombres = list(nombres)
    return nombres[0] if len(nombres) == 1 else ", ".join(nombres[:-1]) + " y " + nombres[-1]


def tablero_territorial(parametros):
    """Recibe los filtros de la URL (request.args) y devuelve todo lo que usa la plantilla."""
    df = cargar_datos()

    anios = sorted(int(a) for a in df["anio"].unique())
    sexos = [s for s in ("Hombre", "Mujer", "Indeterminado") if s in set(df["sexo"])]
    departamentos = sorted(d for d in df["departamento"].unique() if d != SIN_INFO)

    anio = parametros.get("anio", "Todos")
    if not str(anio).isdigit() or int(anio) not in anios:
        anio = "Todos"
    sexo = parametros.get("sexo", "Todos")
    if sexo not in sexos:
        sexo = "Todos"
    depto = parametros.get("departamento", "Todos")
    if depto not in departamentos:
        depto = "Todos"

    datos = df
    if anio != "Todos":
        datos = datos[datos["anio"] == int(anio)]
    if sexo != "Todos":
        datos = datos[datos["sexo"] == sexo]

    # ---------- Departamentos (siempre todo el país, para comparar) ----------
    por_depto = datos["departamento"].value_counts()
    por_depto = por_depto[por_depto.index != SIN_INFO]
    total_pais = len(datos)

    tabla_deptos = [
        {
            "posicion": i + 1,
            "departamento": d,
            "casos": formato(n),
            "porcentaje": porcentaje(n / total_pais * 100) if total_pais else "0,0 %",
            "seleccionado": d == depto,
        }
        for i, (d, n) in enumerate(por_depto.items())
    ]

    # ---------- Municipios (del departamento elegido o de todo el país) ----------
    ambito = datos[datos["departamento"] == depto] if depto != "Todos" else datos
    total = len(ambito)
    por_mpio = ambito.groupby(["cod_mpio", "municipio", "departamento"], observed=True).size()
    por_mpio = por_mpio.sort_values(ascending=False)
    nombres_mpio = [
        m if depto != "Todos" or m == d else f"{m} ({d})"
        for _, m, d in por_mpio.index
    ]
    mpios_mitad = int((por_mpio.cumsum() < total / 2).sum() + 1) if total else 0

    # ---------- Zona del hecho por departamento (% dentro de cada uno) ----------
    con_depto = datos[datos["departamento"] != SIN_INFO]
    zonas = pd.crosstab(con_depto["departamento"].astype(str), con_depto["zona"].astype(str), normalize="index") * 100
    zonas = zonas.reindex(columns=ZONAS, fill_value=0).sort_values(RURAL, ascending=False)
    rural_ambito = (ambito["zona"] == RURAL).sum() / total * 100 if total else 0

    # ---------- Indicadores ----------
    hay_datos = total > 0
    if depto != "Todos":
        lider = nombres_mpio[0] if hay_datos else "Sin datos"
        lider_casos = por_mpio.iloc[0] if hay_datos else 0
        top5 = por_mpio.head(5).sum()
    else:
        lider = por_depto.index[0] if hay_datos else "Sin datos"
        lider_casos = por_depto.iloc[0] if hay_datos else 0
        top5 = por_depto.head(5).sum()

    indicadores = {
        "total": formato(total),
        "ambito": depto if depto != "Todos" else "Colombia",
        "nivel": "municipio" if depto != "Todos" else "departamento",
        "municipios": formato(len(por_mpio)),
        "lider": lider,
        "lider_casos": formato(lider_casos),
        "lider_pct": porcentaje(lider_casos / total * 100 if total else 0),
        "top5": porcentaje(top5 / total * 100 if total else 0),
        "mpios_mitad": mpios_mitad,
        "rural": porcentaje(rural_ambito),
    }

    # ---------- Interpretaciones (se recalculan con los filtros) ----------
    vacio = "No hay registros para la combinación de filtros seleccionada."
    if total_pais:
        top3 = por_depto.head(3)
        menores = por_depto.tail(3)
        texto_deptos = (
            f"{lista(top3.index)} reúnen el {porcentaje(top3.sum() / total_pais * 100)} de los registros y los "
            f"cinco primeros departamentos el {porcentaje(por_depto.head(5).sum() / total_pais * 100)}. "
            f"En el otro extremo, {lista(menores.index)} tienen apenas {lista(formato(n) for n in menores)} registros."
        )
        rural = zonas[RURAL]
        mas_rural = rural.sort_values(ascending=False).head(3)
        mas_urbano = rural.sort_values().head(3)
        texto_zonas = (
            f"En {lista(f'{d} ({porcentaje(v)})' for d, v in mas_rural.items())} una gran parte de los casos "
            f"ocurre en la parte rural, mientras que en {lista(f'{d} ({porcentaje(v)})' for d, v in mas_urbano.items())} "
            "casi todos ocurren en cabeceras municipales."
        )
    else:
        texto_deptos = texto_zonas = vacio

    donde = f"en {depto}" if depto != "Todos" else "en el país"
    if hay_datos:
        texto_mpios = (
            f"{nombres_mpio[0]} es el municipio con más registros {donde} ({formato(por_mpio.iloc[0])}; "
            f"{porcentaje(por_mpio.iloc[0] / total * 100)}). Solo {mpios_mitad} de {formato(len(por_mpio))} municipios "
            f"con registros acumulan la mitad de los casos {donde}."
        )
    else:
        texto_mpios = vacio

    graficas = {
        "departamentos": {
            "etiquetas": por_depto.index.tolist()[:15],
            "valores": [int(v) for v in por_depto.values[:15]],
            "seleccionado": depto,
        },
        "municipios": {
            "etiquetas": nombres_mpio[:10],
            "valores": [int(v) for v in por_mpio.values[:10]],
        },
        "zonas": {
            "etiquetas": zonas.index.tolist(),
            "series": [{"nombre": z, "valores": zonas[z].round(1).tolist()} for z in ZONAS],
        },
    }

    return {
        "anios_disponibles": anios,
        "sexos_disponibles": sexos,
        "departamentos_disponibles": departamentos,
        "anio_seleccionado": str(anio),
        "sexo_seleccionado": sexo,
        "departamento_seleccionado": depto,
        "hay_filtros": anio != "Todos" or sexo != "Todos" or depto != "Todos",
        "indicadores": indicadores,
        "tabla_deptos": tabla_deptos,
        "variacion": variacion_departamentos(),
        "interpretaciones": {
            "departamentos": texto_deptos,
            "municipios": texto_mpios,
            "zonas": texto_zonas,
        },
        "graficas": graficas,
    }


def variacion_departamentos(n=12):
    """Registros 2015 vs 2024 de los n departamentos con más casos (evidencia del conocimiento 3)."""
    df = cargar_datos()
    tabla = pd.crosstab(df["departamento"].astype(str), df["anio"])
    principales = df["departamento"].value_counts().head(n).index.astype(str)
    tabla = tabla.loc[principales, [2015, 2024]]
    tabla["variacion"] = (tabla[2024] - tabla[2015]) / tabla[2015] * 100
    return [
        {"departamento": d, "a2015": formato(f[2015]), "a2024": formato(f[2024]),
         "variacion": round(float(f["variacion"]), 1)}
        for d, f in tabla.sort_values("variacion", ascending=False).iterrows()
    ]
