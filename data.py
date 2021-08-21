from geopy import location, location
import streamlit as st
import datetime
import plotly.graph_objects as go
import pandas as pd
import altair as alt
import plotly.figure_factory as ff
from bokeh.plotting import figure
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
from dateutil.relativedelta import relativedelta
import seaborn as sns

st.set_page_config(
    page_title="BD1",
    page_icon="https://4.bp.blogspot.com/-iDZFSQtoBcI/V6C6Ayh721I/AAAAAAAALIc/o9Y4EFym_zI0RS9AZxvm_d2SCCVuI59AQCLcB/s1600/Px187NDI5MTU4OS02LTgwMzYzMDg3.png",
)

def main():
    import json
    import time
    import requests
    import json
    from geopy import location, location
    import pyowm
    from pyowm import OWM
    from pyowm.utils import config
    from pyowm.utils import timestamps
    from pyowm.tiles.enums import MapLayerEnum
    import streamlit.components.v1 as components
    from sqlalchemy import create_engine

    st.markdown(
        """
        <style>
                .css-1aumxhk {
                background-color: rgb(255, 84, 0);
                background-image: linear-gradient(rgb(255, 108, 0), rgb(255, 255, 255));
                }    
        </style>
            """,
        unsafe_allow_html=True,
    )

    key = "3968f1db9458ba69835bd992cc65270d"

    menu = [
        "Home",
        "Windroos",
        "Eendaagstool",
        "Dataframe",
        "Verbanden",
        "Onderlinge verbanden",
        "Temperatuur",
        "Luchtdruk en -vochtigheid",
    ]
    choice = st.sidebar.selectbox("Kies tool", menu)

    engine = create_engine(
        "mysql+mysqlconnector://tesselj2:VLYSwTwXGJKYI3@oege.ie.hva.nl/ztesselj2"
    )
    connection = engine.raw_connection()

    if choice == "Home":
        st.subheader("")
        page_bg_img = """
        <style>
                body {
                background-image: url("https://images.unsplash.com/photo-1506527240747-720a3e17b910?ixid=MXwxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHw%3D&ixlib=rb-1.2.1&auto=format&fit=crop&w=1952&q=80");
                background-size: cover;
                }
        </style>
            """
        st.markdown(page_bg_img, unsafe_allow_html=True)

    elif choice == "Dataframe":
        st.write("""  # Wind analyse tool""")

        citynames = ["Scheveningen", "Marseille"]

        st.sidebar.header("User Input Parameters")

        today = datetime.date(2020, 8, 6)
        tommorow = datetime.date(2020, 8, 8)
        dateMin = datetime.date(2001, 1, 1)
        dateMax = datetime.date(2021, 5, 1)
        location = st.sidebar.selectbox("locaties", citynames)
        startDate = st.sidebar.date_input("Begin datum", today)
        endDate = st.sidebar.date_input("Eind datum", tommorow)
        startTime = st.sidebar.slider("Begin tijd", 0, 23, 12)
        endTime = st.sidebar.slider("Eind tijd", 0, 23, 12)

        data = {
            "Locatie": location,
            "Begin datum": startDate,
            "Eind datum": endDate,
            "Begin tijd": startTime,
            "Eind tijd": endTime,
        }

        # Here we use Nominatin to convert address to a latitude/longitude coordinates"
        geolocator = Nominatim(
            user_agent="data-visualistatie"
        )  # using open street map API
        Geo_Coordinate = geolocator.geocode(location)
        lat = Geo_Coordinate.latitude
        lon = Geo_Coordinate.longitude

        unix_time = calendar.timegm(
            time.strptime(str(startDate) + " 00:00:00", "%Y-%m-%d %H:%M:%S")
        )

        # Correct date and time from the user given input:
        unix_time_start_time = calendar.timegm(
            time.strptime(
                str(startDate) + " " + str((startTime - 2)) + ":00", "%Y-%m-%d %H:%M"
            )
        )

        unix_time_end_time = calendar.timegm(
            time.strptime(
                str(endDate) + " " + str((endTime - 2)) + ":00", "%Y-%m-%d %H:%M"
            )
        )

        # I use only hour and minute because that's the way the data is stored in the database.
        start_dt = datetime.datetime.fromtimestamp(unix_time_start_time).strftime(
            "%Y-%m-%d %H:%M"
        )

        end_dt = datetime.datetime.fromtimestamp(unix_time_end_time).strftime(
            "%Y-%m-%d %H:%M"
        )

        # Test query:

        cuDatabase = connection.cursor()

        query = (
            "SELECT * FROM data"
            + location
            + " WHERE valid >="
            + '"'
            + str(start_dt)
            + '"'
            + " AND valid < "
            + '"'
            + str(end_dt)
            + '"'
        )

        cuDatabase.execute(
            query,
        )

        rows = cuDatabase.fetchall()

        df_wind_information = pd.DataFrame(
            rows,
            columns=[
                "station",
                "valid",
                "lon",
                "lat",
                "elevation",
                "tmpc",
                "dwpc",
                "relh",
                "drct",
                "sknt",
                "mslp",
                "gust",
            ],
        )

        connection.commit()
        cuDatabase.close()

        def clean(df):
            df = df.drop(["lat", "lon", "elevation", "mslp", "gust"], axis=1)
            df = df.join(
                df["valid"]
                .str.split(" ", expand=True)
                .rename(columns={0: "Date", 1: "Time"})
            )
            df = df.drop(["valid"], axis=1)
            df["Date"] = pd.to_datetime(df["Date"])
            df = df.dropna()
            return df

        df = clean(df_wind_information)
        
        df = df.rename(
            columns={
                "station": "Station",
                "tmpc": "Temp",
                "dwpc": "Dew",
                "relh": "Humid",
                "drct": "Wind dir",
                "sknt": "Wind spd",
                "valid_date": "Date",
                "valid_time": "Time",
            }
        )

        # Filter the dataset to a specific date
        checkdate = st.date_input("Select date to compare: ", endDate)
        date_to_check = df["Date"] == pd.to_datetime(checkdate)
        df_filtered_dates = df.loc[date_to_check]
        st.dataframe(df_filtered_dates)

        # Select the row and column you want to compare
        col1, col2 = st.beta_columns([10, 10])
        with col1:
            row = st.selectbox("Select row to compare:", df_filtered_dates.index)
        with col2:
            rangecols = ["Temp", "Dew", "Humid", "Wind dir", "Wind spd"]
            column = st.selectbox(
                "Select column to compare to " + str(row) + " :", rangecols
            )

        # Select in wich range u want to compare this
        col3, col4, col5 = st.beta_columns([7, 7, 6])
        with col3:
            rangefrom = st.text_input(
                "Range " + str(column) + " from:", df.loc[row, column]
            )
        with col4:
            rangeto = st.text_input("To:", df.loc[row, column])
        with col5:
            sameday = st.checkbox("Only show same day")
            sametime = st.checkbox("Only show same time")

        st.dataframe(df.loc[[row]])
        
        # Filters
        def filter_dataframe():
            return df[
                (df[column].astype(float) >= float(rangefrom))
                & (df[column].astype(float) <= float(rangeto))
            ]

        def filtered_sameday(df_filtered):
            get_selected_date = df_filtered_dates["Date"].dt.strftime("%m-%d")
            get_monthday = get_selected_date.iloc[0]
            print(get_monthday)
            return df_filtered[
                pd.to_datetime(df_filtered["Date"]).dt.strftime("%m-%d") == get_monthday
            ]

        def filtered_sametime(df_filtered):
            get_selected_time = df_filtered_dates["Time"]
            get_time = get_selected_time.iloc[0]
            print(get_time)
            return df_filtered[pd.to_datetime(df_filtered["Time"]) == get_time]

        def filtered_samedayandtime(df_filtered):
            get_selected_date = df_filtered_dates["Date"].dt.strftime("%m-%d")
            get_monthday = get_selected_date.iloc[0]
            print(get_monthday)

            get_selected_time = df_filtered_dates["Time"]
            get_time = get_selected_time.iloc[0]
            print(get_time)

            return df_filtered[
                (
                    pd.to_datetime(df_filtered["Date"]).dt.strftime("%m-%d")
                    == get_monthday
                )
                & (pd.to_datetime(df_filtered["Time"]) == get_time)
            ]

        # Filters dataframe to range
        if sameday == False and sametime == False:
            st.dataframe(filter_dataframe())

        # Filters dataframe on date
        elif sameday == True and sametime == False:
            st.dataframe(filtered_sameday(filter_dataframe()))

        # Filters dataframe on time
        elif sametime == True and sameday == False:
            st.dataframe(filtered_sametime(filter_dataframe()))

        # Filters dataframe on both date and time
        else:

            st.dataframe(filtered_samedayandtime(filter_dataframe()))

    elif choice == "Eendaagstool":
        st.write("""  # Wind analyse tool""")

        citynames = ["Scheveningen", "Marseille"]

        st.sidebar.header("User Input Parameters")

        today = datetime.date(2020, 8, 6)
        tommorow = datetime.date(2020, 8, 7)
        dateMin = datetime.date(2001, 1, 1)
        dateMax = datetime.date(2021, 5, 1)
        location = st.sidebar.selectbox("locaties", citynames)
        startDate = st.sidebar.date_input("Begin datum", today)
        endDate = st.sidebar.date_input("Eind datum", tommorow)
        startTime = st.sidebar.slider("Begin tijd", 0, 23, 12)
        endTime = st.sidebar.slider("Eind tijd", 0, 23, 12)

        data = {
            "Locatie": location,
            "Begin datum": startDate,
            "Eind datum": endDate,
            "Begin tijd": startTime,
            "Eind tijd": endTime,
        }
        
        unix_time = calendar.timegm(
            time.strptime(str(startDate) + " 00:00:00", "%Y-%m-%d %H:%M:%S")
        )

        # Correct date and time from the user given input:
        unix_time_start_time = calendar.timegm(
            time.strptime(
                str(startDate) + " " + str((startTime - 2)) + ":00", "%Y-%m-%d %H:%M"
            )
        )

        unix_time_end_time = calendar.timegm(
            time.strptime(
                str(endDate) + " " + str((endTime - 2)) + ":00", "%Y-%m-%d %H:%M"
            )
        )

        # I use only hour and minute because that's the way the data is stored in the database.
        start_dt = datetime.datetime.fromtimestamp(unix_time_start_time).strftime(
            "%Y-%m-%d %H:%M"
        )

        end_dt = datetime.datetime.fromtimestamp(unix_time_end_time).strftime(
            "%Y-%m-%d %H:%M"
        )

        # Test query:
        cuDatabase = connection.cursor()
        query = (
            "SELECT * FROM data"
            + location
            + " WHERE valid >="
            + '"'
            + str(start_dt)
            + '"'
            + " AND valid < "
            + '"'
            + str(end_dt)
            + '"'
        )

        cuDatabase.execute(
            query,
        )

        rows = cuDatabase.fetchall()
        df_wind_information = pd.DataFrame(
            rows,
            columns=[
                "station",
                "valid",
                "lon",
                "lat",
                "elevation",
                "tmpc",
                "dwpc",
                "relh",
                "drct",
                "sknt",
                "mslp",
                "gust",
            ],
        )
        connection.commit()
        cuDatabase.close()

        def clean(df):
            df = df.drop(["lat", "lon", "elevation", "mslp", "gust"], axis=1)
            df = df.join(
                df["valid"]
                .str.split(" ", expand=True)
                .rename(columns={0: "valid_date", 1: "valid_time"})
            )
            df = df.drop(["valid"], axis=1)
            df["valid_date"] = pd.to_datetime(df["valid_date"])
            df = df.dropna()
            return df

        df = clean(df_wind_information)
        

        # Extracting windspeed and derection current
        real_time = []
        wind_direction = []
        wind_speed = []
        air_temp = []

        for index, row in df.iterrows():
            wind_direction.append(row["drct"])
            wind_speed.append(row["sknt"])
            air_temp.append(row["tmpc"])
            real_time.append(row["valid_time"])

        wind_direction = np.array(wind_direction)
        wind_speed = np.array(wind_speed)
        air_temp = np.array(air_temp)
        real_time = np.array(real_time)

        def degToCompass(num):
            
            # Devide angle and add tie
            val = int((num / 22.5) + 0.5)
            arr = [
                "N",
                "NNE",
                "NE",
                "ENE",
                "E",
                "ESE",
                "SE",
                "SSE",
                "S",
                "SSW",
                "SW",
                "WSW",
                "W",
                "WNW",
                "NW",
                "NNW",
            ]
            return arr[(val % 16)]

        cardinals = []

        # Make cardinals from dataframe
        for wind in wind_direction:
            cardinals.append(degToCompass(wind))
        
        # Avarage deriction 
        average_wind_direction = np.average(wind_direction)
        average_cardinal = degToCompass(average_wind_direction)

        fig, ax = plt.subplots()
        ax.set_title(
            "Day: "
            + str(startDate)
            + " until "
            + str(endDate)
            + "                 Average direction: "
            + str(average_cardinal)
        )

        time = range(len(wind_speed))
        ax.plot(
            real_time, wind_speed, linewidth=2, color="blue", marker=".", label="123"
        )

        plt.xticks(np.arange(0, 51, 5))
        ax.set_xlabel("Time of day (CEST)", fontsize=14)
        ax.set_ylabel("Wind speed (m/s)", color="blue", fontsize=14)
        ax.grid(True)

        for i, txt in enumerate(cardinals):
            ax.annotate(txt, (time[i], wind_speed[i]), size="8", weight="bold")

        ax2 = ax.twinx()
        ax2.plot(time, air_temp, linewidth=2, color="red")
        ax2.set_ylabel("Air temperature (°C)", color="red", fontsize=14)

        st.pyplot(plt)

    elif choice == "Windroos":
        st.write("""  # Wind analyse tool""")
        # import city list
        with open(r"citylist.json", encoding="utf8") as f:
            citylist = json.load(f)

        citynames = ["Marseille", "Scheveningen"]

        st.sidebar.header("User Input Parameters")
        today = datetime.date(2020, 8, 6)
        tommorow = datetime.date(2020, 8, 8)
        dateMin = datetime.date(2001, 1, 1)
        dateMax = datetime.date(2021, 5, 1)
        location = st.sidebar.selectbox("locaties", citynames)
        startDate = st.sidebar.date_input("Begin datum", today, dateMin, dateMax)
        endDate = st.sidebar.date_input("Eind datum", tommorow, dateMin, dateMax)
        startTime = st.sidebar.slider("Begin tijd", 0, 23, 12)
        endTime = st.sidebar.slider("Eind tijd", 0, 23, 12)

        data = {
            "Locatie": location,
            "Begin datum": startDate,
            "Eind datum": endDate,
            "Begin tijd": startTime,
            "Eind tijd": endTime,
        }
        features = pd.DataFrame(data, index=[0])

        # Here we use Nominatin to convert address to a latitude/longitude coordinates"
        geolocator = Nominatim(
            user_agent="data-visualistatie"
        )  # using open street map API
        Geo_Coordinate = geolocator.geocode(location)
        lat = Geo_Coordinate.latitude
        lon = Geo_Coordinate.longitude

        # Needs API call to convert time to unixtimestamp
        # unix_time = 1615287481 # Parameter is time
        unix_time = calendar.timegm(
            time.strptime(str(startDate) + " 00:00:00", "%Y-%m-%d %H:%M:%S")
        )

        # Correct date and time from the user given input:

        unix_time_start_time = calendar.timegm(
            time.strptime(
                str(startDate) + " " + str((startTime - 2)) + ":00", "%Y-%m-%d %H:%M"
            )
        )

        unix_time_end_time = calendar.timegm(
            time.strptime(
                str(endDate) + " " + str((endTime - 2)) + ":00", "%Y-%m-%d %H:%M"
            )
        )

        dt = datetime.datetime.fromtimestamp(unix_time).strftime("%Y-%m-%d %H:%M:%S")

        # Only hour and minute because that's the way the data is stored in the database.
        start_dt = datetime.datetime.fromtimestamp(unix_time_start_time).strftime(
            "%Y-%m-%d %H:%M"
        )

        end_dt = datetime.datetime.fromtimestamp(unix_time_end_time).strftime(
            "%Y-%m-%d %H:%M"
        )

        cuDatabase = connection.cursor()

        query = (
            "SELECT * FROM data"
            + location
            + " WHERE valid >="
            + '"'
            + str(start_dt)
            + '"'
            + " AND valid < "
            + '"'
            + str(end_dt)
            + '"'
        )

        cuDatabase.execute(
            query,
        )

        rows = cuDatabase.fetchall()

        df_wind_information = pd.DataFrame(
            rows,
            columns=[
                "station",
                "valid",
                "lon",
                "lat",
                "elevation",
                "tmpc",
                "dwpc",
                "relh",
                "drct",
                "sknt",
                "mslp",
                "gust",
            ],
        )

        connection.commit()
        cuDatabase.close()

        # Openweather API call
        API = (
            "http://api.openweathermap.org/data/2.5/onecall/timemachine?lat="
            + str(lat)
            + "&lon="
            + str(lon)
            + "&dt="
            + str(unix_time)
            + "&appid="
            + key
        )

        # Read JSON
        response = requests.get(API)

        def jprint(obj):
            # create a formatted string of the Python JSON object
            text = json.dumps(obj, sort_keys=True, indent=4)

        def read_CSV(cityname):
            if cityname == "Marseille":
                return pd.read_csv("LFTH-Marseille 2010-2021.csv")
            if cityname == "Scheveningen":
                return pd.read_csv("EHSA-Scheveningen 2010-2021.csv")

        def split(df, percentage):
            return df.head(int(len(df) * (percentage / 100)))

        def timesceme(df, start_date, end_date, start_time, end_time):
            startdate = pd.to_datetime(start_date)
            enddate = pd.to_datetime(end_date)

            after_start_date = df["valid_date"] >= startdate
            before_end_date = df["valid_date"] <= enddate

            between_two_dates = after_start_date & before_end_date
            filtered_dates = df.loc[between_two_dates]
            return filtered_dates

        def clean(df):
            df = df.drop(["lat", "lon", "elevation", "mslp", "gust"], axis=1)
            df = df.join(
                df["valid"]
                .str.split(" ", expand=True)
                .rename(columns={0: "valid_date", 1: "valid_time"})
            )
            df = df.drop(["valid"], axis=1)
            df["valid_date"] = pd.to_datetime(df["valid_date"])
            df = df.dropna()
            return df

        df = read_CSV(location)
        df = clean(df)
        df = timesceme(df, startDate, endDate, startTime, endTime)

        ax = WindroseAxes.from_ax()
        ax.bar(df.drct, df.sknt, normed=True, opening=0.8, edgecolor="white")
        ax.set_legend()

        st.pyplot(ax.figure)

    elif choice == "Temperatuur":
        st.write("""# Weersverwachting """)
        citynames = ["Marseille", "Scheveningen"]
        st.sidebar.header("User Input Parameters")
        location = st.sidebar.selectbox("locaties", citynames)

        geolocator = Nominatim(
            user_agent="data-visualistatie"
        )  # using open street map API
        Geo_Coordinate = geolocator.geocode(location)
        lat = Geo_Coordinate.latitude
        lon = Geo_Coordinate.longitude

        API = (
            "https://api.openweathermap.org/data/2.5/onecall?lat={}&lon={}&exclude=current,minutely,hourly,alerts&units=metric&appid=".format(
                lat, lon
            )
            + key
        )
        response = requests.get(API)
        dataMap = response.json()

        st.write("Gemiddelde Temperatuur van de komende 7 dagen")
        dag0 = dataMap["daily"][0]["temp"]["day"]
        dag1 = dataMap["daily"][1]["temp"]["day"]
        dag2 = dataMap["daily"][2]["temp"]["day"]
        dag3 = dataMap["daily"][3]["temp"]["day"]
        dag4 = dataMap["daily"][4]["temp"]["day"]
        dag5 = dataMap["daily"][5]["temp"]["day"]
        dag6 = dataMap["daily"][6]["temp"]["day"]
        dag7 = dataMap["daily"][7]["temp"]["day"]
        voorspeldeTemp = {dag0, dag1, dag2, dag3, dag4, dag5, dag6, dag7}
        st.write(voorspeldeTemp)
        st.bar_chart(voorspeldeTemp)

        dag0 = dataMap["daily"][0]["temp"]["day"]
        dag1 = dataMap["daily"][1]["temp"]["day"]
        dag2 = dataMap["daily"][2]["temp"]["day"]
        dag3 = dataMap["daily"][3]["temp"]["day"]
        dag4 = dataMap["daily"][4]["temp"]["day"]
        dag5 = dataMap["daily"][5]["temp"]["day"]
        dag6 = dataMap["daily"][6]["temp"]["day"]
        dag7 = dataMap["daily"][7]["temp"]["day"]
        voorspeldeTemp = {dag0, dag1, dag2, dag3, dag4, dag5, dag6, dag7}
        st.write(voorspeldeTemp)
        st.line_chart(voorspeldeTemp)

    elif choice == "Luchtdruk en -vochtigheid":
        st.write("""# Verwachtingen komende 7 dagen """)
        citynames = [
            "Marseille",
            "Scheveningen",
        ]
        st.sidebar.header("User Input Parameters")
        location = st.sidebar.selectbox("locaties", citynames)

        geolocator = Nominatim(
            user_agent="data-visualistatie"
        )  # using open street map API
        Geo_Coordinate = geolocator.geocode(location)
        lat = Geo_Coordinate.latitude
        lon = Geo_Coordinate.longitude

        API = (
            "https://api.openweathermap.org/data/2.5/onecall?lat={}&lon={}&exclude=current,minutely,hourly,alerts&units=metric&appid=".format(
                lat, lon
            )
            + key
        )
        response = requests.get(API)
        dataMap = response.json()
        # print(dataMap)

        st.write("Verschil luchtvochtigheid in %")
        dag0 = dataMap["daily"][0]["humidity"]
        dag1 = dataMap["daily"][1]["humidity"]
        dag2 = dataMap["daily"][2]["humidity"]
        dag3 = dataMap["daily"][3]["humidity"]
        dag4 = dataMap["daily"][4]["humidity"]
        dag5 = dataMap["daily"][5]["humidity"]
        dag6 = dataMap["daily"][6]["humidity"]
        dag7 = dataMap["daily"][7]["humidity"]
        voorspeldeVochtigheid = {dag0, dag1, dag2, dag3, dag4, dag5, dag6, dag7}
        st.write(voorspeldeVochtigheid)
        verschilVochtigheid = {
            dag1 - dag0,
            dag2 - dag1,
            dag3 - dag2,
            dag4 - dag3,
            dag5 - dag4,
            dag6 - dag5,
            dag7 - dag6,
        }
        st.bar_chart(verschilVochtigheid)

        st.write("luchtdruk in hPa")
        dag0 = dataMap["daily"][0]["pressure"]
        dag1 = dataMap["daily"][1]["pressure"]
        dag2 = dataMap["daily"][2]["pressure"]
        dag3 = dataMap["daily"][3]["pressure"]
        dag4 = dataMap["daily"][4]["pressure"]
        dag5 = dataMap["daily"][5]["pressure"]
        dag6 = dataMap["daily"][6]["pressure"]
        dag7 = dataMap["daily"][7]["pressure"]
        voorspeldeDruk = {dag0, dag1, dag2, dag3, dag4, dag5, dag6, dag7}
        st.write(voorspeldeDruk)
        st.bar_chart(voorspeldeDruk)

    elif choice == "Verbanden":
        st.write("""  # Wind analyse tool""")
        st.write(
            """  Temp = °C , Knots = 1.85 km/h, Dewpoint = °C , Humidity = %, Direction = °(windstreek)   """
        )

        citynames = ["Marseille", "Scheveningen"]

        st.sidebar.header("User Input Parameters")
        today = datetime.date(2020, 7, 23)
        tommorow = datetime.date(2020, 8, 8)
        dateMin = datetime.date(2001, 1, 1)
        dateMax = datetime.date(2021, 5, 1)
        location = st.sidebar.selectbox("locaties", citynames)
        startDate = st.sidebar.date_input("Begin datum", today, dateMin, dateMax)
        endDate = st.sidebar.date_input("Eind datum", tommorow, dateMin, dateMax)
        startTime = st.sidebar.slider("Begin tijd", 0, 23, 12)
        endTime = st.sidebar.slider("Eind tijd", 0, 23, 15)

        data = {
            "Locatie": location,
            "Begin datum": startDate,
            "Eind datum": endDate,
            "Begin tijd": startTime,
            "Eind tijd": endTime,
        }
        features = pd.DataFrame(data, index=[0])

        # unix_time = 1615287481 # Parameter is time
        unix_time = calendar.timegm(
            time.strptime(str(startDate) + " 00:00:00", "%Y-%m-%d %H:%M:%S")
        )

        # Correct date and time from the user given input:
        unix_time_start_time = calendar.timegm(
            time.strptime(
                str(startDate) + " " + str((startTime - 2)) + ":00", "%Y-%m-%d %H:%M"
            )
        )

        unix_time_end_time = calendar.timegm(
            time.strptime(
                str(endDate) + " " + str((endTime - 2)) + ":00", "%Y-%m-%d %H:%M"
            )
        )

        # I use only hour and minute because that's the way the data is stored in the database.
        start_dt = datetime.datetime.fromtimestamp(unix_time_start_time).strftime(
            "%Y-%m-%d %H:%M"
        )

        end_dt = datetime.datetime.fromtimestamp(unix_time_end_time).strftime(
            "%Y-%m-%d %H:%M"
        )

        # Test query:
        cuDatabase = connection.cursor()

        query = (
            "SELECT valid,tmpc,dwpc,relh,drct,sknt FROM data"
            + location
            + " WHERE valid >="
            + '"'
            + str(start_dt)
            + '"'
            + " AND valid < "
            + '"'
            + str(end_dt)
            + '"'
        )

        cuDatabase.execute(
            query,
        )

        rows = cuDatabase.fetchall()

        df_wind_information = pd.DataFrame(
            rows,
            columns=[
                "dateTime",
                "temp",
                "dewpc",
                "hum",
                "drct",
                "knots",
            ],
        )

        df_wind_information = df_wind_information[
            ["dateTime", "temp", "dewpc", "hum", "drct", "knots"]
        ].fillna(
            value=df_wind_information[
                ["dateTime", "temp", "dewpc", "hum", "drct", "knots"]
            ].mean()
        )

        connection.commit()
        cuDatabase.close()

        # Belangrijk wisselen van datatype!
        df_wind_information["dateTime"] = pd.to_datetime(df_wind_information.dateTime)

        df_wind_information.set_index("dateTime", inplace=True, drop=True)
        dfstrtime = datetime.time(startTime)
        dfendtime = datetime.time(endTime)

        df_wind_information = df_wind_information.between_time(dfstrtime, dfendtime)

        if st.sidebar.checkbox("Show Data"):
            st.write(df_wind_information)

        dfCollums = df_wind_information.columns
        colum1 = st.sidebar.selectbox("X-as", dfCollums)
        colum2 = st.sidebar.selectbox("Y-as", dfCollums, 4)
        typeplot = ["line", "scatter"]
        select = st.sidebar.selectbox("Typeplot", typeplot)

        import seaborn as sns
        keuzeGrafiek = sns.relplot(
            data=df_wind_information, kind=select, x=colum1, y=colum2
        )
        st.pyplot(keuzeGrafiek)

        st.line_chart(df_wind_information[["temp", "knots"]], use_container_width=True)

        st.line_chart(df_wind_information[["temp", "dewpc"]], use_container_width=True)

        st.line_chart(
            df_wind_information[["temp", "knots", "dewpc"]], use_container_width=True
        )

        st.line_chart(df_wind_information[["dewpc", "hum"]], use_container_width=True)

        st.line_chart(df_wind_information[["knots", "drct"]], use_container_width=True)

    elif choice == "Onderlinge verbanden":
        st.write("""  # Wind analyse tool""")
        st.write(
            """  Temp = °C , Knots = 1.85 km/h, Dewpoint = °C , Humidity = %, Direction = °(windstreek)   """
        )

        citynames = ["Marseille", "Scheveningen"]

        st.sidebar.header("User Input Parameters")
        today = datetime.date(2020, 7, 23)
        tommorow = datetime.date(2020, 8, 8)
        dateMin = datetime.date(2001, 1, 1)
        dateMax = datetime.date(2021, 5, 1)
        location = st.sidebar.selectbox("locaties", citynames)
        startDate = st.sidebar.date_input("Begin datum", today, dateMin, dateMax)
        endDate = st.sidebar.date_input("Eind datum", tommorow, dateMin, dateMax)
        startTime = st.sidebar.slider("Begin tijd", 0, 23, 12)
        endTime = st.sidebar.slider("Eind tijd", 0, 23, 15)

        data = {
            "Locatie": location,
            "Begin datum": startDate,
            "Eind datum": endDate,
            "Begin tijd": startTime,
            "Eind tijd": endTime,
        }
        features = pd.DataFrame(data, index=[0])

        # unix_time = 1615287481 # Parameter is time
        unix_time = calendar.timegm(
            time.strptime(str(startDate) + " 00:00:00", "%Y-%m-%d %H:%M:%S")
        )

        # Correct date and time from the user given input:
        unix_time_start_time = calendar.timegm(
            time.strptime(
                str(startDate) + " " + str((startTime - 2)) + ":00", "%Y-%m-%d %H:%M"
            )
        )

        unix_time_end_time = calendar.timegm(
            time.strptime(
                str(endDate) + " " + str((endTime - 2)) + ":00", "%Y-%m-%d %H:%M"
            )
        )

        # I use only hour and minute because that's the way the data is stored in the database.
        start_dt = datetime.datetime.fromtimestamp(unix_time_start_time).strftime(
            "%Y-%m-%d %H:%M"
        )

        end_dt = datetime.datetime.fromtimestamp(unix_time_end_time).strftime(
            "%Y-%m-%d %H:%M"
        )

        # Test query:
        cuDatabase = connection.cursor()

        query = (
            "SELECT valid,tmpc,dwpc,relh,drct,sknt FROM data"
            + location
            + " WHERE valid >="
            + '"'
            + str(start_dt)
            + '"'
            + " AND valid < "
            + '"'
            + str(end_dt)
            + '"'
        )

        cuDatabase.execute(
            query,
        )

        rows = cuDatabase.fetchall()

        df_wind_information = pd.DataFrame(
            rows,
            columns=[
                "dateTime",
                "temp",
                "dewpc",
                "hum",
                "drct",
                "knots",
            ],
        )

        df_wind_information = df_wind_information[
            ["dateTime", "temp", "dewpc", "hum", "drct", "knots"]
        ].fillna(
            value=df_wind_information[
                ["dateTime", "temp", "dewpc", "hum", "drct", "knots"]
            ].mean()
        )

        connection.commit()
        cuDatabase.close()

        # Belangrijk wisselen van datatype!
        df_wind_information["dateTime"] = pd.to_datetime(df_wind_information.dateTime)

        df_wind_information.set_index("dateTime", inplace=True, drop=True)
        dfstrtime = datetime.time(startTime)
        dfendtime = datetime.time(endTime)

        df_wind_information = df_wind_information.between_time(dfstrtime, dfendtime)

        if st.checkbox("Show Data"):
            st.write(df_wind_information)

        import seaborn as sns

        pairPlot = sns.pairplot(data=df_wind_information, kind="reg")
        st.pyplot(pairPlot)

if __name__ == "__main__":
    main()
