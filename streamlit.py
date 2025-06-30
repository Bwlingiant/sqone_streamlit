import streamlit as st
import psycopg
# import os
import pandas as pd
import altair as alt

@st.cache_resource
def get_connection():
    return psycopg.connect(
    host=st.secrets["postgres"]["host"],
    dbname=st.secrets["postgres"]["dbname"],
    user=st.secrets["postgres"]["user"],
    password=st.secrets["postgres"]["password"],
    port=st.secrets["postgres"]["port"]
)

conn = get_connection()

# query = '''SELECT * FROM "fgc".startgg_sets LIMIT 5;'''
# df = pd.read_sql_query(query, conn)
# Run query
# with conn.cursor() as cur:
#     cur.execute('''SELECT * FROM "fgc".startgg_sets LIMIT 5;''')
#     rows = cur.fetchall()

standing_query = '''SELECT * FROM "fgc".startgg_tournament_standings;'''
sets_query = '''WITH matchups AS (
  SELECT
    game_id,
    set_id,
    player1_id AS player_id,
    player2_id AS opponent_id,
    CASE WHEN entrant1_id = winner_id THEN 1 ELSE 0 END AS win,
    CASE WHEN entrant2_id = winner_id THEN 1 ELSE 0 END AS loss
  FROM fgc.startgg_sets

  UNION ALL

  SELECT
    game_id,
    set_id,
    player2_id AS player_id,
    player1_id AS opponent_id,
    CASE WHEN entrant2_id = winner_id THEN 1 ELSE 0 END AS win,
    CASE WHEN entrant1_id = winner_id THEN 1 ELSE 0 END AS loss
  FROM fgc.startgg_sets
)

SELECT
  m1.game_id,
  game1.game_name,
  m1.player_id,
pl1.player_name,
  opponent_id,
opp1.player_name opponent_name,
  SUM(win) AS wins,
  SUM(loss) AS losses
FROM matchups m1
LEFT JOIN "fgc".startgg_players pl1
ON m1.player_id = pl1.player_id
LEFT JOIN "fgc".startgg_players opp1
on m1.opponent_id = opp1.player_id
LEFT JOIN "fgc".game_lov game1
ON m1.game_id = game1.game_id
GROUP BY m1.game_id, game1.game_name, m1.player_id, opponent_id, pl1.player_name, opp1.player_name
ORDER BY m1.game_id, m1.player_id, opponent_id
;
'''
sets_df = pd.read_sql_query(sets_query, conn)

col1, col2 = st.columns(2)


st.logo("sqone-logo.png", size="Large")
# st.write("Query Results", df)
with col1:
    
  player_filter = st.selectbox("Player 1 Filter", sets_df['player_name'].unique(), index=None)
  players_filtered = sets_df.loc[sets_df["player_name"]==player_filter]


  opponent_filter = st.selectbox("Opponent Filter", players_filtered['opponent_name'].unique(), index=None)

  if opponent_filter is None:
      opponents_filtered = players_filtered
  else:
      opponents_filtered = players_filtered.loc[players_filtered["opponent_name"]==opponent_filter]

  game_filter = st.selectbox("Game Filter", opponents_filtered["game_name"].unique(), index=None)

  if game_filter is None:
      sets_filtered = opponents_filtered
  else:
      sets_filtered = opponents_filtered.loc[opponents_filtered["game_name"]==game_filter]

# st.write("Standings Results", sets_filtered[["player_name", "opponent_name", "wins", "losses", "game_name"]])

pie_df = sets_filtered.melt(value_vars=['wins', 'losses'], 
                 var_name='result', 
                 value_name='count')

chart = alt.Chart(pie_df).mark_arc().encode(
    theta="count",
    color="result"
)

 
with col2:
    st.write("Standings Results", sets_filtered[["player_name", "opponent_name", "wins", "losses", "game_name"]])
    st.altair_chart(chart)