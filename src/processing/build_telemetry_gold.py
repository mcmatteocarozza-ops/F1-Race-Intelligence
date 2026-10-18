from pyspark.sql import SparkSession
from pyspark.sql import functions as F

SILVER_PATH = "data/silver/car_data_2024"
GOLD_PATH = "data/gold/telemetry_performance_2024_v2"

spark = (
    SparkSession.builder
    .appName("F1-Telemetry-Gold-2024")
    .master("local[2]")
    .config("spark.sql.session.timeZone", "UTC")
    .config("spark.sql.shuffle.partitions", "16")
    .getOrCreate()
)

spark.sparkContext.setLogLevel("ERROR")

try:
    print("\n=== F1 RACE INTELLIGENCE ===")
    print("BUILD TELEMETRY GOLD 2024\n")

    silver = spark.read.parquet(SILVER_PATH)

    gold = (
        silver
        .groupBy("session_key", "driver_number")
        .agg(
            F.count("*").alias("total_events"),
            F.round(F.avg("speed"), 2).alias("avg_speed_kmh"),
            F.max("speed").alias("max_speed_kmh"),
            F.round(F.avg("rpm"), 2).alias("avg_rpm"),
            F.max("rpm").alias("max_rpm"),
            
            F.round(
                F.avg(
                    F.when(
                        F.col("throttle").between(0, 100),
                        (F.col("throttle") > 0).cast("double")
                    )
                ) * 100,
                2
            ).alias("accelerating_samples_pct"),

            F.round(
                F.avg(
                    F.when(
                        F.col("brake").isin(0, 100),
                        (F.col("brake") == 100).cast("double")
                    )
                ) * 100,
                2
            ).alias("braking_samples_pct"),
        )
    )

    print("Scrittura Gold Parquet in corso...")

    gold.write.mode("errorifexists").parquet(GOLD_PATH)

    print("\nDataset salvato in:", GOLD_PATH)
    print("BUILD TELEMETRY GOLD COMPLETATO")

finally:
    spark.stop()