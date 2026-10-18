from pyspark.sql import SparkSession
from pyspark.sql import functions as F
from pyspark.sql.window import Window

spark = (
    SparkSession.builder
    .appName("F1-Lap-Evolution")
    .master("local[2]")
    .getOrCreate()
)

spark.sparkContext.setLogLevel("ERROR")

try:
    print("\n=== F1 RACE INTELLIGENCE ===")
    print("LAP EVOLUTION - MONZA 2024\n")

    laps = spark.read.parquet("data/silver/laps")

    monza = laps.filter(
        (F.col("session_key") == 9590)
        & (F.col("valid_lap") == True)
    )

    # Finestra sui giri di ogni pilota
    driver_window = (
        Window
        .partitionBy("session_key", "driver_number")
        .orderBy("lap_number")
    )

    # Calcolo del tempo del giro precedente
    evolution = (
        monza
        .withColumn(
            "previous_lap_seconds",
            F.lag("lap_duration").over(driver_window)
        )
        .withColumn(
            "delta_previous_seconds",
            F.round(
                F.col("lap_duration")
                - F.col("previous_lap_seconds"),
                3
            )
        )
    )

    print("=== EVOLUZIONE PILOTA N. 4 ===")

    (
        evolution
        .filter(F.col("driver_number") == 4)
        .select(
            "lap_number",
            "lap_duration",
            "previous_lap_seconds",
            "delta_previous_seconds"
        )
        .orderBy("lap_number")
        .show(20, truncate=False)
    )

    print("\n=== STATISTICHE VARIAZIONE TEMPI ===")

    (
        evolution
        .filter(F.col("delta_previous_seconds").isNotNull())
        .groupBy("driver_number")
        .agg(
            F.round(
                F.avg(F.abs("delta_previous_seconds")), 3
            ).alias("avg_absolute_lap_change")
        )
        .orderBy("avg_absolute_lap_change")
        .show(20, truncate=False)
    )

finally:
    spark.stop()