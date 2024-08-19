import streamlit as st
import json
import folium
import geopandas as gpd
from streamlit_folium import st_folium
from folium.plugins import Fullscreen
import os

# CSS pour personnaliser le style de la page et ajuster les marges
st.markdown("""
    <style>
    body {
        font-family: 'Arial', sans-serif;
        background-color: #f5f5f5;
    }
    .main-title {
        background-color: #4CAF50;
        color: white;
        padding: 20px;
        text-align: center;
        border-radius: 8px;
        font-size: 32px;
    }
    .section-title {
        color: #4CAF50;
        margin-top: 20px;
        font-size: 24px;
        border-bottom: 2px solid #4CAF50;
        padding-bottom: 10px;
    }
    .description {
        font-size: 18px;
        margin-bottom: 20px;
    }
    .sidebar .sidebar-content {
        background-color: #ffffff;
        padding: 15px;
        border-radius: 8px;
        box-shadow: 0 0 10px rgba(0,0,0,0.1);
    }
    .stButton button {
        background-color: #4CAF50 !important;
        border: none;
        color: white !important;
        padding: 10px 20px;
        text-align: center;
        text-decoration: none;
        display: inline-block;
        font-size: 16px;
        margin: 4px 2px;
        cursor: pointer;
        border-radius: 8px;
    }
    .map-container {
        width: 100%;
        margin: 0;
    }
    .leaflet-container {
        width: 100% !important;
        height: 100% !important;
    }
    </style>
    """, unsafe_allow_html=True)


# Titre de la page avec un style personnalisé
st.markdown('<div class="main-title">Résultats de l\'agrégation</div>', unsafe_allow_html=True)

# Explication sur l'interprétation de l'indice d'allongement
st.markdown('<div class="section-title">Interprétation de l\'indice d\'allongement</div>', unsafe_allow_html=True)
st.markdown("""
L'indice d'allongement d'un polygone est un rapport entre sa longueur et sa largeur maximales. 
- **Indice d'allongement proche de 1** : le polygone est proche d'une forme carrée ou circulaire.
- **Indice d'allongement élevé** : le polygone est très allongé, ce qui peut indiquer une forme linéaire ou irrégulière.
Cet indice est utilisé pour identifier la compacité ou l'étirement d'une parcelle.
""")

# Fonction pour charger, reprojeter et filtrer le GeoJSON
def load_and_reproject_geojson(filepath, surf_column, elongation_threshold=None, surface_threshold=None):
    with open(filepath, 'r') as file:
        data = json.load(file)
    gdf = gpd.GeoDataFrame.from_features(data['features'])
    gdf = gdf.set_crs(epsg=2154).to_crs(epsg=4326)
    if elongation_threshold is not None:
        gdf = gdf[gdf['elongation_index'] >= elongation_threshold]
    if surface_threshold is not None and surf_column in gdf.columns:
        gdf = gdf[gdf[surf_column] >= surface_threshold]
    reprojected_geojson = json.loads(gdf.to_json())
    return reprojected_geojson, gdf


# Construire des chemins relatifs pour les fichiers GeoJSON
base_dir = os.path.dirname(__file__)  # Répertoire où se trouve app.py

file_paths = {
    'Catégorie 1': (os.path.join(base_dir, 'data/Allongement_suite_agreg_C_1_test.geojson'), 'surf_poly_agreg'),
    'Catégorie 2': (os.path.join(base_dir, 'data/Allongement_suite_agreg_C_2_test.geojson'), 'surf_agreg_c_2'),
    'Catégorie 3': (os.path.join(base_dir, 'data/Allongement_suite_agreg_C_3_test.geojson'), 'surf_poly_agreg_c3')
}


# Choisir la "page" avec une clé unique
page = st.sidebar.selectbox("Navigation", ["Accueil", "Carte des Polygones", "Parcelles Filtrées"], key="page_selectbox")

# Accueil
if page == "Accueil":
    st.markdown('<div class="section-title">Bienvenue sur l\'application</div>', unsafe_allow_html=True)
    st.markdown("""
    Utilisez le menu de navigation pour accéder aux différentes sections de l'application :
    - **Carte des Polygones** : Visualisez les polygones filtrés sur une carte.
    - **Parcelles Filtrées** : Consultez les parcelles qui composent les polygones filtrés.
    """)

