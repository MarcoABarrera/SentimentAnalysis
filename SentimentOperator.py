import pandas as pd
import joblib
from sklearn.feature_extraction.text import TfidfVectorizer

# Load saved model and vectorizer
model = joblib.load("logistic_model.pkl")
vectorizer = joblib.load("vectorizer.pkl")

# Load the dataset (small portion or already preloaded)
#df = pd.read_csv("cleaned_comments.csv", nrows=100_000)
url = "https://redditcommentscleaned.blob.core.windows.net/data/cleaned_comments.csv"
    #df = pd.read_csv("cleaned_comments.csv", nrows=50000)
df = pd.read_csv(url)
df['label'] = df['score'].apply(lambda x: 1 if x > 2 else 0)

# Start keyword query loop
while True:
    keyword = input("\nEnter a keyword to analyze sentiment (or type 'exit' to quit): ").lower().strip()
    if keyword == 'exit':
        break

    # Filter comments containing the keyword
    filtered_df = df[df['cleaned_text'].str.contains(keyword, case=False, na=False)]
    if filtered_df.empty:
        print("No comments found with that keyword.")
        continue

    # Vectorize and predict sentiment
    X_filtered = vectorizer.transform(filtered_df['cleaned_text'])
    predictions = model.predict(X_filtered)

    # Show results
    filtered_df['predicted_sentiment'] = predictions
    sentiment_counts = filtered_df['predicted_sentiment'].value_counts(normalize=True)

    print(f"\nSentiment toward '{keyword}':")
    print(f"Positive: {sentiment_counts.get(1, 0)*100:.2f}%")
    print(f"Negative: {sentiment_counts.get(0, 0)*100:.2f}%")
