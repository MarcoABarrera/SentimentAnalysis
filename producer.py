import zstandard as zstd
import json
import io
from kafka import KafkaProducer

START_TS = 1554076800
END_TS = 1555472130
TOPIC = "reddit-comments"

producer = KafkaProducer(
    bootstrap_servers='localhost:9092', #192.168.1.100:9092 localhost:9092
    value_serializer=lambda v: json.dumps(v).encode('utf-8'),
    retries=5,
    acks='all',
    linger_ms=100,  # slight delay to batch messages
    batch_size=32*1024  # 32KB batches
)

file_path = "data/RC_2019-04.zst" #bringing the data from the .zst

print("Streaming filtered Reddit comments to Kafka...") #printing for debugging

with open(file_path, 'rb') as fh: #decompressing the file
    dctx = zstd.ZstdDecompressor()
    stream_reader = dctx.stream_reader(fh)
    text_stream = io.TextIOWrapper(stream_reader, encoding='utf-8')

    for line in text_stream:
        try:
            comment = json.loads(line)
            created = int(comment.get('created_utc', 0))

            if START_TS <= created <= END_TS:
                payload = {
                    'body': comment.get('body', ''),
                    'created_utc': created,
                    'subreddit': comment.get('subreddit', ''),
                    'id': comment.get('id', ''),
                    'author': comment.get('author', ''),
                    'score': comment.get('score', ''),
                    'controversiality': comment.get('controversiality', '')
                }
                producer.send(TOPIC, value=payload)

        except Exception:
            continue

producer.flush()
print("All filtered comments have been sent to Kafka!")

