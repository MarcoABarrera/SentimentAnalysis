FROM flink:1.17.2

# Set environment variables
ENV KAFKA_VERSION=3.1.0
ENV SCALA_VERSION=2.12
ENV KAFKA_PYTHON=2.0.2
ENV CONFLUENT_KAFKA_VERSION=2.3.0
ENV PYFLINK_VERSION=1.17.2
ENV FLINK_VERSION=1.17.2
ENV NLTK_DATA=/opt/flink/nltk_data
ENV PYTHONPATH=/opt/flink/opt/python

# Install Python and pip
RUN apt-get update && \
    apt-get install -y python3 python3-pip && \
    ln -s /usr/bin/python3 /usr/bin/python && \
    pip3 install --upgrade pip

# Install required Python packages
RUN pip install \
    kafka-python==${KAFKA_PYTHON} \
    confluent-kafka==${CONFLUENT_KAFKA_VERSION} \
    apache-flink==${PYFLINK_VERSION} \
    nltk \
    emoji

# Download NLTK data into a known location used in runtime
RUN mkdir -p $NLTK_DATA && \
    python -c "import nltk; \
               nltk.download('punkt', download_dir='$NLTK_DATA'); \
               nltk.download('stopwords', download_dir='$NLTK_DATA'); \
               nltk.download('punkt_tab', download_dir='$NLTK_DATA')"
    

# Add Kafka connector JARs to Flink lib
ADD https://repo1.maven.org/maven2/org/apache/flink/flink-connector-kafka/1.17.2/flink-connector-kafka-1.17.2.jar /opt/flink/lib/
ADD https://repo1.maven.org/maven2/org/apache/kafka/kafka-clients/3.5.1/kafka-clients-3.5.1.jar /opt/flink/lib/
ADD https://repo1.maven.org/maven2/org/apache/flink/flink-connector-kafka/${FLINK_VERSION}/flink-connector-kafka-${FLINK_VERSION}.jar /opt/flink/lib/
ADD https://repo1.maven.org/maven2/org/apache/kafka/kafka-clients/3.5.1/kafka-clients-3.5.1.jar /opt/flink/lib/
ADD https://repo1.maven.org/maven2/org/apache/flink/flink-sql-connector-kafka/${FLINK_VERSION}/flink-sql-connector-kafka-${FLINK_VERSION}.jar /opt/flink/lib/

# Set PYTHONPATH for PyFlink
ENV PYTHONPATH=/opt/flink/opt/python