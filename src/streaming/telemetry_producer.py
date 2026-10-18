import time
from pathlib import Path

from pyspark.sql import SparkSession
from pyspark.sql import functions as F
from pyspark.sql.window import Window

SILVER_PATH = "data/silver/car_data_2024"
STREAM_PATH = Path("data/streaming/input")

# Gran Premio Italia 2024 - Lando Norris
SESSION_KEY = 9590
DRIVER_NUMBER = 4

MAX_EVENTS = 10000
BATCH_SIZE = 500
DELAY_SECONDS = 3

spark = (
    SparkSession.builder
    .appName("F1-Telemetry-Producer")
    .master("local[2]")
    .config("spark.sql.shuffle.partitions", "16")
    .getOrCreate()
)

spark.sparkContext.setLogLevel("ERROR")

try:
    print("\n=== F1 RACE INTELLIGENCE ===")
    print("TELEMETRY STREAMING PRODUCER\n")

    # Leggiamo soltanto la sessione e il pilota
    telemetry = (
        spark.read.parquet(SILVER_PATH)
        .filter(
            (F.col("session_key") == SESSION_KEY)
            & (F.col("driver_number") == DRIVER_NUMBER)
        )
        .orderBy("event_time")
        .limit(MAX_EVENTS)
    )

    # Numerare cronologicamente gli eventi selezionati
    window = Window.orderBy("event_time")

    numbered = telemetry.withColumn(
        "row_id",
        F.row_number().over(window)
    )

    # Assegnazione gli eventi ai micro-batch simulati
    batches = (
        numbered
        .withColumn(
            "batch_id",
            F.floor(
                (F.col("row_id") - 1) / BATCH_SIZE
            )
        )
        .drop("row_id")
        .cache()
    )

    total_events = batches.count()
    total_batches = (
        total_events + BATCH_SIZE - 1
    ) // BATCH_SIZE

    print(f"Sessione: {SESSION_KEY}")
    print(f"Pilota: #{DRIVER_NUMBER}")
    print(f"Eventi da riprodurre: {total_events}")
    print(f"Eventi per gruppo: {BATCH_SIZE}")
    print(f"Gruppi da pubblicare: {total_batches}")
    print(f"Intervallo: {DELAY_SECONDS} secondi\n")

    if total_events == 0:
        raise ValueError(
            "Nessun evento trovato per sessione e pilota."
        )

    STREAM_PATH.mkdir(
        parents=True,
        exist_ok=True
    )

    # Evitiamo di mescolare il nuovo replay con file rimasti da esecuzioni precedenti
    existing = list(STREAM_PATH.iterdir())

    if existing:
        raise RuntimeError(
            "La cartella streaming/input non è vuota. "
            "Non elimino automaticamente i dati precedenti."
        )

    # Pubblicazione progressiva dei file Parquet
    for batch_id in range(total_batches):
        batch = (
            batches
            .filter(F.col("batch_id") == batch_id)
            .drop("batch_id")
        )

        output = STREAM_PATH / f"batch_{batch_id:04d}"

        (
            batch
            .coalesce(1)
            .write.mode("errorifexists")
            .parquet(str(output))
        )

        print(
            f"Pubblicato gruppo {batch_id + 1}"
            f"/{total_batches}"
        )

        time.sleep(DELAY_SECONDS)

    print("\nREPLAY COMPLETATO")

finally:
    spark.stop()