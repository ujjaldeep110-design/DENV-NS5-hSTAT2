import streamlit as st
import pandas as pd
import plotly.express as px
import os

# --- 1. PAGE CONFIGURATION ---
st.set_page_config(page_title="Phytochemical ADMET Dashboard", layout="wide")
st.title("🧪 Dengue NS5 & hSTAT2: Phytochemical Screening Dashboard")
st.markdown("Interactive filtering of molecular docking and ADMETlab3 toxicity profiles.")

# --- 2. LOAD & CLEAN DATA ---
@st.cache_data
def load_data():
    file_path = "Comprehensive_ADMET_Ranked_871.csv" 
    
    if os.path.exists(file_path):
        df = pd.read_csv(file_path)
        # Clean wrapped Excel column headers to prevent KeyError
        df.columns = df.columns.str.replace(r'\n', ' ', regex=True).str.strip()
        df.columns = df.columns.str.replace(r'\s+', ' ', regex=True)
        return df
    else:
        st.error(f"File not found at: {file_path}. Ensure the CSV is uploaded to your GitHub repository.")
        return pd.DataFrame()

df = load_data()

if not df.empty:
    name_col = 'Ligand Name' if 'Ligand Name' in df.columns else 'Ligand_Name'
    
    # --- 3. SIDEBAR FILTERS ---
    st.sidebar.header("⚙️ Filter Criteria")
    
    # Compound Search
    search_query = st.sidebar.text_input("🔍 Search Compound Name", "")
    
    # Binding Affinity Filters
    max_vina_ns5 = st.sidebar.slider("Max Vina Score (NS5)", min_value=-15.0, max_value=0.0, value=-8.0, step=0.5)
    max_vina_hstat2 = st.sidebar.slider("Max Vina Score (hSTAT2)", min_value=-15.0, max_value=0.0, value=-8.0, step=0.5)
    
    # Drug-likeness Filter
    min_qed = st.sidebar.slider("Min QED Score", min_value=0.0, max_value=1.0, value=0.4, step=0.05)
    
    # Toxicity Dealbreakers
    st.sidebar.markdown("### Organ Toxicity Limits")
    max_dili = st.sidebar.slider("Max DILI (Liver Tox)", min_value=0.0, max_value=1.0, value=0.5, step=0.05)
    max_herg = st.sidebar.slider("Max hERG (Heart Tox)", min_value=0.0, max_value=1.0, value=0.5, step=0.05)
    max_ototox = st.sidebar.slider("Max Ototoxicity (Ear)", min_value=0.0, max_value=1.0, value=0.8, step=0.05)
    max_neurotox = st.sidebar.slider("Max Neurotoxicity (Brain)", min_value=0.0, max_value=1.0, value=0.5, step=0.05)
    max_nephrotox = st.sidebar.slider("Max Nephrotoxicity (Kidney)", min_value=0.0, max_value=1.0, value=0.5, step=0.05)
    max_hematotox = st.sidebar.slider("Max Hematotoxicity (Blood)", min_value=0.0, max_value=1.0, value=0.5, step=0.05)
    
    # NEW: Respiratory Toxicity Filter
    max_resp = st.sidebar.slider("Max Respiratory Toxicity", min_value=0.0, max_value=1.0, value=0.5, step=0.05)
    
    # Cancer Risk & DNA Damage
    st.sidebar.markdown("### Systemic Risks")
    max_carc = st.sidebar.slider("Max Carcinogenicity", min_value=0.0, max_value=1.0, value=0.6, step=0.05)
    
    # NEW: Genotoxicity Filter
    max_geno = st.sidebar.slider("Max Genotoxicity", min_value=0.0, max_value=1.0, value=0.5, step=0.05)
    
    # PAINS Filter
    exclude_pains = st.sidebar.checkbox("Exclude PAINS (Assay Interference)", value=True)

    # --- 4. APPLY FILTERS ---
    filtered_df = df.copy()
    
    # Apply text search if the user typed a name
    if search_query:
        filtered_df = filtered_df[filtered_df[name_col].str.contains(search_query, case=False, na=False)]
    
    if 'PAINS' in filtered_df.columns:
        filtered_df['PAINS'] = filtered_df['PAINS'].astype(str).str.strip()
        if exclude_pains:
            filtered_df = filtered_df[filtered_df['PAINS'].isin(['0', '0.0', '[-]'])]
            
    def safe_filter(dataframe, column, condition, value):
        if column in dataframe.columns:
            dataframe[column] = pd.to_numeric(dataframe[column], errors='coerce')
            if condition == '<=':
                return dataframe[dataframe[column] <= value]
            elif condition == '>=':
                return dataframe[dataframe[column] >= value]
        return dataframe

    # Apply all numeric sliders
    filtered_df = safe_filter(filtered_df, 'Vina Score NS5', '<=', max_vina_ns5)
    filtered_df = safe_filter(filtered_df, 'Vina Score hSTAT2', '<=', max_vina_hstat2)
    filtered_df = safe_filter(filtered_df, 'QED', '>=', min_qed)
    filtered_df = safe_filter(filtered_df, 'DILI', '<=', max_dili)
    filtered_df = safe_filter(filtered_df, 'hERG', '<=', max_herg)
    filtered_df = safe_filter(filtered_df, 'Ototoxicity', '<=', max_ototox)
    filtered_df = safe_filter(filtered_df, 'Neurotoxicity-DI', '<=', max_neurotox)
    filtered_df = safe_filter(filtered_df, 'Nephrotoxicity-DI', '<=', max_nephrotox)
    filtered_df = safe_filter(filtered_df, 'Hematotoxicity', '<=', max_hematotox)
    filtered_df = safe_filter(filtered_df, 'Respiratory', '<=', max_resp)
    filtered_df = safe_filter(filtered_df, 'Carcinogenicity', '<=', max_carc)
    filtered_df = safe_filter(filtered_df, 'Genotoxicity', '<=', max_geno)

    # --- 5. MAIN DASHBOARD VISUALIZATIONS ---
    col1, col2 = st.columns(2)
    with col1:
        st.metric(label="Total Initial Compounds", value=len(df))
    with col2:
        st.metric(label="Candidates Passing Filters", value=len(filtered_df))

    st.markdown("---")
    
    st.subheader("📊 Chemical Space: Binding Affinity vs. Toxicity")
    if not filtered_df.empty and 'Vina Score NS5' in filtered_df.columns and 'DILI' in filtered_df.columns:
        hover_data = [name_col, 'SMILES']
        for col in ['total score', 'comp score', 'QED', 'Ototoxicity', 'Neurotoxicity-DI', 'Respiratory', 'Genotoxicity']:
            if col in filtered_df.columns:
                hover_data.append(col)
                
        fig = px.scatter(
            filtered_df, 
            x='Vina Score NS5', 
            y='DILI', 
            color='QED' if 'QED' in filtered_df.columns else None,
            hover_data=hover_data,
            color_continuous_scale='Viridis',
            title="Dengue NS5 Affinity vs. Liver Toxicity (Hover for details)"
        )
        fig.update_xaxes(autorange="reversed")
        
        st.plotly_chart(fig, width='stretch')
    else:
        st.warning("No compounds match the current filter criteria or required columns are missing.")

    # --- 6. DATA TABLE EXPORT ---
    st.subheader("📋 Filtered Candidates Data")
    st.dataframe(filtered_df)

    csv = filtered_df.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="Download Filtered Data as CSV",
        data=csv,
        file_name='Dashboard_Top_Candidates.csv',
        mime='text/csv',
    )
