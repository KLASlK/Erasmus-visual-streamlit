import streamlit as st
import polars as pl
import folium as fo
from streamlit_folium import st_folium
from typing import Dict, List

# Debug data
try:
    schools_source = pl.read_excel("schools.xlsx") # Schools_source je "nedotknutelná" zdrojová tabulka; kdo se jí pokusí modifikovat, toho zabiju
except:
    schools_source = pl.DataFrame({
        "name":["School 1", "School 2", "School 3", "School 4"],
        "country":["Spain", "Spain", "Czechia", "Mars"],
        "study":["Maths", "Chemistry", "Maths", "Biology"],
        "latitude":[50.5, 47.8, 67.1, 55.555],
        "longtitude":[14.25, 22.74, 37.8, 44.444]
        })

#TODO: Obecně hodně těhle deklarací je sketch. Trochu se na to kouknout a optimalizovat.
schools:pl.DataFrame = schools_source.select("name", "country", "study") # Schools je subtabulka sloužící k filtrování a jiným sussy operacím. Asi tady deklarována zbytečně vysoko.
picks = schools.to_dict() # Dictionary s filtrovacími klíčovými slovíčky pro každý sloupeček
for column in picks.keys():
    picks[column] = ["---"]  + picks[column].unique(maintain_order=True).to_list()

def filter_schools(school_df:pl.DataFrame) -> pl.DataFrame:
    """Funkce na profiltrování škol dle více podmínek."""
    filtered = school_df
    filter_choice = []

    for column in filtered.columns:
        if column not in st.session_state: # Teoreticky by se nemělo stát (st.multiselect inicializuje ten column jako prázdný seznam, takže bude v session state)
            continue

        if len(st.session_state[column]) > 0:
            filter_choice.append(pl.col(column).is_in(st.session_state[column])) 
        
    if len(filter_choice) < 1: # Pokud nejsou žádný podmínky, dej filtru vždycky pravdivou podmínku
        filter_choice = [True]
    print(filter_choice)

    return filtered.filter(filter_choice)

st.header("UJEP PRF Erasmus")
st.divider()

# --- TABULKA ---

# Filtrování
filters = st.columns(len(schools.columns)) # Sloupečky s filtry
for index, column in enumerate(schools.columns):
    with filters[index]:
        st.session_state[column] = st.multiselect(label=column, options=picks[column]) # Samotné filtry, NOTE: This is kinda stupid?

schools = filter_schools(schools_source)
schools_sub = schools.select("name", "country", "study")

st.table(schools_sub)

# --- MAPA --- TODO: Mapa pod tabulkou je hodně špatnej design. Pokud ta tabulka bude moc velká, bude to chtít hodně scrollování před nalezením mapy. Posunout mapu nahoru, nebo aspoň vedle tabulky.
# WE FOLIUM UP IN THIS HOE
# Hranice mapy
max_lat, min_lat = 75, 33
max_long, min_long = 65, -31

# Inicializace mapy
europe = fo.Map(
    [50.5, 14.25],
    zoom_start=4, # Počáteční krok přiblížení, čím menší tím oddálenější
    max_bounds=True, # Omezení tahání vedle
    min_lat=min_lat,
    max_lat=max_lat,
    min_lon=min_long,
    max_lon=max_long
)

# Vytvoření Markerů na mapě
# Extrahování koordinací z dataframeu #TODO: Tohle je extrémně špatný přístup. Holy fuck.
coords = zip(schools.to_series(schools.get_column_index("name")).to_list(),schools.to_series(schools.get_column_index("latitude")).to_list(),schools.to_series(schools.get_column_index("longtitude")).to_list())
# Iterace a zapsání do mapy
for coord in coords:
    fo.Marker(
        location=[coord[1], coord[2]],
        popup=fo.Popup(coord[0])
    ).add_to(europe)

# Body ilustrující kam až lze tahat "kameru" (debug only)
fo.CircleMarker([max_lat, max_long]).add_to(europe)
fo.CircleMarker([max_lat, min_long]).add_to(europe)
fo.CircleMarker([min_lat, max_long]).add_to(europe)
fo.CircleMarker([min_lat, min_long]).add_to(europe)

# Spuštění (thank you based open-source contributors)
st_folium(europe, use_container_width=True)

#st.session_state