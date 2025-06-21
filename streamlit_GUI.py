import streamlit as st
import pandas as pd
import joblib
import plotly.express as px

# Load model and vectorizer
model = joblib.load("sentiment_model.joblib")
vectorizer = joblib.load("vectorizer.joblib")

# Load data from Azure Blob in chunks
@st.cache_data(show_spinner="Loading data from Azure Blob...")
def load_matching_data_from_blob(keyword1, keyword2, target_rows=500_000, chunk_size=100_000):
    url = "https://redditcommentscleaned.blob.core.windows.net/data/cleaned_comments.csv"
    matched_frames = []
    row_count = 0

    chunk_iter = pd.read_csv(url, chunksize=chunk_size)
    for chunk in chunk_iter:
        chunk['timestamp'] = pd.to_datetime(chunk['created_utc'], unit='s')
        mask = (chunk['cleaned_text'].str.contains(keyword1, case=False, na=False)) | \
               (chunk['cleaned_text'].str.contains(keyword2, case=False, na=False))
        matched = chunk[mask]
        matched_frames.append(matched)
        row_count += len(matched)
        if row_count >= target_rows:
            break

    if matched_frames:
        return pd.concat(matched_frames)
    else:
        return pd.DataFrame()

# Analysis function
def analyze_keyword(df, keyword):
    subset = df[df['cleaned_text'].str.contains(keyword, case=False, na=False)]
    if subset.empty:
        return None, None, None

    X = vectorizer.transform(subset['cleaned_text'])
    preds = model.predict(X)
    subset['sentiment'] = preds

    sentiment_counts = subset['sentiment'].value_counts().sort_index().reindex([0, 1], fill_value=0)

    daily_sentiment = subset.groupby(subset['timestamp'].dt.date)['sentiment'].mean().reset_index()
    daily_sentiment.columns = ['time', 'average_sentiment']

    if daily_sentiment['time'].nunique() == 1:
        subset['hour'] = subset['timestamp'].dt.floor('H')
        daily_sentiment = subset.groupby('hour')['sentiment'].mean().reset_index()
        daily_sentiment.columns = ['time', 'average_sentiment']

    return sentiment_counts, daily_sentiment, len(subset)

# Streamlit UI
st.title("Sentiment Analysis Dashboard")
st.write("Enter two keywords to analyze sentiment in Reddit comments from Azure Blob storage.")

col_input1, col_input2 = st.columns(2)
keyword1 = col_input1.text_input("Keyword 1", value="ai")
keyword2 = col_input2.text_input("Keyword 2", value="human")

if st.button("Analyze"):
    with st.spinner("Loading and filtering data..."):
        df = load_matching_data_from_blob(keyword1, keyword2)

    if df.empty:
        st.warning("No matching comments found in dataset.")
    else:
        col1, col2 = st.columns(2)

        with col1:
            st.subheader(f"Sentiment for '{keyword1}'")
            counts1, timeline1, total1 = analyze_keyword(df, keyword1)
            if counts1 is not None:
                st.write(f"Total comments: {total1}")
                st.bar_chart(counts1.rename({0: "Negative", 1: "Positive"}))
                fig1 = px.line(
                    timeline1,
                    x="time",
                    y="average_sentiment",
                    title="Sentiment Over Time",
                    markers=True
                )
                fig1.update_traces(line=dict(width=3))
                fig1.update_layout(yaxis=dict(range=[0, 1]))
                st.plotly_chart(fig1, use_container_width=True)
            else:
                st.warning(f"No matching comments for '{keyword1}'.")

        with col2:
            st.subheader(f"Sentiment for '{keyword2}'")
            counts2, timeline2, total2 = analyze_keyword(df, keyword2)
            if counts2 is not None:
                st.write(f"Total comments: {total2}")
                st.bar_chart(counts2.rename({0: "Negative", 1: "Positive"}))
                fig2 = px.line(
                    timeline2,
                    x="time",
                    y="average_sentiment",
                    title="Sentiment Over Time",
                    markers=True
                )
                fig2.update_traces(line=dict(width=3))
                fig2.update_layout(yaxis=dict(range=[0, 1]))
                st.plotly_chart(fig2, use_container_width=True)
            else:
                st.warning(f"No matching comments for '{keyword2}'.")

