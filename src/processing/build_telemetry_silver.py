from pyspark.sql import SparkSession
from pyspark.sql import functions as F
from pyspark.sql.types import (
    StructType, StructField, LongType, StringType
)

BRONZE_PATH = "data/bronze/car_data/*.json"

# Scrivo inizialmente in una nuova cartella.
# Il precedente Silver rimane intatto.
SILVER_PATH = "data/silver/car_data_2024"

spark = (
    SparkSession.builder
    .appName("F1-Telemetry-Silver-2024")
    .master("local[2]")
    .config("spark.sql.session.timeZone", "UTC")
    .config("spark.sql.shuffle.partitions", "16")
    .config("spark.driver.memory", "3g")
    .config("spark.sql.files.maxPartitionBytes", "64m")
    .getOrCreate()
)

spark.sparkContext.setLogLevel("ERROR")

schema = StructType([
    StructField("date", StringType(), True),
    StructField("session_key", LongType(), True),
    StructField("meeting_key", LongType(), True),
    StructField("driver_number", LongType(), True),
    StructField("rpm", LongType(), True),
    StructField("n_gear", LongType(), True),
    StructField("drs", LongType(), True),
    StructField("throttle", LongType(), True),
    StructField("speed", LongType(), True),
    StructField("brake", LongType(), True),
])

try:
    print("\n=== F1 RACE INTELLIGENCE ===")
    print("BUILD TELEMETRY SILVER 2024\n")

    # Lettura Bronze con schema esplicito
    bronze = (
        spark.read
        .schema(schema)
        .option("multiLine", "true")
        .json(BRONZE_PATH)
    )

    # Conversione timestamp
    telemetry = bronze.withColumn(
        "event_time",
        F.to_timestamp("date")
    )

    # Validazione dei campi essenziali
    telemetry = telemetry.filter(
        F.col("session_key").isNotNull()
        & F.col("driver_number").isNotNull()
        & F.col("event_time").isNotNull()
    )

    # Indicatori
    telemetry = (
        telemetry
        .withColumn(
            "is_braking",
            F.when(F.col("brake").isNotNull(), F.col("brake") > 0)
        )
        .withColumn(
            "is_accelerating",
            F.when(
                F.col("throttle").isNotNull(),
                F.col("throttle") > 0
            )
        )
    )

    # Salvataggio Parquet partizionato per sessione
    print("Scrittura Silver Parquet in corso...")

    (
        telemetry.write
        .mode("errorifexists")
        .partitionBy("session_key")
        .parquet(SILVER_PATH)
    )

    print("\nDataset salvato in:", SILVER_PATH)
    print("BUILD TELEMETRY SILVER COMPLETATO")

finally:
    spark.stop()
