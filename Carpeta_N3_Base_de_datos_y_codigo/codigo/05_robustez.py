# ============================================================================
# UNIVERSIDAD NACIONAL DEL CENTRO DEL PERÚ
# Facultad de Economía — Escuela Profesional de Economía
# Finanzas I (055D) — Ciclo V — Periodo 2026-II
# ----------------------------------------------------------------------------
# Nombres y apellidos : Chancha Santiago Alex Omar
# Código de matrícula : 2024200492K
# Tema N.º 9 (Unidad I): Solvencia bancaria en el Perú — ratio de capital
#                        global y activos ponderados por riesgo (APR)
# ----------------------------------------------------------------------------
# 05_robustez.py
#
# Ejecutar DESPUÉS de 03_limpieza_datos.py (usa el mismo panel que 04).
# Genera en /salidas:
#   - tabla7_evolucion_anual.csv/.xlsx     (evolución anual de los indicadores)
#   - tabla8_promedios_por_banco.csv/.xlsx (promedios por banco)
#   - tabla9_robustez.csv/.xlsx y .txt     (modelo de efectos fijos en 7 variantes)
#   - figura5_roe_cartera_evolucion.png    (medianas mensuales de ROE y cartera)
#   - figura6_rcg_por_banco.png            (RCG promedio por banco)
#   - figura7_robustez_cartera.png         (coeficiente de cartera, IC 95 %)
#
# Variantes del modelo de efectos fijos por banco (errores agrupados por banco):
#   Base, (a) sin winsorizar, (b) sin Bank of China, (c) sin Alfin Banco,
#   (d) 2018-2022, (e) 2023-2025, (f) sin 2020-2021.
# ============================================================================

import os
import sys
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

try:
    from linearmodels.panel import PanelOLS
    from scipy import stats as sp_stats
except ImportError as error:
    sys.exit(f"\n[ERROR] Falta una librería. Corre: pip install -r requirements.txt\nDetalle: {error}\n")


def obtener_directorio_base():
    try:
        dir_actual = os.path.dirname(os.path.abspath(__file__))
    except NameError:
        dir_actual = os.getcwd()
    if os.path.basename(dir_actual).lower() == "codigo":
        return os.path.dirname(dir_actual)
    return dir_actual


DIR_BASE = obtener_directorio_base()
RUTA_PANEL = os.path.join(DIR_BASE, "datos_procesados", "datos_procesados_2024200492K.csv")
DIR_SALIDAS = os.path.join(DIR_BASE, "salidas")
os.makedirs(DIR_SALIDAS, exist_ok=True)

VARIABLE_Y = "ratio_capital_global_pct"
VARIABLES_X = ["roe_pct", "cartera_atrasada_pct", "ln_apr_total_soles"]
PERCENTILES_WINSOR = (0.01, 0.99)
VARIABLES_WINSOR = ["ratio_capital_global_pct", "roe_pct"]
AZUL = "#1f4e79"

plt.rcParams.update({"figure.dpi": 120, "font.size": 10,
                     "axes.spines.top": False, "axes.spines.right": False})


def cargar_panel(winsorizar=True):
    df = pd.read_csv(RUTA_PANEL, encoding="utf-8-sig")
    df["fecha"] = pd.to_datetime(df["fecha"])
    df["ln_apr_total_soles"] = np.log(df["apr_total_soles"])
    if winsorizar:
        for columna in VARIABLES_WINSOR:
            inferior, superior = df[columna].quantile(list(PERCENTILES_WINSOR))
            df[columna] = df[columna].clip(lower=inferior, upper=superior)
    return df.sort_values(["banco", "fecha"]).reset_index(drop=True)


def guardar_tabla(df, nombre_base, incluir_index=True):
    df.to_csv(os.path.join(DIR_SALIDAS, f"{nombre_base}.csv"), index=incluir_index, encoding="utf-8-sig")
    df.to_excel(os.path.join(DIR_SALIDAS, f"{nombre_base}.xlsx"), index=incluir_index)
    print(f"Guardado: {nombre_base}.csv / .xlsx")


