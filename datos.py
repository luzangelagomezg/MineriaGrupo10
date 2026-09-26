"""Carga y limpieza básica del conjunto de datos compartido por las cuatro dimensiones."""
from functools import lru_cache
from pathlib import Path

import pandas as pd

RUTA_DATOS = Path(__file__).parent / "data" / "presuntos_homicidios_2015_2024.csv.gz"

# Nombres cortos para las columnas que se usan con más frecuencia
COLUMNAS = {
    "Año del hecho": "anio",
    "Mes del hecho": "mes",
    "Dia del hecho": "dia_semana",
    "Rango de Hora del Hecho X 3 Horas": "rango_hora",
    "Sexo de la victima": "sexo",
    "Grupo de edad quinquenal": "edad_quinquenal",
    "Ciclo Vital": "ciclo_vital",
    "Código Dane Departamento": "cod_departamento",
    "Departamento del hecho DANE": "departamento",
    "Código Dane Municipio": "cod_municipio",
    "Municipio del hecho DANE": "municipio",
    "Localidad del Hecho": "localidad",
    "Zona del Hecho": "zona",
    "Escenario del Hecho": "escenario",
    "Mecanismo Causal de la Lesión Fatal": "mecanismo",
    "Presunto Agresor Detallado": "agresor",
}


def _nombre_mas_frecuente(df, codigo, nombre):
    """Unifica los nombres que cambian de escritura entre años usando el código DANE."""
    canon = df.groupby(codigo)[nombre].agg(lambda s: s.value_counts().index[0])
    return df[codigo].map(canon)


@lru_cache(maxsize=1)
def cargar_datos():
    df = pd.read_csv(RUTA_DATOS, dtype=str, encoding="utf-8")
    df = df.rename(columns=COLUMNAS)
    df["anio"] = df["anio"].astype(int)

    # Ej.: "Bogotá D.C." / "Bogotá, D.C." o "Quindio" / "Quindío" comparten código DANE
    df["departamento"] = _nombre_mas_frecuente(df, "cod_departamento", "departamento")
    df["municipio"] = _nombre_mas_frecuente(df, "cod_municipio", "municipio")

    # "Centro poblado(corregimiento..." y "Centro poblado (corregimiento..." son la misma zona
    df["zona"] = df["zona"].str.replace(r"poblado\s*\(", "poblado (", regex=True)
    return df
