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
    df["Density"] = 7850  # kg/m3 for steel
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
st.sidebar.header("🔧 Design Requirements")

fos = st.sidebar.slider(
    "Factor of Safety",
    min_value=1.2,
    max_value=3.0,
    value=1.7,
    step=0.1
)

required_yield = st.sidebar.slider(
    "Required Yield Strength (MPa)",
    min_value=float(min_yield),
    max_value=float(max_yield),
    value=float(min_yield)
)

required_uts = st.sidebar.slider(
    "Minimum UTS Requirement (MPa)",
    min_value=float(min_uts),
    max_value=float(max_uts),
    value=float(min_uts)
)

# Allowable stress derived from yield strength
allowable_stress = required_yield / fos

# --------------------------------------------------
# SHOW DATA CONSTRAINTS (FOR NEW USERS)
# --------------------------------------------------
st.sidebar.markdown("### 📊 Data-Based Limits")
st.sidebar.info(
    f"""
    **Yield Strength range:**  
    {min_yield:.1f} – {max_yield:.1f} MPa

    **UTS range:**  
    {min_uts:.1f} – {max_uts:.1f} MPa

    **Allowable stress range (FoS = {fos}):**  
    {(min_yield/fos):.1f} – {(max_yield/fos):.1f} MPa
    """
)

# --------------------------------------------------
# RULE-BASED FILTERING
# --------------------------------------------------
df["Strength_OK"] = df["Yield_Strength"] >= required_yield
df["UTS_OK"] = df["UTS"] >= required_uts
df["Safety_OK"] = df["Yield_Strength"] >= allowable_stress

df["Selected"] = df["Strength_OK"] & df["UTS_OK"] & df["Safety_OK"]
selected_df = df[df["Selected"]].reset_index(drop=True)

# --------------------------------------------------
# ASHBY & MECHANICAL INDICES
# --------------------------------------------------
selected_df["Ashby_Strength_Density"] = (
    selected_df["Yield_Strength"] / selected_df["Density"]
)

selected_df["Safety_Index"] = (
    selected_df["Yield_Strength"] / allowable_stress
)

# Yield / UTS ratio → ductility / failure margin indicator
selected_df["Yield_to_UTS_Ratio"] = (
    selected_df["Yield_Strength"] / selected_df["UTS"]
)

# --------------------------------------------------
# OUTPUT TABLE
# --------------------------------------------------
st.subheader("Suitable Steel Conditions")

st.dataframe(
    selected_df.sort_values(
        by=["Ashby_Strength_Density", "Yield_to_UTS_Ratio"],
        ascending=[False, True]
    ),
    use_container_width=True
)

# --------------------------------------------------
# INTERACTIVE ASHBY PLOT (PLOTLY)
# --------------------------------------------------
st.subheader("Ashby Selection Map (Click a point)")

fig = px.scatter(
    selected_df,
    x="Ashby_Strength_Density",
    y="Yield_to_UTS_Ratio",
    hover_data=[
        "Yield_Strength",
        "UTS",
        "Safety_Index"
    ],
    labels={
        "Ashby_Strength_Density": "Strength / Density",
        "Yield_to_UTS_Ratio": "Yield / UTS Ratio"
    },
    title="Ashby Selection Map"
)

# Capture click events
selected_points = plotly_events(
    fig,
    click_event=True,
    hover_event=False,
    select_event=False,
    override_height=500
)

st.plotly_chart(fig, use_container_width=True)

# --------------------------------------------------
# HIGHLIGHT CLICKED POINT IN TABLE
# --------------------------------------------------
if selected_points:
    idx = selected_points[0]["pointIndex"]
    highlighted_row = selected_df.iloc[[idx]]

    st.subheader("Selected Steel (from Ashby plot)")
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
    "Selection is constrained by available experimental data and "
    "allowable stress is derived from yield strength using a factor of safety."
)
