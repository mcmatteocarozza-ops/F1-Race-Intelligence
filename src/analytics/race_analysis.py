from pyspark.sql import SparkSession

spark = (
    SparkSession.builder
    .appName("F1-Race-Intelligence-Analytics")
    .master("local[2]")
    .getOrCreate()
)

spark.sparkContext.setLogLevel("ERROR")

try:
    print("\n=== F1 RACE INTELLIGENCE ===")
    print("SPARK SQL - ANALISI STAGIONE 2024\n")

    # Lettura del livello Silver
    laps = spark.read.parquet("data/silver/laps")

    # Lettura dei metadati delle gare
    races = (
        spark.read
        .option("multiLine", "true")
        .json("data/bronze/races_2024.json")
    )

    
    laps.createOrReplaceTempView("laps")
    races.createOrReplaceTempView("races")

    
    enriched = spark.sql("""
        SELECT
            l.session_key,
            r.circuit,
            r.country,
            r.date AS race_date,
            l.driver_number,
            l.lap_number,
            l.lap_duration,
            l.valid_lap
        FROM laps l
        INNER JOIN races r
            ON l.session_key = r.session_key
    """)

    enriched.createOrReplaceTempView("enriched_laps")

    print("=== VERIFICA JOIN ===")
    print("Giri Silver:", laps.count())
    print("Giri collegati ai circuiti:", enriched.count())

    print("\n=== TEMPI MEDI PER CIRCUITO ===")

    spark.sql("""
        SELECT
            circuit,
            country,
            COUNT(*) AS valid_laps,
            ROUND(AVG(lap_duration), 3) AS avg_lap_seconds,
            ROUND(MIN(lap_duration), 3) AS fastest_lap_seconds
        FROM enriched_laps
        WHERE valid_lap = TRUE
        GROUP BY circuit, country
        ORDER BY avg_lap_seconds ASC
    """).show(24, truncate=False)

    print("\n=== GIRI PIU VELOCI A MONZA ===")

    spark.sql("""
        SELECT
            circuit,
            driver_number,
            lap_number,
            ROUND(lap_duration, 3) AS lap_seconds
        FROM enriched_laps
        WHERE circuit = 'Monza'
          AND valid_lap = TRUE
        ORDER BY lap_duration ASC
        LIMIT 10
    """).show(truncate=False)

finally:
    spark.stop()