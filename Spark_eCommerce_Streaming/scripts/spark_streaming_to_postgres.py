from pyspark.sql import SparkSession
from pyspark.sql.types import StructType, StructField, StringType, TimestampType, IntegerType
from pyspark.sql.functions import col
import logging
import os

# Configure logging
logging.basicConfig(
    filename='/logs/spark_streaming.log',
    level=logging.INFO,
    format='%(asctime)s %(levelname)s %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    # Initialize SparkSession
    spark = SparkSession.builder \
        .appName("EcommerceStreaming") \
        .config("spark.jars", "/opt/bitnami/spark/jars/postgresql-42.7.3.jar") \
        .config("spark.sql.shuffle.partitions", "2") \
        .getOrCreate()

    logger.info("SparkSession initialized")

    # Define schema for CSV
    schema = StructType([
        StructField("event_id", IntegerType(), False),
        StructField("user_id", StringType(), False),
        StructField("action", StringType(), False),
        StructField("product_id", IntegerType(), False),
        StructField("timestamp", TimestampType(), False),
        StructField("created_at", TimestampType(), True)
    ])

    # Read streaming CSV data
    try:
        df = spark.readStream \
            .schema(schema) \
            .option("maxFilesPerTrigger", 10) \
            .option("header", "true") \
            .option("enforceSchema", "true") \
            .csv("/csv-data")

        logger.info("Started reading streaming CSV data from /csv-data")
    except Exception as e:
        logger.error(f"Failed to read streaming data: {str(e)}")
        spark.stop()
        raise e

    # Type casting and transformations
    try:
        # Read existing event_ids from PostgreSQL
        jdbc_url = f"jdbc:postgresql://{os.getenv('POSTGRES_HOST')}:{os.getenv('POSTGRES_PORT')}/{os.getenv('POSTGRES_DB')}"
        existing_ids_df = spark.read \
            .format("jdbc") \
            .option("url", jdbc_url) \
            .option("dbtable", "user_events") \
            .option("user", os.getenv("POSTGRES_USER")) \
            .option("password", os.getenv("POSTGRES_PASSWORD")) \
            .option("driver", "org.postgresql.Driver") \
            .load() \
            .select("event_id") \
            .cache()

        logger.info("Loaded existing event_ids from PostgreSQL")

        # Apply transformations and filter out existing event_ids
        transformed_df = df \
            .withColumn("timestamp", col("timestamp").cast("timestamp")) \
            .withColumn("created_at", col("created_at").cast("timestamp")) \
            .filter(col("event_id").isNotNull()) \
            .filter(col("user_id").isNotNull()) \
            .filter(col("action").isNotNull()) \
            .filter(col("product_id").isNotNull()) \
            .filter(col("timestamp").isNotNull()) \
            .join(existing_ids_df, "event_id", "left_anti")

        # Log sample rows for debugging
        def log_sample_rows(batch_df, batch_id):
            logger.info(f"Sample rows for batch {batch_id}:")
            batch_df.show(5, truncate=False)

        transformed_df.writeStream \
            .foreachBatch(log_sample_rows) \
            .start()

        logger.info("Applied transformations")
    except Exception as e:
        logger.error(f"Transformation failed: {str(e)}")
        spark.stop()
        raise e

    # Write to PostgreSQL
    def write_to_postgres(batch_df, batch_id):
        try:
            batch_df.write.mode("append") \
                .format("jdbc") \
                .option("url", jdbc_url) \
                .option("dbtable", "user_events") \
                .option("user", os.getenv("POSTGRES_USER")) \
                .option("password", os.getenv("POSTGRES_PASSWORD")) \
                .option("driver", "org.postgresql.Driver") \
                .save()
            logger.info(f"Batch {batch_id} written to PostgreSQL")
        except Exception as e:
            logger.error(f"Failed to write batch {batch_id} to PostgreSQL: {str(e)}")
            raise e

    try:
        query = transformed_df.writeStream \
            .foreachBatch(write_to_postgres) \
            .option("checkpointLocation", "/spark-checkpoints") \
            .start()

        logger.info("Started streaming query to PostgreSQL")
        query.awaitTermination()
    except Exception as e:
        logger.error(f"Streaming query failed: {str(e)}")
        spark.stop()
        raise e

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logger.error(f"Application failed: {str(e)}")
        raise e