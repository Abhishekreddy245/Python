import pandas as pd
import sys

# ---------- Standings Logic ----------
def compute_standings(matches_df, teams_list):
    """
    Compute round-robin standings.
    Returns DataFrame with columns: team, Pld, W, L, PF, PA, PD, Pts sorted by Pts, PD.
    """
    # Initialize
    data = {team: {'Pld': 0, 'W': 0, 'L': 0, 'PF': 0, 'PA': 0, 'Pts': 0} for team in teams_list}
    # Tally
    for _, m in matches_df.iterrows():
        a, b = m['team_a'], m['team_b']
        sa, sb = m['score_a'], m['score_b']
        data[a]['Pld'] += 1; data[b]['Pld'] += 1
        data[a]['PF'] += sa; data[a]['PA'] += sb
        data[b]['PF'] += sb; data[b]['PA'] += sa
        if sa > sb:
            data[a]['W'] += 1; data[b]['L'] += 1; data[a]['Pts'] += 2
        else:
            data[b]['W'] += 1; data[a]['L'] += 1; data[b]['Pts'] += 2
    # Build DataFrame
    df = pd.DataFrame.from_dict(data, orient='index')
    df['PD'] = df['PF'] - df['PA']
    df = df.sort_values(['Pts', 'PD'], ascending=False).reset_index()
    df = df.rename(columns={'index': 'team'})
    return df

# ---------- App / Tests ----------
# Attempt to import Streamlit for the UI; if unavailable, skip UI and enable tests
try:
    import streamlit as st
except ImportError:
    st = None

if st:
    # ---------- Streamlit UI Code ----------
    import pandas as pd

    def init_session_state():
        if 'teams' not in st.session_state:
            st.session_state.teams = pd.DataFrame(columns=['team','player1','player2','player3'])
        if 'matches' not in st.session_state:
            st.session_state.matches = pd.DataFrame(columns=[
                'round','pool','team_a','team_b','player_a','player_b','score_a','score_b'
            ])

    st.title("🏓 Pickleball Tournament Manager")
    init_session_state()
    role = st.sidebar.selectbox("Select role", ['Organizer','Player'])

    if role == 'Organizer':
        st.header("Team & Player Management")
        uploaded = st.file_uploader("Upload teams CSV", type=['csv'])
        if uploaded:
            df = pd.read_csv(uploaded)
            if {'team','player1','player2','player3'}.issubset(df.columns):
                st.session_state.teams = df
                st.success("Teams updated")
            else:
                st.error("CSV must have columns: team, player1, player2, player3")
        with st.expander("Add team manually"):
            t = st.text_input("Team name", key='new_team')
            p1 = st.text_input("Player 1", key='new_p1')
            p2 = st.text_input("Player 2", key='new_p2')
            p3 = st.text_input("Player 3", key='new_p3')
            if st.button("Add Team"):
                row = {'team':t,'player1':p1,'player2':p2,'player3':p3}
                st.session_state.teams = pd.concat([st.session_state.teams,pd.DataFrame([row])],ignore_index=True)
                st.success(f"Added {t}")
        st.subheader("Enter Match Result")
        if st.session_state.teams.empty:
            st.warning("Define teams first.")
        else:
            c1,c2 = st.columns(2)
            with c1:
                pool = st.selectbox("Pool",['A','B'],key='mp')
                rnd = st.number_input("Round",min_value=1,step=1,key='r')
                ta = st.selectbox("Team A",st.session_state.teams['team'],key='ta')
                pa = st.selectbox("Player A",st.session_state.teams.query("team==@ta")[['player1','player2','player3']].values.flatten(),key='pa')
                sa = st.number_input("Score A",min_value=0,step=1,key='sa')
            with c2:
                tb = st.selectbox("Team B",[t for t in st.session_state.teams['team'] if t!=ta],key='tb')
                pb = st.selectbox("Player B",st.session_state.teams.query("team==@tb")[['player1','player2','player3']].values.flatten(),key='pb')
                sb = st.number_input("Score B",min_value=0,step=1,key='sb')
            if st.button("Submit"):
                m = {'round':rnd,'pool':pool,'team_a':ta,'team_b':tb,'player_a':pa,'player_b':pb,'score_a':sa,'score_b':sb}
                st.session_state.matches = pd.concat([st.session_state.matches,pd.DataFrame([m])],ignore_index=True)
                st.success("Recorded!")
        st.subheader("Matches")
        st.dataframe(st.session_state.matches)
        if not st.session_state.matches.empty:
            st.subheader("Standings: Pool A")
            pa = st.session_state.matches.query("pool=='A'")
            teamsA = [t for t in st.session_state.teams['team'] if t.startswith('Team A')]
            st.dataframe(compute_standings(pa,teamsA))
            st.subheader("Standings: Pool B")
            pb = st.session_state.matches.query("pool=='B'")
            teamsB = [t for t in st.session_state.teams['team'] if t.startswith('Team B')]
            st.dataframe(compute_standings(pb,teamsB))

else:
    # ---------- CLI Test Runner ----------
    def _test_compute_standings_basic():
        test = pd.DataFrame([
            {'team_a':'X','team_b':'Y','score_a':11,'score_b':5},
            {'team_a':'Y','team_b':'Z','score_a':7,'score_b':11},
            {'team_a':'Z','team_b':'X','score_a':3,'score_b':11},
        ])
        df = compute_standings(test,['X','Y','Z'])
        assert df.loc[df.team=='X','Pts'].iloc[0]==4
        assert df.loc[df.team=='Y','Pts'].iloc[0]==0
        assert df.loc[df.team=='Z','Pts'].iloc[0]==2
    def _test_compute_standings_tiebreak():
        test = pd.DataFrame([
            {'team_a':'A','team_b':'B','score_a':11,'score_b':5},
            {'team_a':'B','team_b':'C','score_a':11,'score_b':3},
            {'team_a':'C','team_b':'A','score_a':11,'score_b':9},
        ])
        df = compute_standings(test,['A','B','C'])
        # All 1-1, order by PD: A(20-14=6), B(16-14=2), C(14-20=-6)
        expected = ['A','B','C']
        assert df['team'].tolist()==expected, f"Expected order {expected}, got {df['team'].tolist()}"
    if __name__=='__main__':
        _test_compute_standings_basic()
        _test_compute_standings_tiebreak()
        print("All compute_standings tests passed.")
