import requests
import json
import re

import pandas as pd
import pydeck as pdk
import streamlit as st
import numpy as np

from pathlib import Path

from analyse import pie_chart_pdm, do_barplot_count_cinema, do_bar_plot_var, do_bar_plot_ratio
from analyse import do_plot_ratio_seances_entree


@st.cache
def load_data():
    """Load dataframe cinema.

    Returns
    -------
    DataFrame
        Données cinéma.

    """
    path = Path(__file__).resolve().parent
    df = pd.read_csv(path / '../data/etablissements-cinematographiquesculture2018.csv', sep=';')
    df.loc[:, 'Personne par seance'] = (df['entrées 2019'] / df['séances']).astype(int)
    df.loc[:, 'Taux occupation par seance'] = 100 * (df['Personne par seance'] * df['écrans']
                                                     / df['fauteuils'])
    df.loc[df['PdM en entrées des films Art et Essai'] >= 70,
           'Type de cinéma'] = 'Cinéma art et essai'
    df.loc[df['PdM en entrées des films Art et Essai'] < 70,
           'Type de cinéma'] = 'Cinéma classique'

    return df


def get_coord(coords):
    """Récupere les coordonés d'une adresse / CP.

    Parameters
    ----------
    coords : str
        adresse / CP.

    Returns
    -------
    list
        Coordonés.

    """
    if coords == '':
        return [np.nan]
    coords = re.sub(r'\s+', r'\+', coords)
    url = 'https://api-adresse.data.gouv.fr/search/?q={}'.format(coords)

    response = requests.get(url)

    # Check status API
    if response.status_code == 200:
        data = json.loads(response.text)
    else:
        raise Exception('API error: {}'.format(response.status_code))

    # Controle si il a trouvé une addresse
    try:
        longlat = data['features'][0]['geometry']['coordinates']
    except IndexError:
        st.text('Addresse invalide')
        return []
    # Nom et Type de cinéma sont necessaires pour l'affichage
    return [{'nom': 'Vous-êtes ici', 'Type de cinéma': '',
             'lat': longlat[1], 'long': longlat[0]}]


def haversine(lon1, lat1, lon2, lat2):
    """https://stackoverflow.com/a/4913653 .

    Calculate the great circle distance in kilometers between two points
    on the earth (specified in decimal degrees)

    Parameters
    ----------
    lon1 : float
        Longitude point 1.
    lat1 : float
        Latitude point 1.
    lon2 : float
        Longitude point 2.
    lat2 : float
        Latitude point 2.

    Returns
    -------
    type
        Distance en km.

    """
    # convert decimal degrees to radians
    lon1, lat1, lon2, lat2 = [np.radians(x) for x in [lon1, lat1, lon2, lat2]]

    # haversine formula
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = np.sin(dlat / 2)**2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon / 2)**2
    c = 2 * np.arcsin(np.sqrt(a))
    # Radius of earth in kilometers
    r = 6371
    return c * r


def create_map(data, lay=[], use_data=True):
    """Create map.

    Parameters
    ----------
    data : DataFrame
        Données à utiliser pour initiliaser la carte.
    lay : list / Layer
        Layer ou list of Layers à ajouter à la carte.
    use_data : bool
        Si visuliser data ou l'utiliser seulement pour fixer le zoom du debut.

    """
    # Check if layer is a list, if not create a single item list
    if not isinstance(lay, list):
        lay = [lay]

    if use_data:
        # Add a layer avec data to all the layers to be plot
        layers = [pdk.Layer('ScatterplotLayer',
                            data=data,
                            pickable=True,
                            autoHighlight=True,
                            get_position='[longitude, latitude]',
                            get_color='[200, 30, 0, 160]',
                            radius_scale=10,
                            radius_min_pixels=5,
                            radius_max_pixels=50,
                            )] + lay
    else:
        layers = lay

    # Create the map, use data to set the intial position and zoom,
    # on hover show the content of the columns nom and Type de cinéma
    st.pydeck_chart(pdk.Deck(map_style='mapbox://styles/mapbox/light-v9',
                             initial_view_state=pdk.data_utils
                                                   .viewport_helpers
                                                   .compute_view(data[['longitude', 'latitude']]),
                             layers=layers,
                             tooltip={"html": "<b>{nom} <br />{Type de cinéma}"}))


# SETTING PAGE CONFIG TO WIDE MODE
st.set_page_config(layout="wide")

# Titre
st.title('Cinema finder')

data = load_data()

# Divise la page en 2 colonnes, une le double de l'autre en largeur
col1, col2 = st.columns([2, 1])

