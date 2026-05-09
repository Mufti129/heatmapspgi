# ============================================
# app.py
# STREAMLIT + FOLIUM DASHBOARD CABANG
# MENU:
# 1. PETA MODEL GWR
# 2. PETA PERFORMA CABANG
# ============================================

import streamlit as st
import pandas as pd
import folium
import numpy as np

from folium.plugins import HeatMap, MarkerCluster
from streamlit_folium import st_folium

# ============================================
# CONFIG PAGE
# ============================================

st.set_page_config(
    page_title="Dashboard Peta Cabang",
    layout="wide"
)

st.title("📍 Dashboard Analisis Cabang")

# ============================================
# LOAD DATA
# ============================================

@st.cache_data
def load_data():

    # ========================================
    # GANTI LINK RAW GITHUB EXCEL DI SINI
    # ========================================

    url = "https://raw.githubusercontent.com/USERNAME/REPO/main/data/data_cabang.xlsx"

    df = pd.read_excel(url)

    return df

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
# FILTER
# ============================================

st.sidebar.subheader("Filter Data")

selected_wilayah = st.sidebar.multiselect(
    "Kategori Wilayah",
    options=df["kategori_wilayah"].dropna().unique(),
    default=df["kategori_wilayah"].dropna().unique()
)

df = df[df["kategori_wilayah"].isin(selected_wilayah)]

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

    st.header("📊 Peta Model GWR")

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

    # ========================================
    # KOLOM LOCAL COEF
    # contoh:
    # umk_local_coef
    # penduduk_local_coef
    # dst
    # ========================================

    coef_col = f"{selected_var}_local_coef"

    m_gwr = folium.Map(
        location=[center_lat, center_lon],
        zoom_start=10,
        tiles="CartoDB positron"
    )

    marker_cluster = MarkerCluster().add_to(m_gwr)

    for _, row in df.iterrows():

        local_coef = row[coef_col]

        abs_local_coef = abs(local_coef * 10)

        radius_val = max(3, min(abs_local_coef, 20))

        color = "red" if local_coef > 0 else "blue"

        popup_html = f"""
        <b>Cabang:</b> {row['nama_cabang']} <br>
        <b>Variabel:</b> {selected_var} <br>
        <b>Koefisien Lokal:</b> {local_coef:.4f} <br>
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
    # TOP 5 HIGHLIGHT
    # ========================================

    top5 = df.nlargest(5, coef_col)

    for _, row in top5.iterrows():

        folium.Marker(
            location=[row["lat"], row["lon"]],
            tooltip=f"TOP GWR - {row['nama_cabang']}",
            icon=folium.Icon(color="green", icon="star")
        ).add_to(m_gwr)

    # ========================================
    # LEGEND
    # ========================================

    legend_html = """
    <div style="
        position: fixed;
        bottom: 50px;
        left: 50px;
        width: 250px;
        height: 120px;
        background-color: white;
        z-index:9999;
        padding:10px;
        border:2px solid grey;
        font-size:14px;
    ">
    <b>Legenda GWR</b><br>
    🔴 Pengaruh Positif<br>
    🔵 Pengaruh Negatif<br>
    ⭐ Top 5 Lokasi<br>
    Ukuran marker = kekuatan pengaruh
    </div>
    """

    m_gwr.get_root().html.add_child(folium.Element(legend_html))

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

    st.header("🔥 Peta Performa Cabang")

    m = folium.Map(
        location=[center_lat, center_lon],
        zoom_start=11,
        tiles='CartoDB positron'
    )

    # ========================================
    # LAYER 1
    # HEATMAP OMZET
    # ========================================

    fg1 = folium.FeatureGroup(name='Sebaran Omzet')

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
    # LAYER 2
    # HEATMAP UMK
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
    # LAYER 3
    # MARKER CABANG
    # ========================================

    fg3 = folium.FeatureGroup(
        name='Lokasi Cabang'
    )

    for _, row in df.iterrows():

        # ====================================
        # WARNA BERDASARKAN WILAYAH
        # ====================================

        if row['kategori_wilayah'] == 'Perkotaan':
            marker_color = 'red'

        elif row['kategori_wilayah'] == 'Perdesaan':
            marker_color = 'blue'

        else:
            marker_color = 'black'

        # ====================================
        # PERFORMANCE COLOR
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
            fill_opacity=0.7,
            popup=popup_html
        ).add_to(fg3)

    fg3.add_to(m)

    # ========================================
    # TOP 5 CABANG
    # ========================================

    top5_omzet = df.nlargest(5, "avg_omzet")

    for _, row in top5_omzet.iterrows():

        folium.Marker(
            location=[row["lat"], row["lon"]],
            tooltip=f"TOP OMZET - {row['nama_cabang']}",
            icon=folium.Icon(color="green", icon="star")
        ).add_to(m)

    # ========================================
    # LAYER CONTROL
    # ========================================

    folium.LayerControl(
        collapsed=False
    ).add_to(m)

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