# ----------------------------------------------------------------------------
# Tablas descriptivas complementarias
# ----------------------------------------------------------------------------
def tabla_evolucion_anual(df):
    d = df.copy()
    d["patrimonio_efectivo"] = d[VARIABLE_Y] * d["apr_total_soles"] / 100
    agregado = d.groupby("fecha")[["patrimonio_efectivo", "apr_total_soles"]].sum()
    ratio_sistema = agregado["patrimonio_efectivo"] / agregado["apr_total_soles"] * 100
    diciembre = ratio_sistema[ratio_sistema.index.month == 12]
    diciembre.index = diciembre.index.year

    d["anio"] = d["fecha"].dt.year
    tabla = d.groupby("anio").agg(
        observaciones=("banco", "size"),
        rcg_mediana=(VARIABLE_Y, "median"),
        roe_mediana=("roe_pct", "median"),
        cartera_atrasada_mediana=("cartera_atrasada_pct", "median"),
    )
    tabla.insert(1, "rcg_sistema_diciembre", diciembre)
    tabla = tabla.round(2)
    guardar_tabla(tabla, "tabla7_evolucion_anual")
    print(tabla)
    return tabla


def tabla_promedios_por_banco(df):
    tabla = df.groupby("banco").agg(
        meses=("fecha", "count"),
        apr_promedio_millones=("apr_total_soles", "mean"),
        rcg_promedio=(VARIABLE_Y, "mean"),
        roe_promedio=("roe_pct", "mean"),
        cartera_atrasada_promedio=("cartera_atrasada_pct", "mean"),
    )
    tabla["apr_promedio_millones"] = tabla["apr_promedio_millones"] / 1000
    tabla = tabla.sort_values("apr_promedio_millones", ascending=False).round(2)
    guardar_tabla(tabla, "tabla8_promedios_por_banco")
    print(tabla)
    return tabla


# ----------------------------------------------------------------------------
# Modelo de efectos fijos en distintas muestras
# ----------------------------------------------------------------------------
def estimar_efectos_fijos(df):
    panel = df.set_index(["banco", "fecha"])
    modelo = PanelOLS(panel[VARIABLE_Y], panel[VARIABLES_X], entity_effects=True, drop_absorbed=True)
    return modelo.fit(cov_type="clustered", cluster_entity=True)


def estrellas(p):
    return "***" if p < 0.01 else "**" if p < 0.05 else "*" if p < 0.10 else ""


def pruebas_robustez():
    base = cargar_panel(winsorizar=True)
    especificaciones = [
        ("Base", base),
        ("(a) Sin winsorizar", cargar_panel(winsorizar=False)),
        ("(b) Sin Bank of China", base[base["banco"] != "Bank of China"]),
        ("(c) Sin Alfin Banco", base[base["banco"] != "Alfin Banco"]),
        ("(d) 2018-2022", base[base["fecha"] < "2023-01-01"]),
        ("(e) 2023-2025", base[base["fecha"] >= "2023-01-01"]),
        ("(f) Sin 2020-2021", base[~base["fecha"].dt.year.isin([2020, 2021])]),
    ]

    filas, lineas = [], []
    for nombre, datos in especificaciones:
        res = estimar_efectos_fijos(datos)
        fila = {"especificacion": nombre, "observaciones": int(res.nobs),
                "bancos": int(datos["banco"].nunique()), "r2_within": round(float(res.rsquared_within), 4)}
        lineas.append(f"== {nombre} | obs = {int(res.nobs)} | bancos = {fila['bancos']} | R2 within = {fila['r2_within']}")
        for variable in VARIABLES_X:
            coef = float(res.params[variable])
            se = float(res.std_errors[variable])
            p = float(2 * sp_stats.norm.sf(abs(coef / se)))
            fila[f"{variable}_coef"] = coef
            fila[f"{variable}_se"] = se
            fila[f"{variable}_p"] = p
            lineas.append(f"   {variable:24s} {coef:12.5f}{estrellas(p):3s} ({se:.5f})  p = {p:.4f}")
        filas.append(fila)

    tabla = pd.DataFrame(filas).set_index("especificacion")
    guardar_tabla(tabla, "tabla9_robustez")
    texto = "\n".join(lineas) + "\n\nEfectos fijos por banco; errores estándar agrupados por banco.\n* p<0.10, ** p<0.05, *** p<0.01\n"
    with open(os.path.join(DIR_SALIDAS, "tabla9_robustez.txt"), "w", encoding="utf-8") as f:
        f.write(texto)
    print(texto)
    return tabla


