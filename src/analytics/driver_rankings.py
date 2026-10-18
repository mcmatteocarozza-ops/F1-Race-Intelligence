from pyspark.sql import SparkSession

spark = (
    SparkSession.builder
    .appName("F1-Driver-Rankings")
    .master("local[2]")
    .getOrCreate()
)

spark.sparkContext.setLogLevel("ERROR")

try:
    gold = spark.read.parquet(
        "data/gold/driver_race_performance"
    )

    gold.createOrReplaceTempView("driver_performance")

    print("\n=== F1 RACE INTELLIGENCE ===")
    print("SPARK SQL - WINDOW FUNCTIONS\n")

    rankings = spark.sql("""
        SELECT
            circuit,
            driver_number,
            valid_laps,
            fastest_lap_seconds,
            avg_lap_seconds,

            ROW_NUMBER() OVER (
                PARTITION BY session_key
                ORDER BY fastest_lap_seconds ASC,
                         driver_number ASC
            ) AS fastest_lap_rank,

            ROUND(
                fastest_lap_seconds
                - MIN(fastest_lap_seconds) OVER (
                    PARTITION BY session_key
                ),
                3
            ) AS gap_to_fastest_seconds

        FROM driver_performance
    """)

    print("=== MONZA 2024 - CLASSIFICA GIRI VELOCI ===")

    (
        rankings
        .filter(rankings.circuit == "Monza")
        .orderBy("fastest_lap_rank")
        .show(20, truncate=False)
    )

finally:
    spark.stop()