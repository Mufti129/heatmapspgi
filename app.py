import pandas as pd
import folium
from folium.plugins import HeatMap
import streamlit as st

# --- 1. PENGATURAN DATA ---
# URL Google Sheets (Sudah diatur untuk ekspor CSV)
sheet_id = "1EbLaHBvDpflmxejtAdb0JCXxUuozhoptpiHoAvL7Ba4"
gid = "1204195088"
url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv&gid={gid}"

@st.cache_data
def load_data(url):
    df = pd.read_csv(url)
    # Menyeragamkan nama kolom (hapus spasi & kecilkan huruf)
    df.columns = df.columns.str.strip().str.lower()
    
    # Konversi kolom numerik & hapus baris yang rusak/kosong
    cols_to_fix = ['lat', 'lon', 'avg_omzet', 'umk', 'penduduk']
    for col in cols_to_fix:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')
    
    # Hapus data yang tidak memiliki koordinat valid
    df = df.dropna(subset=['lat', 'lon'])
    return df

df_clean = load_data(url)

# --- 2. INISIALISASI PETA ---
m = folium.Map(
    location=[df_clean['lat'].mean(), df_clean['lon'].mean()],
    zoom_start=11,
    tiles='CartoDB positron'
)

# --- 3. FEATURE GROUPS ---
fg_list = {
    'omzet': folium.FeatureGroup(name='Sebaran Omzet (Aktual)'),
    'umk': folium.FeatureGroup(name='Sebaran UMK', show=False),
    'cabang': folium.FeatureGroup(name='Lokasi Cabang (Kota vs Desa)'),
    'jalan': folium.FeatureGroup(name='Lokasi Jalan', show=False)
}

# --- 4. HEATMAPS ---
# Heatmap Omzet
data_omzet = df_clean[['lat', 'lon', 'avg_omzet']].dropna().values.tolist()
HeatMap(data_omzet, radius=15, blur=20, 
        gradient={0.4: 'blue', 0.7: 'lime', 1: 'yellow'}).add_to(fg_list['omzet'])

# Heatmap UMK
data_umk = df_clean[['lat', 'lon', 'umk']].dropna().values.tolist()
HeatMap(data_umk, radius=15, blur=20,
        gradient={0.4: 'purple', 0.7: 'red', 1: 'orange'}).add_to(fg_list['umk'])

# --- 5. MARKER (LOOP TUNGGAL) ---
for i, row in df_clean.iterrows():
    # Logika Warna Wilayah
    cat = str(row.get('kategori_wilayah', '')).lower()
    color_wilayah = 'red' if 'kota' in cat else 'blue' if 'desa' in cat else 'black'
    
    # Logika Warna Jalan
    road_type = str(row.get('jalan', '')).lower()
    road_map = {
        'primary': 'red', 'tertiary': 'red', 'residential': 'beige', 
        'trunk': 'orange', 'secondary': 'blue', 'living_street': 'purple'
    }
    color_jalan = road_map.get(road_type, 'black')

    popup_content = f"""
        <div style='font-family: Arial; font-size: 12px; width: 150px;'>
            <b>Cabang:</b> {row.get('nama_cabang', 'N/A')}<br>
            <b>Omzet:</b> Rp{row.get('avg_omzet', 0):,.0f}<br>
            <b>Jalan:</b> {road_type}<br>
            <b>Penduduk:</b> {row.get('penduduk', 0):,.0f}
        </div>
    """

    # Marker Wilayah ke Layer Cabang
    folium.CircleMarker(
        location=[row['lat'], row['lon']], radius=5, color=color_wilayah,
        fill=True, fill_opacity=0.7, popup=folium.Popup(popup_content, max_width=200)
    ).add_to(fg_list['cabang'])
    
    # Marker Jalan ke Layer Jalan
    folium.CircleMarker(
        location=[row['lat'], row['lon']], radius=5, color=color_jalan,
        fill=True, fill_opacity=0.3, popup=folium.Popup(popup_content, max_width=200)
    ).add_to(fg_list['jalan'])

# --- 6. LAYER CONTROL & LEGENDA ---
for fg in fg_list.values():
    fg.add_to(m)

folium.LayerControl(collapsed=False).add_to(m)

legend_html = '''
     <div style="position: fixed; bottom: 50px; left: 50px; width: 200px; 
                  border:2px solid grey; z-index:9999; font-size:11px;
                  background-color:white; opacity:0.85; padding: 10px; font-family: sans-serif;">
        <b>Legenda Wilayah</b><br>
        <i style="background:red; border-radius:50%; width:10px; height:10px; display:inline-block;"></i> Perkotaan<br>
        <i style="background:blue; border-radius:50%; width:10px; height:10px; display:inline-block;"></i> Perdesaan<br>
        <hr>
        <b>Warna Jalan</b><br>
        <i style="background:red; width:10px; height:10px; display:inline-block;"></i> Utama (Primary)<br>
        <i style="background:blue; width:10px; height:10px; display:inline-block;"></i> Sekunder<br>
        <i style="background:orange; width:10px; height:10px; display:inline-block;"></i> Trunk
     </div>
'''
m.get_root().html.add_child(folium.Element(legend_html))

# --- 7. TAMPILKAN DI STREAMLIT ---
st.title("PGI Business Heatmap Analysis")
st.write(f"Menampilkan data dari {len(df_clean)} lokasi cabang.")
st.components.v1.html(m._repr_html_(), height=1000)
