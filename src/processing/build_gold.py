from pyspark.sql import SparkSession
from pyspark.sql import functions as F

SILVER_PATH = "data/silver/laps"
RACES_PATH = "data/bronze/races_2024.json"
GOLD_PATH = "data/gold/driver_race_performance"

spark = (
    SparkSession.builder
    .appName("F1-Race-Intelligence-Gold")
    .master("local[2]")
    .getOrCreate()
)

spark.sparkContext.setLogLevel("ERROR")

try:
    print("\n=== F1 RACE INTELLIGENCE ===")
    print("BUILD GOLD - DRIVER RACE PERFORMANCE\n")

    laps = spark.read.parquet(SILVER_PATH)

    races = (
        spark.read
        .option("multiLine", "true")
        .json(RACES_PATH)
    )

    if races.count() != races.select("session_key").distinct().count():
        raise ValueError("Sessioni duplicate nei metadati")

    enriched = laps.join(
        races.select("session_key", "circuit", "country"),
        on="session_key",
        how="inner"
    )

    if enriched.count() != laps.count():
        raise ValueError("JOIN non valido")

    valid_laps = enriched.filter(
        (F.col("valid_lap") == True)
        & (F.col("valid_identifiers") == True)
    )

    gold = (
        valid_laps
        .groupBy(
            "session_key",
            "circuit",
            "country",
            "driver_number"
        )
        .agg(
            F.count("*").alias("valid_laps"),
            F.round(F.min("lap_duration"), 3).alias("fastest_lap_seconds"),
            F.round(F.avg("lap_duration"), 3).alias("avg_lap_seconds"),
            F.round(F.stddev_samp("lap_duration"), 3).alias("lap_stddev_seconds")
        )
    )

    
    # 6. Lettura anagrafiche piloti
    drivers = (
        spark.read
        .option("multiLine", "true")
        .json("data/bronze/drivers_2024.json")
    )

    # informazioni necessarie
    driver_info = drivers.select(
        "session_key",
        "driver_number",
        "full_name",
        "team_name"
    ).dropDuplicates([
        "session_key",
        "driver_number"
    ])

    # Arricchimento del dataset Gold
    gold_enriched = gold.join(
        driver_info,
        on=["session_key", "driver_number"],
        how="left"
    )

    # Controlli di qualità
    if gold_enriched.count() != gold.count():
        raise ValueError(
            "JOIN piloti non valido: numero di record modificato"
        )

    missing_names = gold_enriched.filter(
        F.col("full_name").isNull()
    ).count()

    print("Piloti senza anagrafica:", missing_names)

    # Salvataggio del dataset Gold arricchito
    gold_enriched.write.mode("overwrite").parquet(GOLD_PATH)

    # Da qui in poi uso il dataset arricchito
    gold = gold_enriched


    print("=== GOLD STATISTICS ===")
    print("Record Gold:", gold.count())
    print("Gran Premi:", gold.select("session_key").distinct().count())

    print("\n=== MONZA 2024 ===")

    (
        gold.filter(F.col("circuit") == "Monza")
        .orderBy("fastest_lap_seconds")
        .show(25, truncate=False)
    )

    print("\nDataset Gold salvato in:", GOLD_PATH)
    print("BUILD GOLD COMPLETATO")

finally:
    spark.stop()
