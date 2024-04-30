'''A script that creates the home page for the dashboard.'''

from os import environ as ENV
from datetime import datetime, timedelta

import pandas as pd
import altair as alt
import streamlit as st
from dotenv import load_dotenv

from psycopg2 import connect
from psycopg2.extras import RealDictCursor
from psycopg2.extensions import connection


def get_db_connection(config) -> connection:
    """Returns a connection to the database."""

    return connect(
        dbname=config["DB_NAME"],
        user=config["DB_USER"],
        password=config["DB_PASSWORD"],
        host=config["DB_HOST"],
        port=config["DB_PORT"],
        cursor_factory=RealDictCursor
    )


def get_week_list() -> tuple:
    """Returns a tuple containing the dates 
    of the last seven days (not including today)."""
    w_list = []

    for each in range(1, 8):
        day = datetime.now() - timedelta(days=each)
        w_list.append(day.strftime('%Y-%m-%d'))

    return tuple(w_list)


def filter_tags(data_df: pd.DataFrame, tags_: list, col: str) -> pd.DataFrame:
    """Returns a Data-frame that only has the relevant tags."""

    data_df = data_df[data_df[col].isin(tags_)]

    return data_df


def filter_dates(data_df: pd.DataFrame, dates: list, col: str) -> pd.DataFrame:
    """Returns a Data-frame that only has data from the last 7 days."""

    data_df[col] = data_df[col].astype(str)
    data_df = data_df[data_df[col].isin(dates)]

    return data_df


def metric_games_yest(conn_: connection) -> pd.DataFrame:
    """Returns a Data-frame of all the games from the yesterday."""

    yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')

    with conn_.cursor() as cur:
        cur.execute(f""" SELECT name, rating, price, release_date
                    FROM game
                    WHERE release_date = '{yesterday}';""")
        steam_games = cur.fetchall()

    return pd.DataFrame(steam_games)


def metrics_for_graphs_price(conn_: connection) -> pd.DataFrame:
    """Returns a Data-frame of all the average prices for the last week."""
    this_week_list = get_week_list()

    with conn_.cursor() as cur:
        cur.execute(f""" SELECT AVG(price), release_date
                    FROM game
                    WHERE release_date in {this_week_list}
                    GROUP BY release_date;""")
        steam_games = cur.fetchall()

    return pd.DataFrame(steam_games)


def metrics_for_graphs_count(conn_: connection) -> pd.DataFrame:
    """Returns a Data-frame of all the number of games for the last week."""
    this_week_list = get_week_list()

    with conn_.cursor() as cur:
        cur.execute(f""" SELECT COUNT(name), release_date
                    FROM game
                    WHERE release_date in {this_week_list}
                    GROUP BY release_date;""")
        steam_games = cur.fetchall()

    return pd.DataFrame(steam_games)


def metrics_for_graphs_rating(conn_: connection) -> pd.DataFrame:
    """Returns a Data-frame of all the game ratings for the past week."""
    this_week_list = get_week_list()

    with conn_.cursor() as cur:
        cur.execute(f""" SELECT AVG(rating), release_date
                    FROM game
                    WHERE release_date in {this_week_list}
                    GROUP BY release_date;""")
        steam_games = cur.fetchall()

    return pd.DataFrame(steam_games)


def metrics_for_graphs_tags(conn_: connection) -> pd.DataFrame:
    """Returns a Data-frame of all the games tag data from the past week."""
    this_week_list = get_week_list()

    with conn_.cursor() as cur:
        cur.execute(f"""SELECT t.tag_name, count(*) from tag AS t 
                    INNER JOIN game_tag_matching AS gt 
                    ON t.tag_id = gt.tag_id 
                    WHERE gt.game_id IN
                    (SELECT game_id from game 
                    WHERE release_date IN {this_week_list}) 
                    GROUP BY t.tag_name 
                    LIMIT 10;""")
        tags_ = cur.fetchall()

    return pd.DataFrame(tags_)


def metrics_top_twenty(conn_: connection) -> pd.DataFrame:
    """Returns a Data-frame of top rated the games from the last week. """
    this_week_list = get_week_list()

    with conn_.cursor() as cur:
        cur.execute(f"""SELECT g.name, g.rating, g.price, d.developer_name, p.publisher_name
                    FROM game as g
                    JOIN developer as d
                    ON g.developer_id = d.developer_id
                    JOIN publisher as p
                    on g.publisher_id = p.publisher_id
                    WHERE g.release_date in {this_week_list}
                    ORDER BY rating DESC LIMIT 20;""")
        tags_ = cur.fetchall()

    return pd.DataFrame(tags_)


