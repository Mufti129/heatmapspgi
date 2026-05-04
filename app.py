import folium
from folium.plugins import HeatMap

# 1. Inisialisasi Map Utama
m = folium.Map(location=[df_clean['lat'].mean(), df_clean['lon'].mean()],
               zoom_start=11,
               tiles='CartoDB positron')

# 2. Siapkan Feature Groups
fg_list = {
    'omzet': folium.FeatureGroup(name='Sebaran Omzet (Aktual)'),
    'umk': folium.FeatureGroup(name='Sebaran UMK', show=False),
    'cabang': folium.FeatureGroup(name='Lokasi Cabang (Kota vs Desa)'),
    'ruko': folium.FeatureGroup(name='Sebaran Lebar Ruko', show=False),
    'penduduk': folium.FeatureGroup(name='Sebaran Penduduk', show=False),
    'ponsel': folium.FeatureGroup(name='Sebaran Toko Ponsel', show=False),
    'kompetitor': folium.FeatureGroup(name='Sebaran Kompetitor', show=False),
    'jalan': folium.FeatureGroup(name='Lokasi Jalan')
}

# 3. Tambahkan Heatmaps (Gunakan list comprehension agar lebih cepat)
HeatMap([[r.lat, r.lon, r.avg_omzet] for r in df_clean.itertuples()], radius=15, blur=20, 
        gradient={0.4: 'blue', 0.7: 'lime', 1: 'yellow'}).add_to(fg_list['omzet'])

HeatMap([[r.lat, r.lon, r.umk] for r in df_clean.itertuples()], radius=15, blur=20,
        gradient={0.4: 'purple', 0.7: 'red', 1: 'orange'}).add_to(fg_list['umk'])

# ... (tambahkan HeatMap lainnya dengan pola yang sama)

# 4. Loop Tunggal untuk Marker (Lebih Efisien)
for i, row in df_clean.iterrows():
    # Logika Warna Wilayah
    color_wilayah = 'red' if row['kategori_wilayah'] == 'Perkotaan' else 'blue' if row['kategori_wilayah'] == 'Perdesaan' else 'black'
    
    # Logika Warna Jalan
    road_map = {'primary': 'red', 'tertiary': 'red', 'residential': 'beige', 'trunk': 'orange', 'secondary': 'blue', 'living_street': 'purple'}
    color_jalan = road_map.get(row['jalan'], 'black')

    popup_content = f"""
        <b>Cabang:</b> {row['nama_cabang']}<br>
        <b>Omzet:</b> Rp{row['avg_omzet']:,.0f}<br>
        <b>Jalan:</b> {row['jalan']}<br>
        <b>Penduduk:</b> {row['penduduk']:,.0f}
    """

    # Marker Wilayah
    folium.CircleMarker(location=[row['lat'], row['lon']], radius=5, color=color_wilayah,
                        fill=True, fill_opacity=0.7, popup=popup_content).add_to(fg_list['cabang'])
    
    # Marker Jalan
    folium.CircleMarker(location=[row['lat'], row['lon']], radius=5, color=color_jalan,
                        fill=True, fill_opacity=0.3, popup=popup_content).add_to(fg_list['jalan'])

# 5. Masukkan semua layer ke peta
for fg in fg_list.values():
    fg.add_to(m)

folium.LayerControl(collapsed=False).add_to(m)

# 6. Legenda yang Sinkron
legend_html = '''
     <div style="position: fixed; 
                 bottom: 50px; left: 50px; width: 220px; height: 280px; 
                 border:2px solid grey; z-index:9999; font-size:12px;
                 background-color:white; opacity:0.9; padding: 10px;
                 ">
        <b>Kategori Wilayah (Circle)</b><br>
        <i style="background:red;">&nbsp;&nbsp;</i> Perkotaan<br>
        <i style="background:blue;">&nbsp;&nbsp;</i> Perdesaan<br>
        <i style="background:black;">&nbsp;&nbsp;</i> Perkampungan<br><br>
        <b>Tipe Jalan</b><br>
        <i style="background:red;">&nbsp;&nbsp;</i> Primary/Tertiary<br>
        <i style="background:beige; border:1px solid black;">&nbsp;&nbsp;</i> Residential<br>
        <i style="background:orange;">&nbsp;&nbsp;</i> Trunk<br>
        <i style="background:blue;">&nbsp;&nbsp;</i> Secondary<br>
        <i style="background:purple;">&nbsp;&nbsp;</i> Living Street
     </div>
'''
m.get_root().html.add_child(folium.Element(legend_html))
m
