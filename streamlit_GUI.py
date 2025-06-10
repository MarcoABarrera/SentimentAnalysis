import streamlit as st
import pandas as pd
import joblib
import matplotlib.pyplot as plt
from datetime import datetime

# Load model and vectorizer
model = joblib.load("sentiment_model.joblib")
vectorizer = joblib.load("vectorizer.joblib")

# Loading the preprocessed data
@st.cache_data
def load_data(keyword):
    url = "https://redditcommentscleaned.blob.core.windows.net/data/cleaned_comments.csv"
    chunk_iter = pd.read_csv(url, chunksize=100000)
    relevant_chunks = []
    for chunk in chunk_iter:
        mask = chunk['cleaned_text'].str.contains(keyword, case=False, na=False)
        if mask.any():
            relevant_chunks.append(chunk[mask])
    if not relevant_chunks:
        return None
    df = pd.concat(relevant_chunks)
    df['timestamp'] = pd.to_datetime(df['created_utc'], unit='s')
    return df

df = load_data()

# --- Streamlit UI ---
st.title("Sentiment Analysis Dashboard")
st.write("Please enter two keywords to compare their sentiment in Reddit comments.")

col1, col2 = st.columns(2)
keyword1 = col1.text_input("Keyword 1", value="ai")
keyword2 = col2.text_input("Keyword 2", value="human")

#Creating the Analyze button to run the model
if st.button("Analyze"):
    def analyze_keyword(keyword):
        subset = df[df['cleaned_text'].str.contains(keyword, case=False, na=False)]
        if subset.empty:
            return None, None, None

        X = vectorizer.transform(subset['cleaned_text'])
        preds = model.predict(X)
        subset['sentiment'] = preds

        sentiment_counts = subset['sentiment'].value_counts().sort_index()
        sentiment_counts = sentiment_counts.reindex([0, 1], fill_value=0)

        sentiment_over_time = subset.groupby(subset['timestamp'].dt.date)['sentiment'].mean()
        return sentiment_counts, sentiment_over_time, len(subset)

    st.subheader(f"Sentiment for: {keyword1}")
    counts1, timeline1, total1 = analyze_keyword(keyword1)
    if counts1 is not None:
        st.write(f"Total comments: {total1}")
        st.bar_chart(counts1.rename({0: "Negative", 1: "Positive"}))
        st.line_chart(timeline1)
    else:
        st.warning("No matching comments found.")

    st.subheader(f"Sentiment for: {keyword2}")
    counts2, timeline2, total2 = analyze_keyword(keyword2)
    if counts2 is not None:
        st.write(f"Total comments: {total2}")
        st.bar_chart(counts2.rename({0: "Negative", 1: "Positive"}))
        st.line_chart(timeline2)
    else:
        st.warning("No matching comments found.")
