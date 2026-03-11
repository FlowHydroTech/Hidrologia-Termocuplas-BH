# -*- coding: utf-8 -*-
"""
Created on Wed Jan 28 14:23:34 2026

@author: Sebastian
"""

import os
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

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
                "1-Wire", "Mission", "SUTA", "Waiting", "Sample",
                "Roll", "First", "Total", "Temperature", "Data ",
                "Date/Time"
            )):
                continue

            partes = linea.split(",", 2)
            if len(partes) != 3:
                continue

            try:
                fecha = partes[0]
                valor = float(partes[2].replace(",", "."))
                datos.append([fecha, valor])
            except ValueError:
                continue

    df = pd.DataFrame(datos, columns=["datetime", "temperatura"])
    df["datetime"] = pd.to_datetime(df["datetime"], format="%d-%m-%y %H:%M:%S")

    return df


# ============================================================
# PROCESAR CADA TC
# ============================================================
def procesar_carpeta_tc(ruta_carpeta, nombre_tc, T_objetivo, filtro_fechas):

    print(f"\n📂 Procesando carpeta: {nombre_tc}")

    # IDS DEFINITIVOS
    orden_correcto = {
        # T1
        "A400000082BAF041": ("T1", "Ssuperior"),
        "7D000000828FA841": ("T1", "Sintermedio"),
        "5900000082B86A41": ("T1", "Sinferior"),

        # T2
        "2E000000828FF441": ("T2", "Ssuperior"),
        "4B0000008298EA41": ("T2", "Sintermedio"),
        "4600000082991C41": ("T2", "Sinferior"),

        # T3
        "870000008290BE41": ("T3", "Ssuperior"),
        "0600000082994E41": ("T3", "Sintermedio"),
        "98000000828FD441": ("T3", "Sinferior"),

        # T4
        "F60000008290D841": ("T4", "Ssuperior"),
        "2D00000082925E41": ("T4", "Sintermedio"),
        "B3000000828F2741": ("T4", "Sinferior"),

        # T5
        "3800000082952A41": ("T5", "Ssuperior"),
        "B000000082987741": ("T5", "Sintermedio"),
        "2800000082978041": ("T5", "Sinferior"),
    }

    archivos = [f for f in os.listdir(ruta_carpeta) if f.lower().endswith(".csv")]
    tabla = {}

    ini, fin = pd.to_datetime(filtro_fechas[0]), pd.to_datetime(filtro_fechas[1])

    for archivo in archivos:
        id_code = archivo.split("_")[0]

        if id_code not in orden_correcto:
            print(f"⚠ ID no reconocido: {archivo}")
            continue

        T, nivel = orden_correcto[id_code]
        if T != T_objetivo:
            continue

        df = leer_ibutton_csv(os.path.join(ruta_carpeta, archivo))

        # FILTRO TEMPORAL
        df = df[(df["datetime"] >= ini) & (df["datetime"] <= fin)]

        tabla[nivel] = df

    # ==========================
    # EXCEL FILTRADO (COPIA)
    # ==========================
    columnas = []
    for nivel in ["Ssuperior", "Sintermedio", "Sinferior"]:
        if nivel in tabla:
            columnas.append(tabla[nivel]["datetime"].rename(f"{nivel}_fecha"))
            columnas.append(tabla[nivel]["temperatura"].rename(f"{nivel}_temp"))

    df_excel = pd.concat(columnas, axis=1)
    ruta_excel = os.path.join(ruta_carpeta, f"datos_filtrados_{nombre_tc}.xlsx")
    df_excel.to_excel(ruta_excel, index=False)

    # ==========================
    # GRAFICO
    # ==========================
    fig, ax = plt.subplots(figsize=(7, 4), dpi=300)

    nombres_leyenda = {
        "Ssuperior": "S. Superior",
        "Sintermedio": "S. Intermedio",
        "Sinferior": "S. Inferior",
    }

    for nivel, df in tabla.items():
        ax.plot(
            df["datetime"],
            df["temperatura"],
            label=nombres_leyenda[nivel],
            linewidth=1.2
        )

    # Eje Y
    ax.set_ylabel("Temperatura [°C]", rotation=0, labelpad=40)
    ax.yaxis.set_label_coords(-0.02, 1.02)

    # Eje X → 2 marcas por día (cada 12 h)
    
    ax.xaxis.set_major_locator(mdates.DayLocator()) 
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%d-%m-%Y")) 
    ax.xaxis.set_minor_locator(mdates.HourLocator(byhour=[0,12])) 
    plt.xticks(rotation=60)    
    # Grillas suaves
    ax.grid(True, which="major", axis="x", linestyle="--", linewidth=0.4, alpha=0.5)
    ax.grid(True, which="major", axis="y", linestyle="--", linewidth=0.4, alpha=0.5)

    ax.legend(frameon=False)
    ax.set_title(f"{T_objetivo} – Evolución temporal de temperatura")

    ruta_png = os.path.join(ruta_carpeta, f"temperatura_{nombre_tc}.png")
    plt.tight_layout()
    plt.savefig(ruta_png)
    plt.close()

    print(f"✔ Excel generado: {ruta_excel}")
    print(f"✔ Gráfico generado: {ruta_png}")


# ============================================================
# MAIN
# ============================================================
def main():

    ruta_base = (
        r"G:\Unidades compartidas\03.2 Proyectos MLP3"
        r"\MLP-OT010_MC y MN Tranque Quillayes"
        r"\03.WIP\05.Terreno"
        r"\5. Terreno 2 Termocuplas Ene 2026"
        r"\3. Datos Termocuplas 22-01-26"
    )

    filtros_tc = { "T1": ("2025-12-21 08:00", "2026-01-22 06:00"), "T2": ("2026-01-21 12:00", "2026-01-22 20:00"), "T3": ("2026-01-22 13:00", "2026-01-22 20:00"), "T4": ("2025-12-21 06:00", "2026-01-22 06:00"), "T5": ("2025-12-21 10:00", "2026-01-22 06:00"), }

    carpetas_tc = {
        "tc1": "T1",
        "tc2": "T2",
        "tc3": "T3",
        "tc4": "T4",
        "tc5": "T5",
    }

    for carpeta, T in carpetas_tc.items():
        ruta_tc = os.path.join(ruta_base, carpeta)
        if os.path.isdir(ruta_tc):
            procesar_carpeta_tc(
                ruta_tc,
                carpeta,
                T,
                filtros_tc[T]
            )


if __name__ == "__main__":
    main()


