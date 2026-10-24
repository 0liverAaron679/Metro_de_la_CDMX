import os
import re
import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st

# Configuración de la página de Streamlit
st.set_page_config(
    page_title="Panel de Negocio - Afluencia Metro CDMX",
    page_icon="🚇",
    layout="wide",
)

TEMPLATE_PLOT = "plotly_white"

# Título principal de la aplicación
st.title("🚇 Análisis de Afluencia y Demanda - Metro CDMX")
st.markdown(
    "Plataforma simplificada para la evaluación de movilidad urbana y monitoreo de estaciones clave (2010 - 2024)."
)


# Función para cargar y limpiar los datos desde la misma carpeta del proyecto
@st.cache_data
def cargar_datos():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    filename = os.path.join(script_dir, "0e8ffe58-28bb-4dde-afcd-e5f5b4de4ccb.csv")
    df = pd.read_csv(filename)

    # Limpieza y estandarización de la columna 'linea'
    def limpiar_linea(val):
        val_str = str(val)
        res = re.sub(
            r"[^0-9A-Za-z]",
            "",
            val_str.replace("Linea", "")
            .replace("Línea", "")
            .replace("LÃ­nea", ""),
        )
        return res.strip()

    df["linea"] = df["linea"].apply(limpiar_linea)
    df["fecha"] = pd.to_datetime(df["fecha"])
    df = df[(df["anio"] >= 2010) & (df["anio"] <= 2024)]
    return df


try:
    df = cargar_datos()

    # --- BARRA LATERAL: FILTROS SIMPLIFICADOS ---
    st.sidebar.header("🎛️ Filtros de Visualización")

    # 1. Selector simple de Años (Rango)
    st.sidebar.subheader("📅 Rango de Años")
    rango_anos = st.sidebar.slider(
        "Selecciona el periodo:",
        min_value=2010,
        max_value=2024,
        value=(2010, 2024)
    )

    # 2. Selector rápido de Líneas (Multiselect limpio)
    st.sidebar.subheader("🚇 Líneas del Metro")
    raw_lines = sorted(
        df["linea"].unique(),
        key=lambda x: (0, int(x)) if str(x).isdigit() else (1, str(x)),
    )
    lineas_opciones = {f"Línea {l}": l for l in raw_lines}
    
    seleccion_lineas = st.sidebar.multiselect(
        "Selecciona las líneas a consultar:",
        options=list(lineas_opciones.keys()),
        default=list(lineas_opciones.keys()) # Todas seleccionadas por defecto
    )
    lineas_seleccionadas = [lineas_opciones[item] for item in seleccion_lineas]

    # Aplicación de filtros
    df_filtrado = df[
        (df["anio"] >= rango_anos[0]) & 
        (df["anio"] <= rango_anos[1]) &
        (df["linea"].isin(lineas_seleccionadas))
    ]

    # --- PANEL DE MÉTRICAS CLAVE (KPIs) ---
    st.markdown("### 📈 Indicadores Clave")
    c1, c2, c3, c4 = st.columns(4)
    
    total_pasajeros = df_filtrado["afluencia"].sum() / 1e6
    c1.metric("Demanda Total Acumulada", f"{total_pasajeros:,.2f} M")
    
    promedio_diario = df_filtrado["afluencia"].mean()
    c2.metric("Promedio Diario / Estación", f"{promedio_diario:,.0f} pas.")
    
    estaciones_activas = df_filtrado["estacion"].nunique()
    c3.metric("Estaciones Monitoreadas", f"{estaciones_activas}")
    
    max_registro = df_filtrado.loc[df_filtrado["afluencia"].idxmax()] if not df_filtrado.empty else None
    if max_registro is not None:
        c4.metric("Pico Máximo de Afluencia", f"{max_registro['afluencia']:,} pas.", help=f"Estación {max_registro['estacion']} (Línea {max_registro['linea']})")
    else:
        c4.metric("Pico Máximo", "0 pas.")

    st.markdown("---")

    # --- VISUALIZACIONES INTERACTIVAS SIMPLIFICADAS ---
    tab1, tab2, tab3 = st.tabs([
        "📈 Líneas de Tendencia Temporal", 
        "📉 Gráfico de Dispersión", 
        "🌐 Modelo 3D Interactivo"
    ])

    with tab1:
        st.subheader("Evolución y Líneas de Tendencia de la Afluencia")
        st.markdown("Comportamiento anual del volumen de pasajeros transportados por línea.")

        if df_filtrado.empty:
            st.warning("Selecciona al menos una línea en la barra lateral.")
        else:
            df_tendencia = df_filtrado.groupby(["anio", "linea"], as_index=False)["afluencia"].sum()
            df_tendencia["afluencia_millones"] = df_tendencia["afluencia"] / 1e6

            fig_lineas = px.line(
                df_tendencia,
                x="anio",
                y="afluencia_millones",
                color="linea",
                markers=True,
                labels={"anio": "Año", "afluencia_millones": "Afluencia Total (Millones)", "linea": "Línea"},
                template=TEMPLATE_PLOT
            )
            fig_lineas.update_layout(hovermode="x unified", height=500)
            st.plotly_chart(fig_lineas, use_container_width=True)

    with tab2:
        st.subheader("Gráfico de Dispersión: Relación Operativa")
        st.markdown("Distribución de la afluencia registrada en el periodo seleccionado.")

        if df_filtrado.empty:
            st.warning("Selecciona al menos una línea en la barra lateral.")
        else:
            df_sample = df_filtrado.sample(n=min(4000, len(df_filtrado)), random_state=42)
            
            fig_scatter = px.scatter(
                df_sample,
                x="fecha",
                y="afluencia",
                color="linea",
                opacity=0.6,
                labels={"fecha": "Fecha", "afluencia": "Afluencia Diaria", "linea": "Línea"},
                template=TEMPLATE_PLOT
            )
            fig_scatter.update_layout(height=500)
            st.plotly_chart(fig_scatter, use_container_width=True)

    with tab3:
        st.subheader("Visualización Tridimensional Interactiva")
        st.markdown("💡 **Tip:** Haz clic y arrastra con el mouse para rotar el gráfico 3D.")

        if df_filtrado.empty:
            st.warning("Selecciona al menos una línea en la barra lateral.")
        else:
            df_3d = df_filtrado.groupby(["anio", "linea"], as_index=False)["afluencia"].sum()
            df_3d["afluencia_millones"] = df_3d["afluencia"] / 1e6

            fig_3d = px.scatter_3d(
                df_3d,
                x="anio",
                y="linea",
                z="afluencia_millones",
                color="linea",
                size="afluencia_millones",
                opacity=0.85,
                labels={"anio": "Año", "linea": "Línea", "afluencia_millones": "Millones de Pasajeros"},
                template=TEMPLATE_PLOT
            )
            fig_3d.update_layout(height=600, margin=dict(l=0, r=0, b=0, t=0))
            st.plotly_chart(fig_3d, use_container_width=True)

    # --- TABLA DE DATOS EXPLORATORIA ---
    with st.expander("🔍 Ver registros detallados"):
        st.dataframe(df_filtrado, use_container_width=True)

except Exception as e:
    st.error(f"Ocurrió un error al procesar la aplicación. Detalles: {e}")