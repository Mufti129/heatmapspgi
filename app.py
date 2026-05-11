# ============================================
# app.py
# DASHBOARD ANALISIS CABANG
# STREAMLIT + FOLIUM
# ============================================

import streamlit as st
import pandas as pd
import folium
import numpy as np
import warnings

from folium.plugins import HeatMap, MarkerCluster
from streamlit_folium import st_folium

warnings.filterwarnings("ignore")

# ============================================
# CONFIG PAGE
# ============================================

st.set_page_config(
    page_title="Dashboard Analisis Cabang",
    layout="wide"
)

st.title("Dashboard Analisis Cabang")

# ============================================
# LOAD DATA
# ============================================

@st.cache_data
def load_data():

    try:

        # ====================================
        # LOAD EXCEL LOKAL DARI GITHUB REPO
        # ====================================

        df = pd.read_excel(
            "data/FIX_mining_prediksi_attribute_jumlah_!.xlsx",
            engine="openpyxl"
        )

        # ====================================
        # CLEANING
        # ====================================

        df = df.dropna(subset=['lat', 'lon'])

        df = df.fillna(0)

        return df

    except Exception as e:

        st.error(f"Gagal load data: {e}")
        st.stop()

df = load_data()

# ============================================
# SIDEBAR
# ============================================

st.sidebar.title("Menu Dashboard")

menu = st.sidebar.radio(
    "Pilih Menu",
    [
        "Peta Model GWR",
        "Peta Performa Cabang"
    ]
)

# ============================================
# FILTER DATA
# ============================================

st.sidebar.subheader("Filter")

# FILTER WILAYAH
selected_wilayah = st.sidebar.multiselect(
    "Kategori Wilayah",
    options=df["kategori_wilayah"].dropna().unique(),
    default=df["kategori_wilayah"].dropna().unique()
)

df = df[df["kategori_wilayah"].isin(selected_wilayah)]

# SEARCH CABANG
search_cabang = st.sidebar.text_input(
    "Cari Nama Cabang"
)

if search_cabang:

    df = df[
        df['nama_cabang']
        .astype(str)
        .str.contains(search_cabang, case=False)
    ]

# ============================================
# METRICS
# ============================================

col1, col2, col3 = st.columns(3)

col1.metric(
    "Jumlah Cabang",
    len(df)
)

col2.metric(
    "Total Avg Omzet",
    f"Rp {df['avg_omzet'].sum():,.0f}"
)

col3.metric(
    "Rata-rata UMK",
    f"Rp {df['umk'].mean():,.0f}"
)

# ============================================
# DOWNLOAD DATA
# ============================================

st.download_button(
    label="Download Data CSV",
    data=df.to_csv(index=False),
    file_name="data_cabang.csv",
    mime="text/csv"
)

# ============================================
# CENTER MAP
# ============================================

center_lat = df["lat"].mean()
center_lon = df["lon"].mean()

# ============================================
# MENU 1
# PETA MODEL GWR
# ============================================

if menu == "Peta Model GWR":

    st.header("Peta Model GWR")

    variables_to_visualize = [
        'umk',
        'penduduk',
        'kemiskinan',
        'jumlah_kompetitor',
        'jumlah_pasar_tradisional',
        'jarak_pasar',
        'lebar_ruko',
        'jumlah_bangunan',
        'commercial_hub_index',
        'premium_spot_score',
        'comp_per_pop'
    ]

    selected_var = st.selectbox(
        "Pilih Variabel GWR",
        variables_to_visualize
    )

    coef_col = f"{selected_var}_local_coef"

    # ========================================
    # VALIDASI KOLOM
    # ========================================

    if coef_col not in df.columns:

        st.error(
            f"Kolom '{coef_col}' belum tersedia di dataset"
        )

        st.stop()

    # ========================================
    # MAP
    # ========================================

    m_gwr = folium.Map(
        location=[center_lat, center_lon],
        zoom_start=10,
        tiles="CartoDB positron"
    )

    marker_cluster = MarkerCluster().add_to(m_gwr)

    # ========================================
    # MARKER GWR
    # ========================================

    for _, row in df.iterrows():

        local_coef = row[coef_col]

        abs_local_coef = abs(local_coef * 10)

        radius_val = max(3, min(abs_local_coef, 20))

        color = "red" if local_coef > 0 else "blue"

        popup_html = f"""
        <b>Cabang:</b> {row['nama_cabang']}<br>
        <b>Variabel:</b> {selected_var}<br>
        <b>Koefisien Lokal:</b> {local_coef:.4f}<br>
        <b>Nilai Variabel:</b> {row[selected_var]:,.0f}
        """

        folium.CircleMarker(
            location=[row["lat"], row["lon"]],
            radius=radius_val,
            color=color,
            fill=True,
            fill_color=color,
            fill_opacity=0.7,
            popup=popup_html
        ).add_to(marker_cluster)

    # ========================================
    # TOP 5 GWR
    # ========================================

    top5 = df.nlargest(5, coef_col)

    for _, row in top5.iterrows():

        folium.Marker(
            location=[row["lat"], row["lon"]],
            tooltip=f"TOP GWR - {row['nama_cabang']}",
            icon=folium.Icon(
                color="green",
                icon="star"
            )
        ).add_to(m_gwr)

    # ========================================
    # AUTO FIT MAP
    # ========================================

    sw = df[['lat', 'lon']].min().values.tolist()
    ne = df[['lat', 'lon']].max().values.tolist()

    m_gwr.fit_bounds([sw, ne])

    # ========================================
    # LEGEND
    # ========================================

    legend_html = """
    <div style="
        position: fixed;
        bottom: 50px;
        left: 50px;
        width: 250px;
        height: 130px;
        background-color: white;
        z-index:9999;
        padding:10px;
        border:2px solid grey;
        font-size:14px;
    ">
    <b>Legenda GWR</b><br>
    🔴 Pengaruh Positif<br>
    🔵 Pengaruh Negatif<br>
    ⭐ Top 5 Lokasi<br><br>
    Ukuran marker = kekuatan pengaruh
    </div>
    """

    m_gwr.get_root().html.add_child(
        folium.Element(legend_html)
    )

    st_folium(
        m_gwr,
        width=1400,
        height=700
    )

