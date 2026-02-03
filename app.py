import streamlit as st
import pandas as pd
import plotly.express as px
from streamlit_plotly_events import plotly_events

# --------------------------------------------------
# PAGE CONFIG
# --------------------------------------------------
st.set_page_config(page_title="Steel Selection Framework", layout="wide")

st.title("🛠️ Interactive Steel Selection Tool")
st.markdown(
    "Steel selection based on **Yield Strength**, **UTS**, **Safety** and **Ashby material indices**"
)

# --------------------------------------------------
# LOAD DATA
# --------------------------------------------------
@st.cache_data
def load_data():
    df = pd.read_excel("Final_Steel_Selection_Results.xlsx")
    df["Density"] = 7850
    df["row_id"] = df.index.astype(int)  # ✅ stable ID
    return df

df = load_data()

# --------------------------------------------------
# DATA-BASED LIMITS
# --------------------------------------------------
min_yield = df["Yield_Strength"].min()
max_yield = df["Yield_Strength"].max()

min_uts = df["UTS"].min()
max_uts = df["UTS"].max()

# --------------------------------------------------
# SIDEBAR INPUTS
# --------------------------------------------------
st.sidebar.header("Design Requirements")

fos = st.sidebar.slider("Factor of Safety", 1.2, 3.0, 1.7, 0.1)

required_yield = st.sidebar.slider(
    "Required Yield Strength (MPa)",
    float(min_yield),
    float(max_yield),
    float(min_yield)
)

required_uts = st.sidebar.slider(
    "Minimum UTS Requirement (MPa)",
    float(min_uts),
    float(max_uts),
    float(min_uts)
)

allowable_stress = required_yield / fos

# --------------------------------------------------
# DATA CONSTRAINT DISPLAY
# --------------------------------------------------
st.sidebar.markdown("### Data-Based Limits")
st.sidebar.info(
    f"""
    **Yield Strength:** {min_yield:.1f} – {max_yield:.1f} MPa  
    **UTS:** {min_uts:.1f} – {max_uts:.1f} MPa  
    **Allowable Stress (FoS={fos}):** {(min_yield/fos):.1f} – {(max_yield/fos):.1f} MPa
    """
)

# --------------------------------------------------
# RULE-BASED FILTERING
# --------------------------------------------------
df["Strength_OK"] = df["Yield_Strength"] >= required_yield
df["UTS_OK"] = df["UTS"] >= required_uts
df["Safety_OK"] = df["Yield_Strength"] >= allowable_stress

df["Selected"] = df["Strength_OK"] & df["UTS_OK"] & df["Safety_OK"]

# --------------------------------------------------
# ASHBY & MECHANICAL INDICES (ALL DATA)
# --------------------------------------------------
df["Ashby_Strength_Density"] = df["Yield_Strength"] / df["Density"]
df["Yield_to_UTS_Ratio"] = df["Yield_Strength"] / df["UTS"]
df["Safety_Index"] = df["Yield_Strength"] / allowable_stress

# --------------------------------------------------
# FILTERED TABLE
# --------------------------------------------------
st.subheader("Suitable Steel Conditions")

selected_df = df[df["Selected"]]

if selected_df.empty:
    st.warning(
        "No steel satisfies the current requirements. "
        "Relax Yield Strength, UTS, or Factor of Safety."
    )
else:
    st.dataframe(
        selected_df.sort_values(
            by=["Ashby_Strength_Density", "Yield_to_UTS_Ratio"],
            ascending=[False, True]
        ),
        use_container_width=True
    )

# --------------------------------------------------
# INTERACTIVE ASHBY MAP (ALL DATA)
# --------------------------------------------------
st.subheader("Ashby Selection Map (Green = Meets Criteria)")

fig = px.scatter(
    df,
    x="Ashby_Strength_Density",
    y="Yield_to_UTS_Ratio",
    color="Selected",
    color_discrete_map={True: "lime", False: "red"},
    custom_data=["row_id"],   # ✅ critical
    hover_data=["Yield_Strength", "UTS", "Safety_Index"],
    labels={
        "Ashby_Strength_Density": "Strength / Density",
        "Yield_to_UTS_Ratio": "Yield / UTS Ratio"
    },
    title="Ashby Selection Map"
)

selected_points = plotly_events(
    fig,
    click_event=True,
    hover_event=False,
    select_event=False,
    override_height=500
)

# --------------------------------------------------
# CLICK → TABLE HIGHLIGHT (ROBUST)
# --------------------------------------------------
if selected_points:
    clicked_row_id = selected_points[0]["customdata"][0]
    highlighted_row = df[df["row_id"] == clicked_row_id]

    st.subheader("🔍 Selected Steel (from Ashby plot)")
    st.dataframe(
        highlighted_row.style.apply(
            lambda x: ["background-color: #fff3b0"] * len(x),
            axis=1
        ),
        use_container_width=True
    )

# --------------------------------------------------
# USER GUIDANCE
# --------------------------------------------------
st.caption(
    "Selection is constrained by available experimental data. "
    "Allowable stress is derived from yield strength using a factor of safety."
)
