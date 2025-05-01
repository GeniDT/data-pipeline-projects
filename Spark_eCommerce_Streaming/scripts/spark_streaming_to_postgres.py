from pyspark.sql import SparkSession
from pyspark.sql.types import StructType, StructField, StringType, TimestampType
from pyspark.sql.functions import col, to_timestamp

# Initialize Spark session
spark = SparkSession.builder \
    .appName("EcommerceStreamingToPostgres") \
    .master("spark://spark:7077") \
    .config("spark.jars", "/opt/bitnami/spark/jars/postgresql-42.7.4.jar") \
    .getOrCreate()

# Define schema for input CSV files
schema = StructType([
    StructField("timestamp", StringType(), False),
    StructField("user_id", StringType(), False),
    StructField("product_id", StringType(), False),
    StructField("event_type", StringType(), False)
])

# Read streaming CSV files from data_stream with header
input_path = "/opt/bitnami/spark/data_stream"
df = spark.readStream \
    .schema(schema) \
    .option("header", "true") \
    .csv(input_path)

# Process the data: cast timestamp to TimestampType
processed_df = df.withColumn("timestamp", to_timestamp(col("timestamp"), "yyyy-MM-dd'T'HH:mm:ss.SSSSSS"))

# PostgreSQL connection details (from environment variables)
jdbc_url = f"jdbc:postgresql://{spark.conf.get('spark.postgres.host')}:{spark.conf.get('spark.postgres.port')}/{spark.conf.get('spark.postgres.db')}"
connection_properties = {
    "user": spark.conf.get("spark.postgres.user"),
    "password": spark.conf.get("spark.postgres.password"),
    "driver": "org.postgresql.Driver"
}

# Write stream to PostgreSQL
def write_to_postgres(batch_df, batch_id):
    batch_df.write \
        .mode("append") \
        .jdbc(url=jdbc_url, table="events", properties=connection_properties)

query = processed_df.writeStream \
    .foreachBatch(write_to_postgres) \
    .option("checkpointLocation", "/opt/bitnami/spark/checkpoint") \
    .start()

# Wait for the streaming query to terminate
query.awaitTermination()