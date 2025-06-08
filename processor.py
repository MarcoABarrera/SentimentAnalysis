from pyflink.datastream import StreamExecutionEnvironment
from pyflink.common.serialization import SimpleStringSchema
from pyflink.datastream.connectors import FlinkKafkaConsumer, FlinkKafkaProducer
from pyflink.common.typeinfo import Types
import json
import emoji
import re

# Custom list of English stopwords
EN_STOPWORDS = {
    'a', 'about', 'above', 'after', 'again', 'against', 'all', 'am', 'an',
    'and', 'any', 'are', 'as', 'at', 'be', 'because', 'been', 'before',
    'being', 'below', 'between', 'both', 'but', 'by', 'could', 'did', 'do',
    'does', 'doing', 'down', 'during', 'each', 'few', 'for', 'from', 'further',
    'had', 'has', 'have', 'having', 'he', 'her', 'here', 'hers', 'herself',
    'him', 'himself', 'his', 'how', 'i', 'if', 'in', 'into', 'is', 'it', "it's",
    'its', 'itself', 'just', 'me', 'more', 'most', 'my', 'myself', 'no', 'nor',
    'not', 'of', 'off', 'on', 'once', 'only', 'or', 'other', 'ought', 'our',
    'ours', 'ourselves', 'out', 'over', 'own', 'same', 'she', 'should', 'so',
    'some', 'such', 'than', 'that', 'the', 'their', 'theirs', 'them',
    'themselves', 'then', 'there', 'these', 'they', 'this', 'those', 'through',
    'to', 'too', 'under', 'until', 'up', 'very', 'was', 'we', 'were', 'what',
    'when', 'where', 'which', 'while', 'who', 'whom', 'why', 'with', 'would',
    'you', 'your', 'yours', 'yourself', 'yourselves'
}

def preprocess_text(text):
    text = text.lower()
    tokens = re.findall(r'\w+|\S', text)  # \w+ catches words, \S captures emojis/punctuation
    return [
        word for word in tokens
        if (word.isalpha() or emoji.demojize(word) != word)  # keep emojis
        and word not in EN_STOPWORDS
    ]

def is_high_quality_comment(comment): #this function filters out all the empty/deleted or short messages (to avoid spam)
    MIN_WORD_COUNT = 5
    MIN_SCORE = 1
    BANNED_PHRASES = ['[removed]', '[deleted]', '']
    
    body = comment.get('body', '').strip()
    score = comment.get('score', 0)
    
    if (body in BANNED_PHRASES or 
        len(body.split()) < MIN_WORD_COUNT or 
        int(score) < MIN_SCORE):
        return False
    return True

def main():
    env = StreamExecutionEnvironment.get_execution_environment()
    env.set_parallelism(1)
    env.add_jars(
        "file:///opt/flink/lib/flink-connector-kafka-1.17.2.jar",
        "file:///opt/flink/lib/kafka-clients-3.5.1.jar"
    )

    kafka_consumer = FlinkKafkaConsumer(
        topics='reddit-comments',
        deserialization_schema=SimpleStringSchema(),
        properties={
            'bootstrap.servers': 'kafka:29092',
            'group.id': 'flink-group',
            'auto.offset.reset': 'earliest'
        }
    )

    kafka_producer = FlinkKafkaProducer(
        topic='reddit-comments-processed',
        serialization_schema=SimpleStringSchema(),
        producer_config={'bootstrap.servers': 'kafka:29092'}
    )

    def process(record):
        try:
            data = json.loads(record)
            if not is_high_quality_comment(data):
                return None
                
            cleaned_tokens = preprocess_text(data['body'])
            if len(cleaned_tokens) < 3:
                return None
                
            data.update({
                'processed': True,
                'word_count': len(cleaned_tokens),
                'cleaned_text': ' '.join(cleaned_tokens),
                'original_length': len(data['body'])
            })
            return json.dumps(data)
            
        except Exception as e:
            print(f"Error: {e}")
            return None

    env.add_source(kafka_consumer) \
        .map(process, output_type=Types.STRING()) \
        .filter(lambda x: x is not None) \
        .add_sink(kafka_producer)

    env.execute("Reddit Comments Processor")

if __name__ == '__main__':
    main()
