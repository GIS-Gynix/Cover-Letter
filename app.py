import streamlit as st
import pandas as pd
import re

# --- CONFIGURATION ---
# Replace with your Google Sheet link
SHEET_URL = "https://docs.google.com/spreadsheets/d/1dvuymQqn8ytxc18pPWr-csqZ_Ke8whO3UCIa6x6XBto/edit?usp=sharing"

def get_ss_id(url):
    match = re.search(r"/spreadsheets/d/([a-zA-Z0-9-_]+)", url)
    return match.group(1) if match else None

st.set_page_config(page_title="Multi-Sheet CSV Dashboard", layout="wide")

st.title("🏙️ Multi-Sheet City CSV Generator")

@st.cache_data(ttl=60)
def load_all_sheets(url):
    ss_id = get_ss_id(url)
    if not ss_id:
        return None
    # Exporting as XLSX to access all tabs
    export_url = f"https://docs.google.com/spreadsheets/d/{ss_id}/export?format=xlsx"
    return pd.read_excel(export_url, sheet_name=None, engine='openpyxl')

try:
    sheets_dict = load_all_sheets(SHEET_URL)
    
    search_id = st.text_input("🔍 Search City ID across all tabs:", placeholder="Enter ID...")

    if search_id:
        found = False
        for sheet_name, df in sheets_dict.items():
            # Clean column names to handle accidental spaces
            df.columns = [str(c).strip() for c in df.columns]
            
            # Look for ID column
            id_col = next((c for c in df.columns if c.lower() in ['city id', 'cityid', 'id']), None)
            
            if id_col:
                match = df[df[id_col].astype(str).str.strip() == str(search_id).strip()]
                
                if not match.empty:
                    found = True
                    st.success(f"✅ Found in Tab: {sheet_name}")
                    st.dataframe(match)
                    
                    # Columns from your provided CSV sample
                    target_cols = ['imdad_link', 'source_type', 'zoning', 'map_date']
                    
                    # Check if columns exist in this specific tab
                    available = [c for c in target_cols if c in df.columns]
                    
                    if len(available) == len(target_cols):
                        final_df = match[target_cols]
                        csv_data = final_df.to_csv(index=False).encode('utf-8')
                        
                        st.download_button(
                            label=f"💾 Download {search_id} CSV",
                            data=csv_data,
                            file_name=f"{search_id}_imdad.csv",
                            mime="text/csv"
                        )
                    else:
                        missing = set(target_cols) - set(available)
                        st.warning(f"⚠️ Tab '{sheet_name}' is missing columns: {missing}")
                    break
        
        if not found:
            st.error("❌ City ID not found in any tab.")

except Exception as e:
    if "openpyxl" in str(e):
        st.error("Missing Library: Please run 'pip install openpyxl' in your terminal.")
    else:
        st.error(f"Error: {e}")