# Carte des Polygones
elif page == "Carte des Polygones":
    selected_layer = st.sidebar.selectbox("Choisissez la catégorie à afficher", list(file_paths.keys()), key="category_selectbox")
    selected_file_path, surf_column = file_paths[selected_layer]
    _, gdf_full = load_and_reproject_geojson(selected_file_path, surf_column)

    min_index = gdf_full['elongation_index'].min()
    max_index = gdf_full['elongation_index'].max()

    elongation_threshold = st.sidebar.slider(
        "Afficher les polygones avec un indice d'allongement supérieur à",
        float(min_index), float(max_index), float(min_index), key="elongation_slider"
    )


    if surf_column in gdf_full.columns:
        min_surface = gdf_full[surf_column].min()
        max_surface = gdf_full[surf_column].max()

        surface_threshold = st.sidebar.slider(
            "Afficher les polygones avec une surface supérieure à",
            float(min_surface), float(max_surface), float(min_surface), key="surface_slider"
        )
    else:
        surface_threshold = None
        st.sidebar.write(f"La colonne '{surf_column}' n'existe pas dans cette catégorie. Le filtrage par surface est désactivé.")

    geojson_data, filtered_gdf = load_and_reproject_geojson(
        selected_file_path, 
        surf_column,
        elongation_threshold=elongation_threshold, 
        surface_threshold=surface_threshold
    )

    st.markdown('<div class="section-title">Nombre de polygones après filtrage</div>', unsafe_allow_html=True)
    st.write(f"{len(filtered_gdf)} polygones")

    # Définir une couleur pour chaque catégorie
    colors = {
        'Catégorie 1': 'red',
        'Catégorie 2': 'blue',
        'Catégorie 3': 'green'
    }

    # Créer la carte avec Folium
    m = folium.Map(location=[48.8566, 2.3522], zoom_start=9)

    if not filtered_gdf.empty:
        folium.GeoJson(
            geojson_data,
            style_function=lambda x: {
                'color': colors[selected_layer],
                'weight': 2,
                'fillOpacity': 1.0
            }
        ).add_to(m)
        bounds = filtered_gdf.total_bounds
        m.fit_bounds([[bounds[1], bounds[0]], [bounds[3], bounds[2]]])

    # Ajouter le bouton plein écran
    Fullscreen(position='topright', title='Plein écran', title_cancel='Quitter le plein écran').add_to(m)

    # Afficher la carte interactive avec des marges réduites sur les côtés, en 16:9
    st.markdown('<div class="map-container">', unsafe_allow_html=True)
    st_folium(m, width=1600, height=675)  # Format 16:9
    st.markdown('</div>', unsafe_allow_html=True)

# Parcelles Filtrées
elif page == "Parcelles Filtrées":
    selected_layer = st.sidebar.selectbox("Choisissez la catégorie à afficher", list(file_paths.keys()), key="category_selectbox_parcelles")
    selected_file_path, surf_column = file_paths[selected_layer]
    _, gdf_full = load_and_reproject_geojson(selected_file_path, surf_column)

    min_index = gdf_full['elongation_index'].min()
    max_index = gdf_full['elongation_index'].max()

    elongation_threshold = st.sidebar.slider(
        "Afficher les polygones avec un indice d'allongement supérieur à",
        float(min_index), float(max_index), float(min_index), key="elongation_slider_parcelles"
        )

    if surf_column in gdf_full.columns:
        min_surface = gdf_full[surf_column].min()
        max_surface = gdf_full[surf_column].max()

        surface_threshold = st.sidebar.slider(
            "Afficher les polygones avec une surface supérieure à",
            float(min_surface), float(max_surface), float(min_surface), key="surface_slider_parcelles"
        )
        
    else:
        surface_threshold = None
        st.sidebar.write(f"La colonne '{surf_column}' n'existe pas dans cette catégorie. Le filtrage par surface est désactivé.")

    # Filtrer les polygones en fonction des seuils choisis
    _, filtered_gdf = load_and_reproject_geojson(
        selected_file_path, 
        surf_column,
        elongation_threshold=elongation_threshold, 
        surface_threshold=surface_threshold
    )

    st.markdown('<div class="section-title">Parcelles qui composent les polygones filtrés</div>', unsafe_allow_html=True)

    # Afficher les parcelles_composantes sous forme de tableau
    if 'parcelles_composantes' in filtered_gdf.columns:
        parcelles_df = filtered_gdf[['parcelles_composantes']]
        st.dataframe(parcelles_df.explode('parcelles_composantes').reset_index(drop=True))
    else:
        st.write("Aucune parcelle correspondante à afficher avec les critères actuels.")
