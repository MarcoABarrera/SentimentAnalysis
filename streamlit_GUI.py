import streamlit as st
import pandas as pd
import joblib
import plotly.express as px
from azure.data.tables import TableServiceClient

# Load model and vectorizer
model = joblib.load("sentiment_model.joblib")
vectorizer = joblib.load("vectorizer.joblib")

# Azure Table Storage info
account_url = "https://redditcommentscleaned.table.core.windows.net"
sas_token = (
    "sv=2024-11-04&ss=bfqt&srt=sco&sp=rwdlacupiytfx&se=2025-08-31T02:07:56Z&"
    "st=2025-06-22T18:07:56Z&spr=https&sig=yxCLVw%2BcnGLtyOxhtlcAVE%2FQ6OX2iEq8U5MrFtpKXtM%3D"
)
table_name = "ProcessedComments"

@st.cache_data(show_spinner="Loading data from Azure Table Storage...")
def load_matching_data_from_table(keyword1, keyword2, max_rows=10000):
    # Create service client and table client
    service_client = TableServiceClient(endpoint=account_url, credential=sas_token)
    table_client = service_client.get_table_client(table_name=table_name)

    filter_expression = (
        f"(substringof('{keyword1}', cleaned_text) or substringof('{keyword2}', cleaned_text))"
    )

    entities = table_client.query_entities(query_filter=filter_expression)

    data = []
    for entity in entities:
        row = {
            "cleaned_text": entity.get("cleaned_text"),
            "timestamp": pd.to_datetime(entity.get("timestamp"))
        }
        data.append(row)
        if len(data) >= max_rows:
            break

    if data:
        return pd.DataFrame(data)
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

    sentiment_counts = (
        subset['sentiment']
        .value_counts()
        .sort_index()
        .reindex([0, 1], fill_value=0)
    )

    daily_sentiment = (
        subset.groupby(subset['timestamp'].dt.date)['sentiment']
        .mean()
        .reset_index()
    )
    daily_sentiment.columns = ['time', 'average_sentiment']

    if daily_sentiment['time'].nunique() == 1:
        subset['hour'] = subset['timestamp'].dt.floor('H')
        daily_sentiment = (
            subset.groupby('hour')['sentiment']
            .mean()
            .reset_index()
        )
        daily_sentiment.columns = ['time', 'average_sentiment']

    return sentiment_counts, daily_sentiment, len(subset)

# Streamlit UI
st.title("Sentiment Analysis Dashboard")
st.write("Enter two keywords to analyze sentiment in Reddit comments from Azure Table Storage.")

col_input1, col_input2 = st.columns(2)
keyword1 = col_input1.text_input("Keyword 1", value="ai")
keyword2 = col_input2.text_input("Keyword 2", value="human")

if st.button("Analyze"):
    with st.spinner("Loading and filtering data..."):
        df = load_matching_data_from_table(keyword1, keyword2)

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
