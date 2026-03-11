import os
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

# ============================================================
# PROFUNDIDADES POR TERMO CUPLA
# ============================================================
profundidades_tc = {
    "T1": {"Ssuperior": 0, "Sintermedio": 0.28, "Sinferior": 0.56},
    "T2": {"Ssuperior": 0, "Sintermedio": 0.20, "Sinferior": 0.40},
    "T3": {"Ssuperior": 0, "Sintermedio": 0.20, "Sinferior": 0.40},
    "T4": {"Ssuperior": 0, "Sintermedio": 0.28, "Sinferior": 0.56},
    "T5": {"Ssuperior": 0, "Sintermedio": 0.28, "Sinferior": 0.56},
}

# ============================================================
# FRECUENCIA DE TICKS POR TERMO CUPLA (HORAS) (CAMBIAR CADA VALOREQUIVALEA 12 horas)

# ============================================================
frecuencia_grafico = {
    "T1": 48,
    "T2": 4,
    "T3": 3,
    "T4": 48,
    "T5": 48,
}

# ============================================================
# LECTURA CSV IBUTTON
# ============================================================
def leer_ibutton_csv(ruta_archivo):

    datos = []

    with open(ruta_archivo, encoding="latin1") as f:
        for linea in f:

            linea = linea.strip()

            if not linea:
                continue

            if linea.startswith((
                "1-Wire", "Mission", "SUTA", "Waiting",
                "Sample", "Roll", "First", "Total",
                "Temperature", "Data", "Date/Time"
            )):
                continue

            partes = linea.split(",", 2)
            if len(partes) != 3:
                continue

            try:
                fecha = partes[0]
                valor = float(partes[2].replace(",", "."))
                datos.append([fecha, valor])
            except:
                continue

    if len(datos) == 0:
        return pd.DataFrame(columns=["datetime", "temperatura"])

    df = pd.DataFrame(datos, columns=["datetime", "temperatura"])
    df["datetime"] = pd.to_datetime(df["datetime"], format="%d-%m-%y %H:%M:%S")

    return df


# ============================================================
# GENERAR EXCEL + TXT ORDEN
# ============================================================
def generar_excel_separado(tabla_filtrada, ruta_carpeta, nombre_tc, T_objetivo):

    columnas_excel = []
    lineas_txt = []
    orden_niveles = ["Ssuperior", "Sintermedio", "Sinferior"]
    contador = 1

    for nivel in orden_niveles:

        if nivel not in tabla_filtrada:
            continue

        df_nivel = tabla_filtrada[nivel].copy().reset_index(drop=True)

        if df_nivel.empty:
            continue

        df_temp = pd.DataFrame({
            f"fecha{contador}": df_nivel["datetime"],
            f"temp{contador}": df_nivel["temperatura"]
        })

        columnas_excel.append(df_temp)

        profundidad = profundidades_tc[T_objetivo][nivel]

        lineas_txt.append(
            f"fecha{contador} - temp{contador} → {nivel} ({profundidad:.2f} m)"
        )

        contador += 1

    if len(columnas_excel) == 0:
        print("⚠ No hay datos válidos para exportar.")
        return

    df_final = pd.concat(columnas_excel, axis=1)

    # Guardar Excel
    ruta_excel = os.path.join(
        ruta_carpeta,
        f"datos_filtrados_{nombre_tc}.xlsx"
    )

    df_final.to_excel(ruta_excel, index=False)
    print(f"✔ Excel generado: {ruta_excel}")

    # Guardar TXT
    ruta_txt = os.path.join(
        ruta_carpeta,
        f"orden_sensores_{nombre_tc}.txt"
    )

    with open(ruta_txt, "w", encoding="utf-8") as f:
        f.write(f"Orden de columnas en datos_filtrados_{nombre_tc}.xlsx\n\n")
        for linea in lineas_txt:
            f.write(linea + "\n")

    print(f"✔ TXT generado: {ruta_txt}")


