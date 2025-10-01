import streamlit as st
import pandas as pd
from io import BytesIO

st.set_page_config(page_title="CSV Cleaner App", layout="wide")

st.title("📊 CSV Cleaner and Analyzer")

# File uploader
uploaded_file = st.file_uploader("Upload your CSV file", type=["csv"])

if uploaded_file is not None:
    # Load CSV
    df = pd.read_csv(uploaded_file)

    st.write("### 🔍 Original Data ###")
    st.dataframe(df, use_container_width=True, height=600)


    # ---------- Cleaning & Processing ----------
    # Example: Clean website URLs if 'Website' in df.columns:
    if "Website" in df.columns:
        df["Cleaned Website"] = (
            df["Website"]
            .str.replace(r"^https?:\/\/", "", regex=True)
            .str.replace(r"^www\.", "", regex=True)
            .str.rstrip("/")
        )

    # Example: Find duplicate companies
    if "Company" in df.columns:
        company_counts = df["Company"].value_counts()
        companies_with_duplicates = company_counts[company_counts > 1]

    st.write("### 🏢 Duplicate Companies")
    if companies_with_duplicates.empty:
        st.success("No duplicate companies found ✅")
    else:
        # Show summary of duplicate companies
        st.write(companies_with_duplicates)

        # Show customers belonging to duplicate companies
        duplicate_company_customers = df[df["Company"].isin(companies_with_duplicates.index)]
        st.write("#### 👥 Customers in Duplicate Companies")
        st.dataframe(
            duplicate_company_customers[["Company", "First Name", "Last Name", "City"]],
            use_container_width=True
        )



    # Example: Find duplicate cities
    if "City" in df.columns:
        city_counts = df["City"].value_counts()
        cities_with_duplicates = city_counts[city_counts > 1]

        st.write("### 🌆 Duplicate Cities")
        if cities_with_duplicates.empty:
            st.success("No duplicate cities found ✅")
        else:
            st.write(cities_with_duplicates)
    # 4) Sort by subscription date (new feature)
    df_sorted = df.copy()  # keep original for display
    if "Subscription Date" in df.columns:
        df_sorted["Subscription Date"] = pd.to_datetime(df_sorted["Subscription Date"], errors="coerce")
        df_sorted = df_sorted.sort_values("Subscription Date", ascending=True).reset_index(drop=True)

        st.write("### 📅 Customers Sorted by Subscription Date")
        st.dataframe(df_sorted, use_container_width=True, height=600)
    else:
        st.warning("⚠️ No 'Subscription Date' column found. Skipping sorting step.")


    # ---------- Download Cleaned File ----------
    st.write("### 💾 Download Processed Data")

    buffer = BytesIO()
    df_sorted.to_csv(buffer, index=False)
    buffer.seek(0)

    st.download_button(
        label="📥 Download cleaned CSV",
        data=buffer,
        file_name="cleaned_output.csv",
        mime="text/csv"
    )