# ============================================
# MENU 2
# PETA PERFORMA CABANG
# ============================================

elif menu == "Peta Performa Cabang":

    st.header("Peta Performa Cabang")

    m = folium.Map(
        location=[center_lat, center_lon],
        zoom_start=11,
        tiles='CartoDB positron'
    )

    # ========================================
    # LAYER 1 - HEATMAP OMZET
    # ========================================

    fg1 = folium.FeatureGroup(
        name='Sebaran Omzet'
    )

    heat_omzet = [
        [row['lat'], row['lon'], row['avg_omzet']]
        for _, row in df.iterrows()
    ]

    HeatMap(
        heat_omzet,
        radius=15,
        blur=20,
        gradient={
            0.4: 'blue',
            0.7: 'lime',
            1: 'yellow'
        }
    ).add_to(fg1)

    fg1.add_to(m)

    # ========================================
    # LAYER 2 - HEATMAP UMK
    # ========================================

    fg2 = folium.FeatureGroup(
        name='Sebaran UMK',
        show=False
    )

    heat_umk = [
        [row['lat'], row['lon'], row['umk']]
        for _, row in df.iterrows()
    ]

    HeatMap(
        heat_umk,
        radius=15,
        blur=20
    ).add_to(fg2)

    fg2.add_to(m)

    # ========================================
    # LAYER 3 - MARKER CABANG
    # ========================================

    fg3 = folium.FeatureGroup(
        name='Lokasi Cabang'
    )

    for _, row in df.iterrows():

        # ====================================
        # WARNA WILAYAH
        # ====================================

        if row['kategori_wilayah'] == 'Perkotaan':

            marker_color = 'red'

        elif row['kategori_wilayah'] == 'Perdesaan':

            marker_color = 'blue'

        else:

            marker_color = 'black'

        # ====================================
        # RADIUS BERDASARKAN OMZET
        # ====================================

        omzet = row['avg_omzet']

        if omzet >= df['avg_omzet'].quantile(0.75):

            radius = 12

        elif omzet >= df['avg_omzet'].quantile(0.50):

            radius = 8

        else:

            radius = 5

        popup_html = f"""
        <b>Cabang:</b> {row['nama_cabang']}<br>
        <b>Wilayah:</b> {row['kategori_wilayah']}<br>
        <b>Omzet:</b> Rp {row['avg_omzet']:,.0f}<br>
        <b>Jalan:</b> {row['jalan']}<br>
        <b>Lebar Ruko:</b> {row['lebar_ruko']}<br>
        <b>Penduduk:</b> {row['penduduk']:,.0f}<br>
        <b>Kompetitor:</b> {row['jumlah_kompetitor']:,.0f}<br>
        <b>Pasar:</b> {row['jumlah_pasar_tradisional']:,.0f}
        """

        folium.CircleMarker(
            location=[row['lat'], row['lon']],
            radius=radius,
            color=marker_color,
            fill=True,
            fill_color=marker_color,
            fill_opacity=0.7,
            popup=popup_html
        ).add_to(fg3)

    fg3.add_to(m)

    # ========================================
    # TOP 5 OMZET
    # ========================================

    top5_omzet = df.nlargest(5, "avg_omzet")

    for _, row in top5_omzet.iterrows():

        folium.Marker(
            location=[row["lat"], row["lon"]],
            tooltip=f"TOP OMZET - {row['nama_cabang']}",
            icon=folium.Icon(
                color="green",
                icon="star"
            )
        ).add_to(m)

    # ========================================
    # LAYER CONTROL
    # ========================================

    folium.LayerControl(
        collapsed=False
    ).add_to(m)

    # ========================================
    # AUTO FIT MAP
    # ========================================

    sw = df[['lat', 'lon']].min().values.tolist()
    ne = df[['lat', 'lon']].max().values.tolist()

    m.fit_bounds([sw, ne])

    # ========================================
    # LEGEND
    # ========================================

    legend_html = """
    <div style="
        position: fixed;
        bottom: 50px;
        left: 50px;
        width: 250px;
        height: 170px;
        background-color: white;
        z-index:9999;
        padding:10px;
        border:2px solid grey;
        font-size:14px;
    ">
    <b>Legenda</b><br>
    🔴 Perkotaan<br>
    🔵 Perdesaan<br>
    ⚫ Perkampungan<br>
    ⭐ Top 5 Omzet<br><br>
    Ukuran marker = performa omzet
    </div>
    """

    m.get_root().html.add_child(
        folium.Element(legend_html)
    )

    st_folium(
        m,
        width=1400,
        height=700
    )
