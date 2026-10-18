from pyspark.sql import SparkSession
from pyspark.sql import functions as F

SILVER_PATH = "data/silver/car_data_2024"

spark = (
    SparkSession.builder
    .appName("F1-Telemetry-Data-Quality")
    .master("local[2]")
    .config("spark.sql.shuffle.partitions", "16")
    .getOrCreate()
)

spark.sparkContext.setLogLevel("ERROR")

try:
    print("\n=== F1 TELEMETRY DATA QUALITY ===\n")

    df = spark.read.parquet(SILVER_PATH)

    # Statistiche e valori nulli 
    stats = df.agg(
        F.count("*").alias("total_events"),
        F.countDistinct("session_key").alias("sessions"),
        F.sum(F.col("speed").isNull().cast("long")).alias("null_speed"),
        F.sum(F.col("rpm").isNull().cast("long")).alias("null_rpm"),
        F.sum(F.col("throttle").isNull().cast("long")).alias("null_throttle"),
        F.sum(F.col("brake").isNull().cast("long")).alias("null_brake"),
        F.sum(F.col("drs").isNull().cast("long")).alias("null_drs"),
        F.sum(
            ((F.col("speed") < 0) | (F.col("speed") > 400))
            .cast("long")
        ).alias("speed_out_of_range"),
        F.sum(
            ((F.col("rpm") < 0) | (F.col("rpm") > 20000))
            .cast("long")
        ).alias("rpm_out_of_range"),
        F.sum(
            ((F.col("throttle") < 0) | (F.col("throttle") > 100))
            .cast("long")
        ).alias("throttle_out_of_range"),
        F.sum(
            (~F.col("brake").isin(0, 100)).cast("long")
        ).alias("brake_unexpected")
    ).first()

    for name, value in stats.asDict().items():
        print(f"{name}: {value:,}")

    # Duplicati 
    print("\nChecking duplicate event keys...")

    duplicate_groups = (
        df.groupBy(
            "session_key",
            "driver_number",
            "event_time"
        )
        .count()
        .filter(F.col("count") > 1)
    )

    duplicates = duplicate_groups.agg(
        F.coalesce(
            F.sum(F.col("count") - 1),
            F.lit(0)
        ).alias("duplicate_events")
    ).first()["duplicate_events"]

    print(f"Duplicate event keys (extra rows): {duplicates:,}")

    print("\nDATA QUALITY CHECK COMPLETED")

finally:
    spark.stop()