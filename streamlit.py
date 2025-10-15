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

st.logo("sqone-logo.png", size="Large")
# st.write("Query Results", df)


import streamlit as st
import pandas as pd

# sets_df columns assumed: ["game_name", "player_name", "opponent_name", ...]
with st.container():
    p1col, p2col, gamecol = st.columns(3)

    # --- GAME can be chosen anytime (or left as All) ---
    with gamecol:
        game_options = sorted(sets_df["game_name"].dropna().unique().tolist())
        game_filter = st.selectbox("Game Filter", ["All"] + game_options, index=0)

    # Narrow the working frame by game (if picked)
    df_by_game = sets_df if game_filter == "All" else sets_df[sets_df["game_name"] == game_filter]

    # --- PLAYER 1 can also be chosen anytime ---
    with p1col:
        p1_options = sorted(df_by_game["player_name"].dropna().unique().tolist())
        player_filter = st.selectbox("Player 1 Filter", p1_options, index=None, placeholder="Pick Player 1")

    # --- PLAYER 2 only appears AFTER Player 1 is selected ---
    with p2col:
        if player_filter is not None and player_filter != "":
            df_by_p1 = df_by_game[df_by_game["player_name"] == player_filter]
            p2_options = sorted(df_by_p1["opponent_name"].dropna().unique().tolist())
            opponent_filter = st.selectbox("Opponent Filter", p2_options, index=None, placeholder="Pick Opponent")
        else:
            st.info("Select Player 1 to enable Opponent filter.")
            opponent_filter = None

    # --- Build final filtered dataframe ---
    filtered = sets_df.copy()
    if game_filter != "All":
        filtered = filtered[filtered["game_name"] == game_filter]
    if player_filter:
        filtered = filtered[filtered["player_name"] == player_filter]
    if opponent_filter:
        filtered = filtered[filtered["opponent_name"] == opponent_filter]

    st.dataframe(filtered, use_container_width=True)

    # Optional: Small empty-state hint
    if filtered.empty:
        st.caption("No matches with the current filters.")


# st.write("Standings Results", sets_filtered[["player_name", "opponent_name", "wins", "losses", "game_name"]])

pie_df = filtered.melt(value_vars=['wins', 'losses'], 
                 var_name='result', 
                 value_name='count')

pie_df_summed = pie_df.groupby(['result']).sum().reset_index()

chart = alt.Chart(pie_df_summed).mark_arc().encode(
    theta="count",
    color="result"
)

col1, col2 = st.columns(2)

with col1:
    st.write("Standings Results")
    st.dataframe(filtered[["opponent_name", "wins", "losses", "game_name"]], hide_index=True)
with col2:
    st.altair_chart(chart)