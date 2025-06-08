from kafka import KafkaConsumer
import json
import csv

consumer = KafkaConsumer(
    'reddit-comments-processed',
    bootstrap_servers='localhost:9092',
    auto_offset_reset='earliest',
    value_deserializer=lambda m: json.loads(m.decode('utf-8'))
)

with open('cleaned_comments.csv', 'w', newline='', encoding='utf-8') as f:
    writer = csv.DictWriter(f, fieldnames=['cleaned_text', 'score', 'subreddit'])
    writer.writeheader()
    for message in consumer:
        data = message.value
        writer.writerow({
            'cleaned_text': data.get('cleaned_text', ''),
            'score': data.get('score', 0),
            'subreddit': data.get('subreddit', '')
        })