with col2:
    # Right column
    # Plot the figure returned by function
    st.pyplot(do_barplot_count_cinema(data, "DEP", 'Nombre cinéma', 'Département',
                                      'Nombre de cinéma par département'))
    # Catch the input text
    address = st.text_input(label='Vous ete où ? Addresse ou CP',
                            value="", placeholder='E.g. : 58 Bd Gouvion-Saint-Cyr')

    if len(address) > 0:
        pointpos = get_coord(address)
        if len(pointpos) > 0:
            # data is cached by streamlit, to not have to load it at each refresh
            # Changing it would lead to erros => copy of the DataFrame
            df = data.copy(deep=True)

            # Calculate distance
            df.loc[:, 'Distance (km)'] = df.apply(lambda x: haversine(x['longitude'], x['latitude'],
                                                                      pointpos[0]['long'],
                                                                      pointpos[0]['lat']),
                                                  axis=1)
            # Take n smallest, ascending order
            df_proche = df.nsmallest(10, 'Distance (km)').reset_index(drop=True)

            st.text('Le cinema le plus proche est le {},  \n'.format(df_proche.iloc[0]['nom'])
                    + 'en {}, {},  \nau {:.2f} km de distance.'.format(df_proche.iloc[0]['adresse'],
                                                                       df_proche.iloc[0]['commune'],
                                                                       df_proche.iloc[0]['Distance (km)']))

            # Plot the figure returned by function with the filtered df
            st.pyplot(pie_chart_pdm(df_proche, "Répartition des parts de marché"))
    else:
        pointpos = []
        # Plot the figure returned by function with all the data
        st.pyplot(pie_chart_pdm(data, "Répartition des parts de marché"))


with col1:
    # Left column
    if len(pointpos) > 0:
        # If we have an address
        # Layer with the given point in green
        laypos = pdk.Layer('ScatterplotLayer',
                           data=pd.DataFrame(pointpos),
                           pickable=True,
                           get_position='[long, lat]',
                           get_color='[26, 225, 53, 160]',
                           radius_scale=10,
                           radius_min_pixels=5,
                           radius_max_pixels=50)

        # If more columns than necessary are passed, we have errors
        col_show = ['nom', 'Type de cinéma', 'longitude', 'latitude']
        # Layer cinema art et essai in blue
        layart = pdk.Layer('ScatterplotLayer',
                           data=df_proche[df_proche['Type de cinéma'] == 'Cinéma art et essai'][col_show],
                           pickable=True,
                           get_position='[longitude, latitude]',
                           get_color='[146, 168, 209, 500]',
                           radius_scale=10,
                           radius_min_pixels=5,
                           radius_max_pixels=50)
        # Layer cinema classique in red
        layclass = pdk.Layer('ScatterplotLayer',
                             data=df_proche[df_proche['Type de cinéma'] == 'Cinéma classique'][col_show],
                             pickable=True,
                             get_position='[longitude, latitude]',
                             get_color='[200, 30, 0, 200]',
                             radius_scale=10,
                             radius_min_pixels=5,
                             radius_max_pixels=50)

        # create map with all the layers, using the full dataframe only to set the zoom
        create_map(df_proche[col_show], [laypos, layart, layclass], use_data=False)

        df_show = df_proche[['nom', 'adresse', 'commune', 'Distance (km)',
                             'Personne par seance',
                             'Type de cinéma']].fillna('')

        # Show the table, highlight the closer distance,
        # format the numbers and color the Type of cinema cells
        st.dataframe(df_show.style.highlight_min(subset=['Distance (km)'], color='#ffef96', axis=0)\
                                  .format({'Distance (km)': "{:.2f}"})
                                  .apply(lambda x: ["background: #92a8d1"
                                                    if (i == len(df_show.columns) - 1)
                                                    and (x['Type de cinéma'] == 'Cinéma art et essai')
                                                    else "background: #eea29a"
                                                    if (i == len(df_show.columns) - 1)
                                                    and (x['Type de cinéma'] == 'Cinéma classique')
                                                    else '' for i, v in enumerate(x)],
                                         axis=1), height=1000)

    else:
        # If we do not have an address, create a map of all France
        create_map(data[['nom', 'Type de cinéma', 'longitude', 'latitude']])

# After the previous columns, create three columns with equal size
col3, col4, col5 = st.columns([1, 1, 1])
with col3:
    if len(pointpos) > 0:
        st.pyplot(do_bar_plot_var(df_proche, "écrans", "", "nombre écrans",
                                  "Répartition des écrans"))
with col4:
    if len(pointpos) > 0:
        st.pyplot(do_bar_plot_ratio(df_proche, "fauteuils", "écrans", "",
                                    "nombre fauteuils par écran",
                                    "Répartition de la moyenne de fauteuils par écran"))

with col5:
    if len(pointpos) > 0:
        st.pyplot(do_plot_ratio_seances_entree(df_proche, "Taux occupation moyenne d'une salle (%)",
                                               "Taux occupation par seance"))
