from pathlib import Path

from pyspark.sql import SparkSession
from pyspark.sql import functions as F

STREAM_PATH = "data/streaming/input"
SILVER_PATH = "data/silver/car_data_2024"
CHECKPOINT_PATH = "data/streaming/checkpoints/telemetry"
METRICS_PATH = "data/streaming/metrics"

Path(STREAM_PATH).mkdir(parents=True, exist_ok=True)
Path(METRICS_PATH).mkdir(parents=True, exist_ok=True)

spark = (
    SparkSession.builder
    .appName("F1-Telemetry-Streaming")
    .master("local[2]")
    .config("spark.sql.session.timeZone", "UTC")
    .config("spark.sql.shuffle.partitions", "16")
    .getOrCreate()
)

spark.sparkContext.setLogLevel("ERROR")

query = None

try:
    print("\n=== F1 RACE INTELLIGENCE ===")
    print("SPARK STRUCTURED STREAMING\n")

    # Recupero lo schema dal Silver 2024.
    # Il Silver è partizionato per session_key.
    schema = spark.read.parquet(SILVER_PATH).schema

    stream = (
        spark.readStream
        .schema(schema)
        .option("recursiveFileLookup", "true")
        .option("maxFilesPerTrigger", 1)
        .parquet(STREAM_PATH)
    )

    def process_batch(batch_df, batch_id):
        if batch_df.isEmpty():
            return

        print(f"\n=== MICRO-BATCH {batch_id} ===")

        metrics = (
            batch_df
            .groupBy("session_key", "driver_number")
            .agg(
                F.count("*").alias("events"),
                F.round(
                    F.avg("speed"), 2
                ).alias("avg_speed"),
                F.max("speed").alias("max_speed"),
                F.round(
                    F.avg("rpm"), 2
                ).alias("avg_rpm")
            )
            .withColumn(
                "batch_id",
                F.lit(batch_id)
            )
        )

        output = (
            f"{METRICS_PATH}/batch_{batch_id:04d}"
        )

        (
            metrics.write
            .mode("overwrite")
            .parquet(output)
        )

        metrics.show(truncate=False)

    query = (
        stream.writeStream
        .foreachBatch(process_batch)
        .option(
            "checkpointLocation",
            CHECKPOINT_PATH
        )
        .trigger(processingTime="3 seconds")
        .start()
    )

    print("Streaming avviato.")
    print("In attesa di nuovi file Parquet...")
    print("Premi Ctrl+C per interrompere.\n")

    query.awaitTermination()

except KeyboardInterrupt:
    print("\nStreaming interrotto dall'utente.")

finally:
    if query is not None and query.isActive:
        query.stop()

    spark.stop()