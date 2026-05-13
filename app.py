import streamlit as st
import pandas as pd
import re

# --- CONFIGURATION ---
# Use the standard Google Sheets URL (Anyone with link can view)
SHEET_URL = "PASTE_YOUR_GOOGLE_SHEET_LINK_HERE"

def get_ss_id(url):
    """Extracts the unique spreadsheet ID from the URL."""
    match = re.search(r"/spreadsheets/d/([a-zA-Z0-9-_]+)", url)
    return match.group(1) if match else None

st.set_page_config(page_title="Global City Search", layout="wide")

st.title("🏙️ Multi-Sheet City CSV Generator")
st.markdown("This dashboard searches **every tab** in your Google Sheet for the specified City ID.")

@st.cache_data(ttl=60)
def load_all_sheets(url):
    ss_id = get_ss_id(url)
    if not ss_id:
        return None
    # We export as XLSX to get access to all sheets at once
    export_url = f"https://docs.google.com/spreadsheets/d/{ss_id}/export?format=xlsx"
    # returns a dictionary: { "Sheet1": dataframe, "Sheet2": dataframe, ... }
    return pd.read_excel(export_url, sheet_name=None)

try:
    sheets_dict = load_all_sheets(SHEET_URL)
    
    # SEARCH BAR
    search_id = st.text_input("🔍 Enter City ID:", placeholder="Enter ID to search across all tabs...")

    if search_id:
        found = False
        
        # Iterate through every sheet in the Google Sheet
        for sheet_name, df in sheets_dict.items():
            # Check if 'City ID' column exists in this specific sheet
            if 'City ID' in df.columns:
                # Search for the ID (converted to string for safety)
                match = df[df['City ID'].astype(str).str.strip() == str(search_id).strip()]
                
                if not match.empty:
                    found = True
                    st.success(f"📍 Match found in tab: **{sheet_name}**")
                    
                    # Preview the data
                    st.subheader("Data Preview")
                    st.dataframe(match)

                    # Filter for your specific 4 columns
                    target_columns = ['imdad_link', 'source_type', 'zoning', 'map_date']
                    
                    # Verify columns exist in this sheet
                    missing = [c for c in target_columns if c not in df.columns]
                    
                    if not missing:
                        final_df = match[target_columns]
                        
                        # Generate CSV
                        csv_data = final_df.to_csv(index=False).encode('utf-8')
                        
                        st.divider()
                        st.download_button(
                            label=f"💾 Download CSV from {sheet_name}",
                            data=csv_data,
                            file_name=f"{search_id}_imdad_link.csv",
                            mime="text/csv"
                        )
                        st.info("💡 Remember: Set your browser to 'Ask where to save' to pick a specific folder.")
                    else:
                        st.error(f"Tab '{sheet_name}' is missing columns: {missing}")
                    
                    # Stop searching once we find the first match
                    break 
        
        if not found:
            st.error(f"❌ City ID '{search_id}' was not found in any of the {len(sheets_dict)} sheets.")

except Exception as e:
    st.error(f"Error loading Google Sheet: {e}")
    st.info("Ensure the sheet is shared so 'Anyone with the link' can View.")