# ============================================================
# PROCESAR CARPETA
# ============================================================
def procesar_carpeta_tc(ruta_carpeta, nombre_tc, T_objetivo, filtro_fechas):

    print(f"\n📂 Procesando carpeta: {nombre_tc}")

    orden_correcto = {
        "A400000082BAF041": ("T1", "Ssuperior"),
        "7D000000828FA841": ("T1", "Sintermedio"),
        "5900000082B86A41": ("T1", "Sinferior"),
        "2E000000828FF441": ("T2", "Ssuperior"),
        "4B0000008298EA41": ("T2", "Sintermedio"),
        "4600000082991C41": ("T2", "Sinferior"),
        "870000008290BE41": ("T3", "Ssuperior"),
        "0600000082994E41": ("T3", "Sintermedio"),
        "98000000828FD441": ("T3", "Sinferior"),
        "F60000008290D841": ("T4", "Ssuperior"),
        "2D00000082925E41": ("T4", "Sintermedio"),
        "B3000000828F2741": ("T4", "Sinferior"),
        "3800000082952A41": ("T5", "Ssuperior"),
        "B000000082987741": ("T5", "Sintermedio"),
        "2800000082978041": ("T5", "Sinferior"),
    }

    ini, fin = pd.to_datetime(filtro_fechas[0]), pd.to_datetime(filtro_fechas[1])

    tabla_filtrada = {}

    archivos = [f for f in os.listdir(ruta_carpeta) if f.lower().endswith(".csv")]

    if len(archivos) == 0:
        print("⚠ No hay archivos CSV en la carpeta.")
        return

    for archivo in archivos:

        id_code = archivo.split("_")[0]

        if id_code not in orden_correcto:
            continue

        T, nivel = orden_correcto[id_code]

        if T != T_objetivo:
            continue

        df_full = leer_ibutton_csv(os.path.join(ruta_carpeta, archivo))

        if df_full.empty:
            continue

        df_filtro = df_full[
            (df_full["datetime"] >= ini) &
            (df_full["datetime"] <= fin)
        ]

        if not df_filtro.empty:
            tabla_filtrada[nivel] = df_filtro

    if len(tabla_filtrada) == 0:
        print("⚠ No hay datos dentro del rango de fechas.")
        return

    # ============================================================
    # EXCEL + TXT
    # ============================================================
    generar_excel_separado(tabla_filtrada, ruta_carpeta, nombre_tc, T_objetivo)

       # ============================================================
    # GRÁFICO PROFESIONAL LIMPIO (VERSIÓN CORREGIDA)
    # ============================================================

    fig, ax = plt.subplots(figsize=(11, 6), dpi=300)

    nombre_legenda = {
        "Ssuperior": "Superior",
        "Sintermedio": "Intermedio",
        "Sinferior": "Inferior"
    }

    colores = {
        "Ssuperior": "#1f77b4",      # azul
        "Sintermedio": "#ff7f0e",    # naranja
        "Sinferior": "#2ca02c"       # verde
    }

    for nivel in ["Ssuperior", "Sintermedio", "Sinferior"]:

        if nivel not in tabla_filtrada:
            continue

        profundidad = profundidades_tc[T_objetivo].get(nivel)
        etiqueta = f"{nombre_legenda[nivel]} ({profundidad:.2f} m)"

        ax.plot(
            tabla_filtrada[nivel]["datetime"],
            tabla_filtrada[nivel]["temperatura"],
            linewidth=2,
            color=colores[nivel],
            label=etiqueta
        )

    # ------------------------------------------------------------
    # FORMATO AUTOMÁTICO INTELIGENTE DE FECHA
    # ------------------------------------------------------------
    fecha_min = min(df["datetime"].min() for df in tabla_filtrada.values())
    fecha_max = max(df["datetime"].max() for df in tabla_filtrada.values())
    dias_total = (fecha_max - fecha_min).days

    if dias_total <= 10:
        intervalo = 1
    elif dias_total <= 20:
        intervalo = 2
    else:
        intervalo = 3

    locator = mdates.DayLocator(interval=intervalo)
    formatter = mdates.DateFormatter("%d-%m")

    ax.xaxis.set_major_locator(locator)
    ax.xaxis.set_major_formatter(formatter)

    plt.xticks(rotation=0)

    # ------------------------------------------------------------
    # ESTÉTICA PROFESIONAL
    # ------------------------------------------------------------
    
    ax.set_xlabel("Fecha", fontsize=14)
    ax.set_ylabel("Temperatura [°C]", fontsize=14)

    ax.tick_params(axis='both', labelsize=12)

    ax.grid(True, linestyle="--", linewidth=0.6, alpha=0.4)

    # quitar bordes superior y derecho
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    ax.legend(
        loc="upper center",
        bbox_to_anchor=(0.5, 1.15),
        ncol=3,
        frameon=False,
        fontsize=12
    )

    plt.tight_layout()

    ruta_png = os.path.join(ruta_carpeta, f"temperatura_{nombre_tc}.png")
    plt.savefig(ruta_png)
    plt.close()

    print(f"✔ Gráfico generado: {ruta_png}")




# ============================================================
# MAIN
# ============================================================
def main():
###############################################################################
##### ACTUALIZAR###############################################################
###############################################################################
    ruta_base = (
        r"G:\Unidades compartidas\03.2 Proyectos MLP3\MLP-OT010_MC y MN Tranque Quillayes"
        r"\03.WIP\05.Terreno\8. Terreno 3 Termocuplas 25Feb26"
        r"\3. Datos Termocuplas 25-02-2026"
    )
###############################################################################
##### ACTUALIZAR###############################################################
###############################################################################
    filtros_tc = {
        "T1": ("2025-12-21 16:00", "2026-02-25 12:00"),
        "T2": ("2026-01-23 13:00", "2026-02-25 12:00"),
        "T3": ("2026-01-23 13:00", "2026-02-25 12:00"),
        "T4": ("2025-12-21 16:00", "2026-02-25 12:00"),
        "T5": ("2025-12-21 16:00", "2026-02-25 12:00"),
    }
    
    carpetas_tc = {
        "tc1": "T1",
        "tc2": "T2",
        "tc3": "T3",
        "tc4": "T4",
        "tc5": "T5",
    }

    for carpeta, T in carpetas_tc.items():

        ruta_tc = os.path.join(ruta_base, carpeta)

        print("\n-----------------------------------")
        print("Buscando carpeta:", ruta_tc)

        if not os.path.isdir(ruta_tc):
            print("❌ Carpeta no existe")
            continue

        procesar_carpeta_tc(ruta_tc, carpeta, T, filtros_tc[T])


if __name__ == "__main__":
    main()

