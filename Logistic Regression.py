import pandas as pd
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report

# Step 1: Load a manageable subset of your data
df = pd.read_csv("cleaned_comments.csv", nrows=100_000)

# Initialize VADER sentiment analyzer
analyzer = SentimentIntensityAnalyzer()

# Apply VADER to generate sentiment scores for each comment
def get_sentiment_label(text):
    vs = analyzer.polarity_scores(text)
    compound = vs['compound']
    # Define label based on compound score thresholds
    if compound >= 0.05:
        return 1  # Positive
    elif compound <= -0.05:
        return 0  # Negative
    else:
        return None  # Neutral / unclear - we can drop these or treat differently

df['label'] = df['cleaned_text'].apply(get_sentiment_label)

# Remove rows with neutral or unclear sentiment (label == None)
df = df.dropna(subset=['label'])
df['label'] = df['label'].astype(int)

print(f"Class distribution after labeling:\n{df['label'].value_counts()}")

# Optional: balance classes by downsampling the majority class
min_class = df['label'].value_counts().min()
balanced_df = pd.concat([
    df[df['label'] == 0].sample(min_class, random_state=42),
    df[df['label'] == 1].sample(min_class, random_state=42)
])

# Step 2: Vectorize the text with TF-IDF
vectorizer = TfidfVectorizer(
    max_features=10000,
    ngram_range=(1, 2),
    stop_words='english',
    min_df=5,
    max_df=0.9,
    sublinear_tf=True
)
X = vectorizer.fit_transform(balanced_df['cleaned_text'])
y = balanced_df['label']

# Train/test split
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y
)

# Train logistic regression
model = LogisticRegression(max_iter=1000, class_weight='balanced')
model.fit(X_train, y_train)

# Predict and evaluate
y_pred = model.predict(X_test)

print("Accuracy:", accuracy_score(y_test, y_pred))
print("\nClassification Report:\n", classification_report(y_test, y_pred))


####Saving the model and the Vectorizer
import joblib

# Save the trained model and vectorizer (for SentimentOperator code)
joblib.dump(model, "logistic_model.pkl")
joblib.dump(vectorizer, "vectorizer.pkl")

# Save the trained model and vectorizer (in joblib format for GUI code)
joblib.dump(model, "sentiment_model.joblib")
joblib.dump(vectorizer, "vectorizer.joblib")
