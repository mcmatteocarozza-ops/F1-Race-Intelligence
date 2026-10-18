from pyspark.sql import SparkSession
from pyspark.sql.functions import (
    col,
    countDistinct,
    sum as spark_sum,
    when
)

# Avvio di Apache Spark
spark = (
    SparkSession.builder
    .appName("F1-Race-Intelligence")
    .master("local[2]")
    .getOrCreate()
)

spark.sparkContext.setLogLevel("ERROR")

try:
    print("\n=== F1 RACE INTELLIGENCE ===")
    print("DATASET INSPECTION - SEASON 2024\n")

    # Lettura dei file JSON
    df = (
        spark.read
        .option("multiLine", "true")
        .json("data/bronze/laps/*.json")
    )

    # Mostra la struttura dei dati
    print("\n=== SCHEMA ===")
    df.printSchema()

    # Statistiche generali
    print("\n=== DATASET STATISTICS ===")

    print("Total records:", df.count())

    df.select(
        countDistinct("session_key").alias("races"),
        countDistinct("driver_number").alias("drivers")
    ).show()

    # Verifica qualità delle durate
    print("\n=== LAP DURATION QUALITY ===")

    df.select(
        spark_sum(
            when(col("lap_duration") > 0, 1).otherwise(0)
        ).alias("valid_laps"),
        spark_sum(
            when(
                col("lap_duration").isNull()
                | (col("lap_duration") <= 0),
                1
            ).otherwise(0)
        ).alias("invalid_laps")
    ).show()

    # Visualizzazione di un campione
    print("\n=== SAMPLE RECORDS ===")

    df.select(
        "session_key",
        "driver_number",
        "lap_number",
        "lap_duration"
    ).show(10, truncate=False)

    # Mantengo attiva la Spark Web UI
    print("\nSpark Web UI: http://localhost:4040")
    input("Premi INVIO per terminare Spark...")

finally:
    spark.stop()
    print("Spark terminato.")

    