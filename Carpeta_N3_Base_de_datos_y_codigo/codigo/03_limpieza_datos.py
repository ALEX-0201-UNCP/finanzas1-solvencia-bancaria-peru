# 1. Chancha Santiago Alex Omar
# 2. 2024200492K
# 3. Script Maestro: Consolidación Final - Panel 15 Bancos (SBS + API)

import os
import glob
import pandas as pd
import numpy as np

# Detección segura de directorios
try:
    DIR_ACTUAL = os.path.dirname(os.path.abspath(__file__))
except NameError:
    DIR_ACTUAL = os.getcwd()

if os.path.basename(DIR_ACTUAL).lower() == "codigo":
    DIR_BASE = os.path.dirname(DIR_ACTUAL)
else:
    DIR_BASE = DIR_ACTUAL

DIR_SBS = os.path.join(DIR_BASE, "datos_crudos", "sbs_ratio_capital_global")
RUTA_API = os.path.join(DIR_BASE, "datos_crudos", "datos_crudos_api.csv")
RUTA_SALIDA_PANEL_CSV = os.path.join(DIR_BASE, "datos_procesados", "datos_panel_15_bancos_2024200492K.csv")
RUTA_SALIDA_PANEL_XLSX = os.path.join(DIR_BASE, "datos_procesados", "datos_panel_15_bancos_2024200492K.xlsx")

def convertir_a_float(val):
    if pd.isna(val):
        return 0.0
    if isinstance(val, (int, float)):
        return float(val)
    s = str(val).strip().replace(',', '')
    try:
        return float(s)
    except:
        return 0.0

def procesar_panel_maestro():
    print("=" * 60)
    print("=== INICIANDO PROCESAMIENTO MAESTRO DEL PANEL FINANCIERO ===")
    print("=" * 60)
    
    archivos_xls = sorted(glob.glob(os.path.join(DIR_SBS, "*.xls*")))
    if not archivos_xls:
        print(f"[ERROR CRÍTICO] No se encontraron archivos en: {DIR_SBS}")
        return

    print(f"-> Total de reportes mensuales SBS encontrados: {len(archivos_xls)}")
    registros = []
    exitos = 0

    # 1. Extracción de los reportes mensuales de la SBS
    for archivo in archivos_xls:
        try:
            ext = os.path.splitext(archivo)[1].lower()
            engine = 'xlrd' if 'xls' in ext and 'xlsx' not in ext else 'openpyxl'
            df_raw = pd.read_excel(archivo, sheet_name=0, header=None, engine=engine)
            
            # Extracción de fecha interna de los reportes
            fecha_str = None
            for r in range(min(6, len(df_raw))):
                val_c = str(df_raw.iloc[r, 0])
                if "20" in val_c:
                    fecha_limpia = val_c.split()[0]
                    parsed = pd.to_datetime(fecha_limpia, errors='coerce')
                    if not pd.isna(parsed):
                        fecha_str = parsed.strftime('%Y-%m-%d')
                        break
            
            if not fecha_str:
                continue

            # Recorrido de filas institucionales de bancos (desde la fila 11)
            for idx in range(11, len(df_raw)):
                val_empresa = str(df_raw.iloc[idx, 0]).strip()
                if not val_empresa or val_empresa.lower() == 'nan':
                    continue
                if any(x in val_empresa.upper() for x in ["TOTAL", "SISTEMA", "FUENTE", "NOTA"]):
                    break
                
                nums = [convertir_a_float(df_raw.iloc[idx, c]) for c in range(1, df_raw.shape[1])]
                
                # Mapeo exacto de las 5 variables sustantivas exigidas por el temario:
                ratio_global = nums[-1] if len(nums) >= 1 else 0.0
                patrimonio = nums[-2] if len(nums) >= 2 else 0.0
                apr_total = nums[-3] if len(nums) >= 3 else 0.0
                roe = nums[-4] if len(nums) >= 4 else 0.0
                cartera_atrasada = nums[-5] if len(nums) >= 5 else 0.0
                
                registros.append({
                    'fecha': fecha_str,
                    'banco': val_empresa,
                    'patrimonio_efectivo': patrimonio,
                    'apr_total': apr_total,
                    'ratio_capital_global': ratio_global,
                    'roe': roe,
                    'cartera_atrasada': cartera_atrasada
                })
            exitos += 1
        except Exception:
            continue

    df_panel = pd.DataFrame(registros)
    if df_panel.empty:
        print("\n[ERROR CRÍTICO] El DataFrame generado está vacío.")
        return

    df_panel = df_panel.drop_duplicates(subset=['fecha', 'banco']).reset_index(drop=True)

    # 2. Integración de variables del API / Banco Mundial (cruce anual con datos mensuales)
    if os.path.exists(RUTA_API):
        print("-> Fusionando variables macroeconómicas (API / Banco Mundial) por año...")
        df_api = pd.read_csv(RUTA_API)
        df_api['anio'] = pd.to_datetime(df_api['fecha'], errors='coerce').dt.year
        df_panel['anio'] = pd.to_datetime(df_panel['fecha'], errors='coerce').dt.year
        
        df_panel = pd.merge(df_panel, df_api.drop(columns=['fecha']), on=['anio'], how='left')
        df_panel = df_panel.drop(columns=['anio'])
    else:
        print("-> [Aviso] Archivo 'datos_crudos_api.csv' no detectado. Se mantiene solo con información SBS.")

    # 3. Filtrado estricto para conservar únicamente a los 15 bancos comerciales de la banca múltiple
    patron_bancos = "Crédito|BCP|BBVA|Continental|Interbank|Scotiabank|GNB|Falabella|Ripley|Comercio|Citibank|Cencosud|ICBC|Alfin|Mibanco|Financiero|BanBif|Interamericano"
    df_panel = df_panel[df_panel['banco'].str.contains(patron_bancos, case=False, na=False)].copy()

    # 4. Exportación de resultados finales en formatos CSV y Excel
    os.makedirs(os.path.dirname(RUTA_SALIDA_PANEL_CSV), exist_ok=True)
    df_panel.to_csv(RUTA_SALIDA_PANEL_CSV, index=False)
    df_panel.to_excel(RUTA_SALIDA_PANEL_XLSX, index=False)
    
    print("\n" + "=" * 60)
    print("=== ¡PROCESAMIENTO EXITOSO! ===")
    print(f"Archivos SBS procesados: {exitos} / {len(archivos_xls)}")
    print(f"Total de observaciones del panel depurado: {len(df_panel)}")
    print(f"Bancos comerciales únicos: {df_panel['banco'].nunique()}")
    print(f"Variables finales incluidas: {df_panel.columns.tolist()}")
    print(f"Ruta CSV:   {RUTA_SALIDA_PANEL_CSV}")
    print(f"Ruta XLSX:  {RUTA_SALIDA_PANEL_XLSX}")
    print("=" * 60)

if __name__ == '__main__':
    procesar_panel_maestro()