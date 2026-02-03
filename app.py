import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

st.set_page_config(page_title="Steel Selection Framework", layout="wide")

st.title("Interactive Steel Selection Tool")
st.markdown("Steel selection based on Yield Strength, UTS, Safety and Ashby indices")

@st.cache_data
def load_data():
    df = pd.read_excel("Final_Steel_Selection_Results.xlsx")
    df['Density'] = 7850
    return df

df = load_data()

# --------------------------------------------------
# 🔹 DATA-BASED LIMITS
# --------------------------------------------------
min_yield = df['Yield_Strength'].min()
max_yield = df['Yield_Strength'].max()

min_uts = df['UTS'].min()
max_uts = df['UTS'].max()

# --------------------------------------------------
# 🔹 SIDEBAR INPUTS
# --------------------------------------------------
st.sidebar.header("Design Requirements")

# Factor of Safety
fos = st.sidebar.slider(
    "Factor of Safety",
    min_value=1.2,
    max_value=3.0,
    value=1.7,
    step=0.1
)

# Required Yield Strength
required_yield = st.sidebar.slider(
    "Required Yield Strength (MPa)",
    min_value=float(min_yield),
    max_value=float(max_yield),
    value=float(min_yield)
)

# Required UTS (NEW FEATURE)
required_uts = st.sidebar.slider(
    "Minimum UTS Requirement (MPa)",
    min_value=float(min_uts),
    max_value=float(max_uts),
    value=float(min_uts)
)

# Allowable stress derived from yield strength
allowable_stress = required_yield / fos

# --------------------------------------------------
# 🔹 SHOW DATA-BASED LIMITS
# --------------------------------------------------
st.sidebar.markdown("### 📊 Data-Based Limits")
st.sidebar.info(
    f"""
    **Yield Strength Range:**  
    {min_yield:.1f} – {max_yield:.1f} MPa

    **UTS Range:**  
    {min_uts:.1f} – {max_uts:.1f} MPa

    **Allowable Stress Range (FoS = {fos}):**  
    {(min_yield/fos):.1f} – {(max_yield/fos):.1f} MPa
    """
)

# --------------------------------------------------
# 🔹 RULE-BASED FILTERING
# --------------------------------------------------
df['Strength_OK'] = df['Yield_Strength'] >= required_yield
df['UTS_OK'] = df['UTS'] >= required_uts
df['Safety_OK'] = df['Yield_Strength'] >= allowable_stress

df['Selected'] = df['Strength_OK'] & df['UTS_OK'] & df['Safety_OK']
selected_df = df[df['Selected']]

# --------------------------------------------------
# 🔹 ADVANCED INDICES (NEW)
# --------------------------------------------------
selected_df['Ashby_Strength_Density'] = selected_df['Yield_Strength'] / selected_df['Density']
selected_df['Safety_Index'] = selected_df['Yield_Strength'] / allowable_stress

# Yield-to-UTS ratio (ductility indicator)
selected_df['Yield_to_UTS_Ratio'] = selected_df['Yield_Strength'] / selected_df['UTS']

# --------------------------------------------------
# 🔹 OUTPUT TABLE
# --------------------------------------------------
st.subheader("✅ Suitable Steel Conditions")

st.dataframe(
    selected_df.sort_values(
        by=['Ashby_Strength_Density', 'Yield_to_UTS_Ratio'],
        ascending=[False, True]
    )
)

# --------------------------------------------------
# 🔹 ASHBY PLOT
# --------------------------------------------------
st.subheader("📈 Ashby Selection Map")

fig, ax = plt.subplots()
ax.scatter(
    selected_df['Ashby_Strength_Density'],
    selected_df['Yield_to_UTS_Ratio']
)

ax.set_xlabel("Strength / Density")
ax.set_ylabel("Yield / UTS Ratio (Ductility Indicator)")
ax.grid(True)

st.pyplot(fig)
