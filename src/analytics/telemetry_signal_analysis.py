from pyspark.sql import SparkSession
from pyspark.sql import functions as F

SILVER_PATH = "data/silver/car_data_2024"

spark = (
    SparkSession.builder
    .appName("F1-Telemetry-Signal-Analysis")
    .master("local[2]")
    .config("spark.sql.shuffle.partitions", "16")
    .getOrCreate()
)

spark.sparkContext.setLogLevel("ERROR")

try:
    print("\n=== TELEMETRY SIGNAL ANALYSIS ===\n")

    telemetry = spark.read.parquet(SILVER_PATH)

    analysis = (
        telemetry
        .groupBy("session_key")
        .agg(
            F.count("*").alias("total_events"),
            F.sum(
                (F.col("throttle") == 104).cast("long")
            ).alias("throttle_104"),
            F.sum(
                (F.col("brake") == 104).cast("long")
            ).alias("brake_104"),
            F.sum(
                (
                    (F.col("throttle") == 104)
                    & (F.col("brake") == 104)
                ).cast("long")
            ).alias("both_104")
        )
        .withColumn(
            "both_104_pct",
            F.round(
                F.col("both_104") * 100
                / F.col("total_events"),
                2
            )
        )
        .orderBy("session_key")
    )

    analysis.show(30, truncate=False)

    affected_sessions = analysis.filter(
        F.col("both_104") > 0
    ).count()

    print(
        f"\nSessions with simultaneous 104 values: "
        f"{affected_sessions}"
    )

    print("\nSIGNAL ANALYSIS COMPLETED")

finally:
    spark.stop()
