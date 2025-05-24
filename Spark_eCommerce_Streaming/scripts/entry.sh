#!/bin/bash
echo "Debugging permissions:"
echo "Listing /scripts:"
ls -l /scripts
echo "Listing /app:"
ls -l /app
echo "Listing /spark-checkpoints:"
ls -l /spark-checkpoints
echo "Stat /app:"
stat /app
echo "Stat /scripts/spark_streaming_to_postgres.py:"
stat /scripts/spark_streaming_to_postgres.py
echo "Stat /spark-checkpoints:"
stat /spark-checkpoints
echo "Current user:"
whoami
echo "Environment variables:"
env
echo "Copying spark_streaming_to_postgres.py to /app"
cp /scripts/spark_streaming_to_postgres.py /app/spark_streaming_to_postgres.py
if [ $? -eq 0 ]; then
    echo "Copy successful, setting environment variables"
    export HOME=/home/spark
    export IVY_HOME=/home/spark/.ivy2
    mkdir -p $IVY_HOME
    echo "Running spark-submit"
    spark-submit \
        --conf "spark.jars.ivy=$IVY_HOME" \
        --conf "spark.hadoop.hadoop.security.authentication=simple" \
        --conf "spark.hadoop.fs.file.impl=org.apache.hadoop.fs.LocalFileSystem" \
        /app/spark_streaming_to_postgres.py
else
    echo "Copy failed, exiting"
    exit 1
fi