# ----------------------------------------------------------------------------
# Figuras complementarias
# ----------------------------------------------------------------------------
def figura_roe_cartera(df):
    medianas = df.groupby("fecha")[["roe_pct", "cartera_atrasada_pct"]].median()
    fig, ejes = plt.subplots(2, 1, figsize=(10, 6.2), sharex=True)
    ejes[0].plot(medianas.index, medianas["roe_pct"], color=AZUL, lw=1.8)
    ejes[0].set_ylabel("ROE anualizado (%)")
    ejes[0].set_title("ROE anualizado: mediana entre bancos", loc="left", fontsize=10)
    ejes[1].plot(medianas.index, medianas["cartera_atrasada_pct"], color=AZUL, lw=1.8)
    ejes[1].set_ylabel("Cartera atrasada (%)")
    ejes[1].set_title("Cartera atrasada: mediana entre bancos", loc="left", fontsize=10)
    ejes[1].set_xlabel("Fecha")
    for eje in ejes:
        eje.grid(alpha=0.3)
    fig.tight_layout()
    fig.savefig(os.path.join(DIR_SALIDAS, "figura5_roe_cartera_evolucion.png"))
    plt.close(fig)
    print("Guardado: figura5_roe_cartera_evolucion.png")


def figura_rcg_por_banco(df):
    promedios = df.groupby("banco")[VARIABLE_Y].mean().sort_values()
    fig, eje = plt.subplots(figsize=(9, 6))
    eje.barh(promedios.index, promedios.values, color=AZUL, height=0.6)
    eje.axvline(10, color="red", ls="--", lw=1, label="Referencia: 10%")
    for i, valor in enumerate(promedios.values):
        eje.text(valor + 0.4, i, f"{valor:.1f}".replace(".", ","), va="center", fontsize=9, color="#333")
    eje.set_xlabel("Ratio de capital global promedio 2018–2025 (%)")
    eje.grid(axis="x", alpha=0.3)
    eje.legend(loc="lower right")
    fig.tight_layout()
    fig.savefig(os.path.join(DIR_SALIDAS, "figura6_rcg_por_banco.png"))
    plt.close(fig)
    print("Guardado: figura6_rcg_por_banco.png")


def figura_robustez(tabla):
    nombres = [n.split(") ", 1)[-1] for n in tabla.index]
    coef = tabla["cartera_atrasada_pct_coef"].values
    se = tabla["cartera_atrasada_pct_se"].values
    y = np.arange(len(nombres))[::-1]
    fig, eje = plt.subplots(figsize=(8, 4.6))
    eje.axvline(0, color="#777", lw=1)
    eje.errorbar(coef, y, xerr=1.96 * se, fmt="o", color=AZUL, ecolor=AZUL, elinewidth=1.6, capsize=4, ms=6)
    eje.set_yticks(y)
    eje.set_yticklabels(nombres)
    eje.set_xlabel("Coeficiente de la cartera atrasada sobre el RCG (IC 95 %)")
    eje.grid(axis="x", alpha=0.3)
    fig.tight_layout()
    fig.savefig(os.path.join(DIR_SALIDAS, "figura7_robustez_cartera.png"))
    plt.close(fig)
    print("Guardado: figura7_robustez_cartera.png")


def main():
    df = cargar_panel(winsorizar=True)
    print(f"Panel: {len(df)} observaciones, {df['banco'].nunique()} bancos\n")
    tabla_evolucion_anual(df)
    tabla_promedios_por_banco(df)
    figura_roe_cartera(df)
    figura_rcg_por_banco(df)
    tabla = pruebas_robustez()
    figura_robustez(tabla)
    print(f"\nListo. Archivos guardados en: {DIR_SALIDAS}")


if __name__ == "__main__":
    main()