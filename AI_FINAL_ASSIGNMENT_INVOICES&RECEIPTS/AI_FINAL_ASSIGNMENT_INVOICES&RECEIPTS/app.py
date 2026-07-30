import streamlit as st
import pandas as pd
import numpy as np
import pickle
import json
import re
from tensorflow.keras.models import load_model
import matplotlib.pyplot as plt

# LOAD DATA + MODELS

@st.cache_data
def load_invoice_data():
    b1 = pd.read_csv("batch1_1.csv")
    b2 = pd.read_csv("batch1_2.csv")
    b3 = pd.read_csv("batch1_3.csv")
    df = pd.concat([b1, b2, b3], ignore_index=True).drop_duplicates()
    return df

@st.cache_data
def load_training_data():
    return pd.read_csv("merged_df.csv")

@st.cache_resource
def load_tfidf():
    with open("tfidf.pkl", "rb") as f:
        return pickle.load(f)

@st.cache_resource
def load_nn():
    return load_model("nn_model.keras")

invoice_df = load_invoice_data()
training_df = load_training_data()
tfidf = load_tfidf()
nn_model = load_nn()

# HELPER FUNCTIONS

def parse_number(num_str):
    if not num_str:
        return None

    num_str = num_str.replace(" ", "").replace(",", ".")

    try:
        return float(num_str)
    except:
        return None


def extract_invoice_info(json_text):
    """Extract invoice metadata + items."""
    data = {}

    # Metadata patterns
    patterns = {
        "Client_name": r'"client_name"\s*:\s*"([^"]+)"',
        "Seller_name": r'"seller_name"\s*:\s*"([^"]+)"',
        "Invoice_no": r'"invoice_number"\s*:\s*"([^"]+)"',
        "Invoice_date": r'"invoice_date"\s*:\s*"([^"]+)"',
        "Total": r'"total"\s*:\s*"([^"]+)"'
    }

    for key, pattern in patterns.items():
        match = re.search(pattern, json_text)
        data[key] = match.group(1) if match else None

    # Fix total numeric type
    if data["Total"]:
        data["Total"] = parse_number(data["Total"])

    # Extract line items
    items = re.findall(
        r'"description"\s*:\s*"([^"]+)"\s*,\s*"quantity"\s*:\s*"([^"]+)"\s*,\s*"total_price"\s*:\s*"([^"]+)"',
        json_text
    )

    cleaned_items = []
    for desc, qty, price in items:

        # Remove escaped AND real newlines
        desc = (
            desc.replace("\\n", " ")
                .replace("\n", " ")
                .replace("  ", " ")
                .strip()
        )

        cleaned_items.append({
            "description": desc,
            "quantity": parse_number(qty),
            "total_price": parse_number(price)
        })

    data["Items"] = cleaned_items

    return data


@st.cache_data
def parse_all_json(df):
    df["Parsed"] = df["Json Data"].apply(extract_invoice_info)
    return df

# STREAMLIT UI 

st.title("Smart Invoice and Receipt Analyzer")

tab1, tab2 = st.tabs(["Invoice Search", "AI Model & Graphs"])

# TAB 1: INVOICE SEARCH + VIEWER

with tab1:

    st.header("Search for any invoice number")

    invoice_df = parse_all_json(invoice_df)

    # Build normalized dataframe for searching
    searchable = pd.DataFrame([
        {
            "File Name": row["File Name"],
            "Invoice_no": row["Parsed"]["Invoice_no"],
            "Client_name": row["Parsed"]["Client_name"],
            "Seller_name": row["Parsed"]["Seller_name"],
            "Invoice_date": row["Parsed"]["Invoice_date"],
            "Total": row["Parsed"]["Total"],
            "Items": row["Parsed"]["Items"]
        }
        for _, row in invoice_df.iterrows()
    ])

    query = st.text_input("Enter Invoice Number (exact or partial):")

    if query:
        results = searchable[
            searchable["Invoice_no"].str.contains(query, na=False)
        ]

        st.write(f"### {len(results)} result(s) found")

        for idx, row in results.iterrows():
            st.write("---")
            st.subheader(f"🧾 Invoice {row['Invoice_no']}")
            st.write(f"**Client:** {row['Client_name']}")
            st.write(f"**Seller:** {row['Seller_name']}")
            st.write(f"**Date:** {row['Invoice_date']}")
            st.write(f"**Total:** {row['Total']}")

            items_df = pd.DataFrame(row["Items"])
            st.write("### Items")
            st.dataframe(items_df, use_container_width=True)

# TAB 2: MODEL, GRAPHS, PREDICTION

with tab2:

    st.header("Neural Network Model Performance")

    metrics = {
        "Accuracy": 0.972,
        "Precision": 0.963,
        "Recall": 0.960,
        "F1 Score": 0.961
    }

    st.write(pd.DataFrame(metrics, index=["NN Model"]))

    # Prediction Section
    st.header("Test Model with Custom OCR Text")

    user_input = st.text_area("Paste OCR Item Description:")

    if st.button("Run Prediction"):
        if user_input.strip() == "":
            st.warning("Please enter text first.")
        else:
            X = tfidf.transform([user_input]).toarray()
            pred = nn_model.predict(X)[0][0]

            st.write("### Prediction:", round(float(pred), 4))

            if pred > 0.5:
                st.success("Likely a correct item description.")
            else:
                st.error("Likely inaccurate OCR — needs review.")

    # Error Analysis Graphs
    st.header("Error Analysis")

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Quantity Error (%)")
        fig1, ax1 = plt.subplots()
        ax1.hist(training_df["Quantity_error_pct"].dropna(), bins=20)
        st.pyplot(fig1)

    with col2:
        st.subheader("Total Price Error (%)")
        fig2, ax2 = plt.subplots()
        ax2.hist(training_df["Total_price_error_pct"].dropna(), bins=20)
        st.pyplot(fig2)
