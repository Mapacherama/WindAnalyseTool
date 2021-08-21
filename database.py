
from geopy import location, location
import streamlit as st
import datetime
import plotly.graph_objects as go
import pandas as pd
from windrose import WindroseAxes
from matplotlib import pyplot as plt
import matplotlib.cm as cm
import numpy as np
import requests
import json
import time
import calendar
import time
from geopy.geocoders import Nominatim
from geopy.extra.rate_limiter import RateLimiter
from sqlalchemy import create_engine

df_wind_information_scheveningen_2010_2021 = pd.read_csv(
    "EHSA-Scheveningen 2010-2021.csv", sep=","
)

df_wind_information_marseille_2010_2021 = pd.read_csv(
    "LFTH-Marseille 2010-2021.csv", sep=","
)


# https://oege.ie.hva.nl/phpmyadmin/index.php
engine = create_engine(
    "mysql+mysqlconnector://tesselj2:VLYSwTwXGJKYI3@oege.ie.hva.nl/ztesselj2"
)


df_wind_information_scheveningen_2010_2021.to_sql(name='dataScheveningen', con=engine,
                                                  index=False, chunksize=1000)

df_wind_information_marseille_2010_2021.to_sql(name='dataMarseille', con=engine,
                                               index=False, chunksize=1000)


# Informatie over de data die van de https://mesonet.agron.iastate.edu/request/download.phtml?network=FR__ASOS website afkomt. Eerst de drie
# dichtstbijzijnde weerststations van Scheveningen, daarna Marseille.


