from pyspark.sql import SparkSession
from pyspark.sql import functions as F

SILVER_PATH = "data/silver/car_data"
METRICS_PATH = "data/streaming/metrics"

spark = (
    SparkSession.builder
    .appName("F1-Streaming-Verification")
    .master("local[2]")
    .getOrCreate()
)

spark.sparkContext.setLogLevel("ERROR")

try:
    print("\n=== F1 RACE INTELLIGENCE ===")
    print("STREAMING VERIFICATION\n")

    silver = spark.read.parquet(SILVER_PATH)
    metrics = (
    spark.read
    .option("recursiveFileLookup", "true")
    .parquet(METRICS_PATH)
    )

    original_events = silver.count()

    processed_events = (
        metrics
        .agg(F.sum("events").alias("total"))
        .first()["total"]
    )

    batch_count = metrics.select(
        "batch_id"
    ).distinct().count()

    duplicate_batch_ids = (
        metrics
        .groupBy("batch_id", "session_key", "driver_number")
        .count()
        .filter(F.col("count") > 1)
        .count()
    )

    print("Eventi originali:", original_events)
    print("Eventi elaborati:", processed_events)
    print("Micro-batch registrati:", batch_count)
    print("Metriche duplicate:", duplicate_batch_ids)

    difference = original_events - processed_events

    print("Differenza:", difference)

    if difference == 0 and duplicate_batch_ids == 0:
        print("\nVERIFICA CONTEGGI SUPERATA")
    else:
        print("\nATTENZIONE: verificare i risultati")

finally:
    spark.stop()