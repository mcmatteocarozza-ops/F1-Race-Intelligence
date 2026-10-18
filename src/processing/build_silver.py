from pyspark.sql import SparkSession
from pyspark.sql import functions as F

# Percorsi
BRONZE_PATH = "data/bronze/laps/*.json"
SILVER_PATH = "data/silver/laps"

# Avvio Spark
spark = (
    SparkSession.builder
    .appName("F1-Race-Intelligence-Bronze-to-Silver")
    .master("local[2]")
    .getOrCreate()
)

spark.sparkContext.setLogLevel("ERROR")

print("\n=== F1 RACE INTELLIGENCE ===")
print("BRONZE -> SILVER\n")

try:
    # 1. Lettura dei JSON originali
    bronze = (
        spark.read
        .option("multiLine", "true")
        .json(BRONZE_PATH)
    )

    print("Record Bronze:", bronze.count())

    # 2. Normalizzazione e validazione
    silver = (
        bronze
        .withColumn(
            "lap_start_timestamp",
            F.to_timestamp("date_start")
        )
        .withColumn(
            "valid_lap",
            F.col("lap_duration").isNotNull()
            & (F.col("lap_duration") > 0)
        )
        .withColumn(
            "valid_identifiers",
            F.col("session_key").isNotNull()
            & F.col("driver_number").isNotNull()
            & F.col("lap_number").isNotNull()
            & (F.col("lap_number") > 0)
        )
        .withColumn(
            "lap_duration_ms",
            F.when(
                F.col("valid_lap"),
                F.round(F.col("lap_duration") * 1000).cast("long")
            )
        )
        .withColumn(
            "sector_total_seconds",
            F.col("duration_sector_1")
            + F.col("duration_sector_2")
            + F.col("duration_sector_3")
        )
    )

    # Eliminazione di eventuali duplicati
    silver = silver.dropDuplicates(
        ["session_key", "driver_number", "lap_number"]
    )

    # Verifica dei risultati
    print("\n=== SILVER QUALITY ===")

    silver.agg(
        F.count("*").alias("total_records"),
        F.sum(F.col("valid_lap").cast("int")).alias("valid_laps"),
        F.sum((~F.col("valid_lap")).cast("int")).alias("invalid_laps"),
        F.sum((~F.col("valid_identifiers")).cast("int")).alias(
            "invalid_identifiers"
        )
    ).show()

    # Salvataggio in formato Parquet
    (
        silver.write
        .mode("overwrite")
        .parquet(SILVER_PATH)
    )

    print("\nDataset Silver salvato in:", SILVER_PATH)
    print("BRONZE -> SILVER COMPLETATO")

finally:
    spark.stop()