def price_chart(data_df: pd.DataFrame, sorting=True) -> alt.Chart:
    """"Generates a bar chart of average daily prices of games over their release dates."""

    data_df['release_date'] = data_df['release_date'].astype(str)
    data_df['AVG price (£)'] = data_df['avg'].apply(lambda x: round(x, 2))
    sort = "-y" if sorting else "x"

    return alt.Chart(data_df).mark_bar().encode(
        x=alt.Y("AVG price (£)", title='Average Daily Game Price'),
        y=alt.X("release_date").sort(sort),
        color="release_date"
    )


def count_chart(data_df: pd.DataFrame, sorting=True) -> alt.Chart:
    """Generates a bar chart of daily number of games releases."""

    data_df['release_date'] = data_df['release_date'].astype(str)
    data_df['Daily Releases'] = data_df['count']
    sort = "-y" if sorting else "x"

    return alt.Chart(data_df).mark_line().encode(
        x=alt.X("release_date",  title='Number Of Daily Releases').sort(sort),
        y=alt.Y("Daily Releases")
    )


def rating_chart(data_df: pd.DataFrame, sorting=True) -> alt.Chart:
    """"Generates a bar chart of average daily ratings of games over their release dates."""

    data_df['release_date'] = data_df['release_date'].astype(str)
    data_df['Average Rating(%)'] = data_df['avg']
    sort = "-y" if sorting else "x"

    return alt.Chart(data_df).mark_bar().encode(
        x=alt.Y("Average Rating(%)", title='Average Daily Game Rating'),
        y=alt.X("release_date").sort(sort),
        color="release_date"
    )


def make_tag_chart(data_df: pd.DataFrame, sorting=True) -> alt.Chart:
    """Generates a bar chart of most popular tags of games in the last week."""

    sort = "-y" if sorting else "x"

    return alt.Chart(data_df).mark_bar().encode(
        x=alt.X("tag_name").sort(sort),
        y="count",
        color="tag_name"
    )


if __name__ == "__main__":

    load_dotenv()
    conn = get_db_connection(ENV)
    week_list = list(get_week_list())

    metric_df = metric_games_yest(conn)
    top_twenty_games = metrics_top_twenty(conn)
    tag_df = metrics_for_graphs_tags(conn)
    tags = tag_df["tag_name"].to_list()

    no_games = metric_df['name'].nunique()
    avg_rating = metric_df['rating'].mean()
    avg_price = metric_df['price'].mean()

    price_df = metrics_for_graphs_price(conn)
    count_df = metrics_for_graphs_count(conn)
    rating_df = metrics_for_graphs_rating(conn)

    conn.close()

    st.set_page_config(page_title='GameScraper',
                       page_icon=":space_invader:", layout="wide")
    st.title("Welcome To GameScraper")
    st.write("---")
    st.subheader(
        "This weeks latest metrics & graphs from the hottest new games!")
    st.text(
        "Brought to you by the GameScraper Team")

    st.divider()
    if no_games == 0:
        st.write("No New Games Released Yesterday")

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Number of new releases yesterday:", no_games)
    with col2:
        st.metric("Average rating of new releases yesterday:",
                  f'{round(avg_rating,2)}%')
    with col3:
        st.metric("Average price of new releases yesterday:",
                  f'£{avg_price:.2f}'.format(avg_price))

    with st.sidebar:
        st.title("Navigation Station :rocket:")
        st.write("---")
        st.title("Filtering")

        creator_options = tags
        filtered_tags = st.multiselect("Available Genres",
                                       options=creator_options,
                                       default=creator_options)

        end_date = st.select_slider(
            'Select a range of dates',
            options=week_list
        )

    filtered_days = week_list[:week_list.index(end_date) + 1]
    new_price_df = filter_dates(price_df, filtered_days, "release_date")
    new_count_df = filter_dates(count_df, filtered_days, "release_date")
    new_rating_df = filter_dates(rating_df, filtered_days, "release_date")
    new_tag_df = filter_tags(tag_df, filtered_tags, "tag_name")
    top_twenty_games = top_twenty_games.drop('rating', axis=1)
    tag_chart = make_tag_chart(new_tag_df)
    p_chart = price_chart(new_price_df)
    c_chart = count_chart(new_count_df)
    r_chart = rating_chart(new_rating_df)

    st.subheader("This Weeks Most Popular Gaming Tags")
    st.altair_chart(tag_chart, use_container_width=True)
    st.subheader("Average Price Per Day",)
    st.altair_chart(p_chart, use_container_width=True)
    st.subheader("This Weeks Top Twenty Games")
    st.write(top_twenty_games)

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Average Rating Per Day")
        st.altair_chart(r_chart)
    with col2:
        st.subheader("Daily Releases")
        st.altair_chart(c_chart, use_container_width=True)
