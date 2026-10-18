# F1 Race Intelligence

**Analisi Big Data delle prestazioni e della telemetria di Formula 1**  
Progetto universitario per il corso *Algoritmi e Strutture Dati per i Big Data*.

## Panoramica

F1 Race Intelligence è un progetto Python che acquisisce dati della stagione 2024 di Formula 1 tramite le API [OpenF1](https://openf1.org/), li elabora con **Apache Spark / PySpark** e li presenta in una dashboard interattiva sviluppata con **Streamlit** e **Plotly**.

Il progetto comprende una pipeline batch organizzata in livelli **Bronze → Silver → Gold**, controlli di qualità sui dati e una simulazione di streaming realizzata con **Spark Structured Streaming**.

L'applicazione viene eseguita **in locale**: non è necessario alcun servizio di hosting a pagamento.

## Dati e risultati

| Indicatore | Valore |
| --- | ---: |
| Gran Premi della stagione 2024 analizzati | 24 |
| Record dei giri | 26.629 |
| Eventi telemetrici analizzati | 16.550.374 |
| Dimensione indicativa della telemetria JSON | 2,9 GB |
| Record Gold `driver_race_performance` | 465 |
| Record Gold `telemetry_performance_2024_v2` | 479 |

I dati provengono da OpenF1. I risultati sono riferiti all'elaborazione descritta nella relazione del progetto.

## Architettura

```text
OpenF1 API
    |
    v
Bronze (JSON originali)
    |
    v
Silver (Parquet, dati strutturati)
    |
    v
Gold (metriche aggregate)
    |
    v
Dashboard Streamlit / Plotly
```

Le trasformazioni batch vengono eseguite con Spark all'interno di un container Docker. La dashboard Streamlit viene avviata separatamente tramite Python locale e legge i dataset predisposti dal progetto.

La simulazione streaming segue un percorso distinto:

```text
Eventi storici -> Producer -> Batch Parquet -> Spark Structured Streaming
                                                |
                                                v
                                         Metriche elaborate
                                                |
                                                v
                                        Live Streaming Monitor
```

La simulazione utilizza **10.000 eventi storici** di Monza 2024, relativi a Lando Norris, pubblicati in **20 batch da 500 eventi** a intervalli di circa **3 secondi**. Non si tratta di una connessione live con le vetture.

## Tecnologie

- **Python** — acquisizione, elaborazioni ausiliarie e interfaccia.
- **Apache Spark 4.0.1 / PySpark** — elaborazioni batch e Structured Streaming nel container Docker.
- **Parquet** — archiviazione dei dati elaborati.
- **Docker Compose** — configurazione dell'ambiente Spark.
- **Streamlit e Plotly** — dashboard e grafici interattivi.
- **OpenF1 API** — sorgente dei dati.

> **Nota sulle versioni:** l'immagine Docker usa Spark 4.0.1. L'ambiente Python locale di sviluppo includeva anche PySpark 4.2.0; per riprodurre le elaborazioni descritte qui è consigliato usare il container, senza mescolare le due installazioni.

## Struttura del repository

```text
F1-Race-Intelligence/
├── src/
│   ├── ingestion/         # Acquisizione dei dati OpenF1
│   ├── processing/        # Trasformazioni Silver e Gold
│   ├── analytics/         # Analisi delle prestazioni e della telemetria
│   ├── quality/           # Controlli sui dati
│   ├── streaming/         # Producer, consumer e verifiche streaming
│   └── dashboard/         # Applicazione Streamlit
├── data/                  # Dataset locali (non necessariamente distribuiti)
├── docker-compose.yml
├── Dockerfile.spark
├── requirements.txt
└── README.md
```

La struttura rappresenta i principali file e directory del progetto. Dataset voluminosi, cache, checkpoint e ambiente virtuale non devono essere inclusi nel repository Git.

## Requisiti

- **Git** per clonare il repository.
- **Docker Desktop** con Docker Compose per eseguire Spark.
- **Python** e `pip` per avviare la dashboard in locale.
- Un browser web.
- Spazio su disco adeguato se si desidera ricostruire i dataset completi.

Lo sviluppo è stato effettuato su Windows 11. I comandi seguenti usano PowerShell; Docker Compose può essere utilizzato anche su altri sistemi compatibili.

## Installazione

### 1. Scaricare il progetto

```powershell
git clone <URL_DEL_REPOSITORY>
cd F1-Race-Intelligence
```

Sostituire il segnaposto con l'URL effettivo del repository GitHub.

### 2. Avviare Apache Spark con Docker

Dalla directory principale:

```powershell
docker compose up -d --build
```

Verificare la versione di Spark:

```powershell
docker exec f1-spark spark-submit --version
```

Il progetto viene montato nel container nel percorso `/app`. La porta `4040` è esposta per l'interfaccia Spark UI, quando è attiva un'applicazione Spark.

### 3. Preparare l'ambiente Python della dashboard

Su Windows, dalla directory principale:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

### 4. Avviare la dashboard

```powershell
.\.venv\Scripts\python.exe -m streamlit run src\dashboard\app.py
```

Aprire nel browser l'indirizzo normalmente indicato da Streamlit, in genere **http://localhost:8501**.

**Importante:** per mostrare le analisi, la dashboard deve poter accedere ai dataset Gold richiesti dal codice. Se i dati non sono presenti, l'installazione delle dipendenze da sola non è sufficiente. Consultare la sezione successiva.

## Ricostruzione completa dei dataset

I dataset voluminosi non sono distribuiti nel repository. È possibile ricostruirli a partire dalle API OpenF1 eseguendo gli script nella sequenza seguente. **Tutti i comandi devono essere lanciati dalla directory principale del progetto**, dopo aver avviato Docker e installato le dipendenze Python come descritto sopra.

### 1. Acquisizione dei dati Bronze

Gli script di acquisizione utilizzano Python locale. Su Windows PowerShell:

```powershell
.\.venv\Scripts\python.exe src/ingestion/discover_sessions.py
.\.venv\Scripts\python.exe src/ingestion/download_drivers.py
.\.venv\Scripts\python.exe src/ingestion/download_season.py
.\.venv\Scripts\python.exe src/ingestion/download_season_telemetry.py
```

La sequenza crea il catalogo `data/bronze/races_2024.json`, le anagrafiche `data/bronze/drivers_2024.json`, i JSON dei giri in `data/bronze/laps/` e i JSON telemetrici in `data/bronze/car_data/`.

`download_car_data.py` è uno script separato per una singola combinazione sessione-pilota; `test_car_data.py` serve a verificare una richiesta all'API e non è necessario per la ricostruzione della stagione.

Il download completo della telemetria può richiedere molto tempo e dipende dalla disponibilità e dai limiti delle API OpenF1. Il downloader telemetrico evita di riscaricare i file JSON già presenti e validi e gestisce tentativi successivi in caso di errori temporanei.

### 2. Elaborazione Silver con Apache Spark

```powershell
docker exec -it f1-spark spark-submit /app/src/processing/build_silver.py
docker exec -it f1-spark spark-submit /app/src/processing/build_telemetry_silver.py
```

Questi passaggi producono rispettivamente `data/silver/laps` e `data/silver/car_data_2024` in formato Parquet. Il secondo dataset è partizionato per `session_key`.

### 3. Elaborazione Gold con Apache Spark

```powershell
docker exec -it f1-spark spark-submit /app/src/processing/build_gold.py
docker exec -it f1-spark spark-submit /app/src/processing/build_telemetry_gold.py
```

I risultati vengono salvati in `data/gold/driver_race_performance` e `data/gold/telemetry_performance_2024_v2`.

**Attenzione alle riesecuzioni:** gli script `build_telemetry_silver.py` e `build_telemetry_gold.py` usano la modalità di scrittura `errorifexists`: se le rispettive directory di destinazione esistono già, Spark interrompe la scrittura. Prima di ripeterli occorre gestire i risultati precedenti (per esempio spostando le directory), evitando di cancellare dati che si desidera conservare. Gli script Silver e Gold dei giri usano invece `overwrite`.

### 4. Avvio della dashboard

Una volta generati i dataset Gold:

```powershell
.\.venv\Scripts\python.exe -m streamlit run src/dashboard/app.py
```

La dashboard è disponibile normalmente all'indirizzo `http://localhost:8501`, senza pubblicazione su un server esterno. Le sezioni Race Analytics, Season Analytics e Driver Comparison usano il Gold dei giri. Telemetry Analytics richiede anche `data/gold/telemetry_performance_2024_v2`, `data/bronze/drivers_2024.json` e i JSON in `data/bronze/car_data/`. Il Live Streaming Monitor legge `data/streaming/metrics`. **Nota:** `app.py` carica il Gold dei giri all’avvio, quindi è richiesto anche per accedere alla vista streaming.

> **Verifica di riproducibilità ancora necessaria:** eseguire la procedura da una copia pulita del repository e controllare che i dati acquisiti dalle API, le dipendenze e i percorsi siano compatibili con gli script e con tutte le viste della dashboard.

## Esempio di analisi Spark

Dopo aver avviato il container e predisposto i dataset necessari:

```powershell
docker exec -it f1-spark spark-submit /app/src/analytics/telemetry_signal_analysis.py
```

Questo script esamina i segnali telemetrici. Nell'analisi della stagione 2024 è stato osservato il valore `104` nei campi acceleratore e freno, al di fuori degli intervalli utilizzati per le relative percentuali. Il suo significato originario non è stato determinato con certezza; il progetto lo esclude dai calcoli delle percentuali di utilizzo considerate.

## Simulazione streaming

La simulazione riproduce fino a **10.000 eventi telemetrici storici** del Gran Premio d’Italia 2024 (sessione `9590`, pilota numero `4`, Lando Norris). Il producer pubblica file Parquet da **500 eventi** ciascuno, intervallati da una pausa di **3 secondi**. Il consumer usa **Spark Structured Streaming** per elaborarli e scrivere metriche per micro-batch, lette dalla dashboard con aggiornamento ogni 3 secondi. Non si tratta di telemetria live acquisita dalla pista.

**Prerequisiti:** container `f1-spark` avviato, dataset Silver `data/silver/car_data_2024` già generato e directory `data/streaming/input` vuota per una nuova simulazione. È consigliabile completare prima la pipeline dei giri, perché `app.py` richiede il relativo dataset Gold anche quando si apre il Live Streaming Monitor.

Aprire **tre terminali** dalla directory principale del progetto:

**Terminale 1 — Consumer** (lasciarlo in esecuzione):

```powershell
docker exec -it f1-spark spark-submit /app/src/streaming/telemetry_consumer.py
```

**Terminale 2 — Producer** (avviarlo dopo il consumer):

```powershell
docker exec -it f1-spark spark-submit /app/src/streaming/telemetry_producer.py
```

**Terminale 3 — Dashboard**:

```powershell
.\.venv\Scripts\python.exe -m streamlit run src/dashboard/app.py
```

Aprire `http://localhost:8501` e selezionare **Live Streaming Monitor**. Le metriche sono scritte in `data/streaming/metrics/batch_XXXX` e vengono mostrate man mano che i micro-batch sono elaborati.

### Ripetere la simulazione dall'inizio

Il producer **rifiuta di avviarsi se `data/streaming/input` non è vuota**. Inoltre, il consumer memorizza l'avanzamento in `data/streaming/checkpoints/telemetry`: riutilizzare il checkpoint non equivale a iniziare una nuova simulazione.

Per un nuovo replay indipendente:

1. Arrestare il consumer con `Ctrl+C` e attendere che termini; assicurarsi che anche il producer abbia finito.
2. Conservare o archiviare i risultati precedenti, se necessari.
3. Rimuovere **solo i dati generati dalla simulazione precedente** nelle directory `data/streaming/input`, `data/streaming/checkpoints/telemetry` e `data/streaming/metrics` (non eliminare `data/silver/car_data_2024`).
4. Avviare nuovamente consumer, producer e dashboard nell'ordine indicato.

**Nota:** producer e consumer usano ciascuno Spark in modalità `local[2]`; la loro esecuzione simultanea richiede risorse sufficienti. La procedura va ancora collaudata su una copia pulita del repository.

## Dashboard

La dashboard comprende cinque sezioni:

1. **Race Analytics** — analisi di una gara.
2. **Season Analytics** — statistiche della stagione.
3. **Driver Comparison** — confronto tra piloti.
4. **Telemetry Analytics** — analisi dei segnali telemetrici.
5. **Live Streaming Monitor** — visualizzazione delle metriche della simulazione streaming.

La dashboard è pensata per l'esecuzione locale, senza hosting pubblico.

## Documentazione

La relazione universitaria descrive le scelte architetturali, le elaborazioni Spark, i controlli di qualità e i risultati ottenuti. Il relativo PDF può essere aggiunto al repository nella cartella `docs/`.

## Fonte dei dati

Dati ottenuti tramite [OpenF1](https://openf1.org/). Il progetto è realizzato per finalità didattiche e non è affiliato o approvato dalla Formula 1 o da OpenF1.

## Stato della distribuzione

Il codice è stato sviluppato e testato nell'ambiente locale dell'autore. Le istruzioni di installazione, la disponibilità dei dataset e la procedura streaming devono essere verificate su una copia pulita del repository prima di considerare la distribuzione completamente riproducibile.
