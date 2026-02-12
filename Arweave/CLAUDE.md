# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is the **Nettalco Blockchain Traceability System**, a pilot program that stores garment production traceability data on the Arweave blockchain. The system extracts data from Oracle databases, generates cryptographic hashes, and uploads immutable records to Arweave using the Irys network with Base-ETH as payment.

## Architecture

### Data Flow
1. **Extraction**: Python scripts query Oracle databases (DBIN/DBNET) for garment data
2. **Processing**: Generate unique SHA-256 hashes and store metadata in MariaDB
3. **Staging**: Save JSON files to `cola_de_envio/` directory (send queue)
4. **Upload**: Node.js scripts upload to Arweave via Irys and update MariaDB with transaction IDs

### Key Databases
- **Oracle DBIN** (128.0.1.97:1521/dbin): Main production database, source of truth
- **Oracle DBNET** (128.0.1.97:1521/dbnet): Legacy system
- **MariaDB db_prendas** (128.1.18.4:3306/db_prendas): Blockchain metadata storage

### MariaDB Tables
- `apdobloctrazhashtemp`: Staging table for pending uploads (status "PENDIENTE_SUBIDA")
- `apdobloctrazhash`: Final table with Arweave transaction IDs
- `apdoblochasherror`: Error tracking with version control

### Blockchain Layer
- **Network**: Arweave (permanent storage)
- **Access Point**: Irys mainnet (bundler/aggregator)
- **Payment**: Base-ETH (Ethereum Layer 2 on Base network)
- **Provider**: https://mainnet.base.org

## Development Commands

### Python Scripts

```bash
# Extract data for a specific date (configured in .env TARGET_DATE)
python main_mariadb.py

# Process multiple dates (weekend recovery mode)
python manager_fin_de_semana.py

# Generate SHA-256 hash (utility)
python hash_utils.py
```

### Node.js Scripts

```bash
# Install dependencies
npm install

# Upload staged files to Arweave with cost analysis
node subida_mariadb.js

# Check wallet and node balances
node ver_saldo.js

# Generate new Ethereum wallet
node generar_wallet.js

# Test upload (legacy)
node subida.js

# Cost simulation without uploading
node simulacion_costos.js
```

## Configuration

### Environment Variables (.env)
```
# Oracle DBNET (Legacy)
DB_USER=nettalco
DB_PASSWORD=nettalco
DB_HOST=128.0.1.97
DB_PORT=1521
DB_NAME=dbnet

# Oracle DBIN (Main)
DBIN_USER=dba2
DBIN_PASSWORD=oso1184
DBIN_HOST=128.0.1.97
DBIN_PORT=1521
DBIN_NAME=dbin

# MariaDB
DB_PRENDAS_USER=user_prendas
DB_PRENDAS_PASSWORD=Nettalco1234$
DB_PRENDAS_HOST=128.1.18.4
DB_PRENDAS_PORT=3306
DB_PRENDAS_NAME=db_prendas

# Blockchain
PRIVATE_KEY=0x... # Ethereum wallet private key

# Batch Processing
TARGET_DATE=2026-01-24  # Date for daily extraction (YYYY-MM-DD)
```

## Critical Workflows

### Daily Extraction & Upload
```bash
# 1. Set target date in .env
# 2. Extract and generate hashes
python main_mariadb.py

# 3. Upload to Arweave (requires user confirmation)
node subida_mariadb.js
```

### Batch Recovery (Multi-Date Processing)
Edit `FECHAS_A_PROCESAR` array in [manager_fin_de_semana.py](manager_fin_de_semana.py), then:
```bash
python manager_fin_de_semana.py
```
This script:
- Auto-updates `TARGET_DATE` in .env for each date
- Runs `main_mariadb.py` to extract data
- Executes `simulacion_costos.js` for cost reporting
- Moves processed files to `BACKUP_FINDE/<date>/`
- Generates `REPORTE_COSTOS_RECUPERACION.txt`

### Hash Generation Logic
The system uses [hash_utils.py](hash_utils.py:4) `generar_hash_unico()` to create SHA-256 fingerprints:
- Sorts JSON keys alphabetically (`sort_keys=True`) for consistency
- Converts timestamps/dates to strings (`default=str`)
- Generates hex digest for uniqueness verification

## Important Implementation Notes

### Database Connection Management
- [main_mariadb.py](main_mariadb.py:193) opens persistent connections (Oracle + MariaDB) for entire batch
- Auto-reconnection logic handles Oracle/MariaDB disconnections (see [main_mariadb.py](main_mariadb.py:207-210))
- Always close connections in `finally` blocks

### Duplicate Handling
- [main_mariadb.py](main_mariadb.py:163): MySQL error 1062 (duplicate entry) returns "RECICLADO" status
- Recycled records skip JSON file generation to save disk I/O
- Only "NUEVO" status creates files in `cola_de_envio/`

### Upload Financial Controls
[subida_mariadb.js](subida_mariadb.js:64-123) implements multi-level safety:
1. **Pre-flight analysis**: Calculates total cost in ETH and USD
2. **Balance verification**: Checks both Irys node balance and wallet balance
3. **Auto-funding**: If node balance insufficient, auto-funds from wallet with 10% buffer
4. **User confirmation**: Requires typing "si" before uploading
5. **Solvency check**: Aborts if total funds insufficient

### Data Extraction
[main_mariadb.py](main_mariadb.py:67-90) calls Oracle stored procedure:
```python
cursor.callproc("tzprc_traztick", [tickbarr, "es", None, p_menserro])
```
This populates 14 temporary tables (see `list_temp_dfs` in [main_mariadb.py](main_mariadb.py:29-34)).

### JSON Filtering
[main_mariadb.py](main_mariadb.py:92-111) uses [relevant_data.json](relevant_data.json) as a whitelist:
- Only specified fields from each table are included in final JSON
- Removes NULL, NaT, and NaN values
- Applies Unicode normalization for Oracle string data

### Arweave Upload Tags
[subida_mariadb.js](subida_mariadb.js:152-156):
```javascript
{ name: "Content-Type", value: "application/json" }
{ name: "App", value: "Nettalco-Trazabilidad" }
{ name: "Hash-Interno", value: hashInterno }
```
These tags enable Arweave GraphQL queries by hash.

## File Organization

### Active Directories
- `cola_de_envio/`: Staging area for JSON files pending upload
- `BACKUP_FINDE/`: Archive organized by date (managed by weekend recovery script)
- `stickers_qr/`: QR code generation output
- `assets/`: Static assets (logos, images)

### Key Files
- `relevant_data.json`: Field whitelist for JSON cleaning
- `clean.json`, `test.json`, `mi_json.json`: Sample/test data files
- `REPORTE_*.txt`: Automated batch processing reports

## Oracle Stored Procedure

The `tzprc_traztick` procedure is the core data extraction engine. It accepts:
- `tickbarr` (VARCHAR2): Garment barcode identifier
- `language` (VARCHAR2): "es" for Spanish output
- Returns data across 14 temporary tables capturing full production lineage

## Common Gotchas

1. **Oracle encoding**: Always use `encoding="UTF-8", nencoding="UTF-8"` in cx_Oracle connections
2. **Date format**: Oracle queries expect `TO_DATE('YYYY-MM-DD', 'YYYY-MM-DD')` format
3. **Hash consistency**: Never modify `hash_utils.py` logic - existing hashes depend on current algorithm
4. **Windows compatibility**: [manager_fin_de_semana.py](manager_fin_de_semana.py:82) uses `errors='replace'` for emoji handling in subprocess output
5. **Irys network**: Uses mainnet, not devnet - real ETH costs apply
6. **Base network**: Must have ETH on Base L2, not Ethereum mainnet

## Blockchain URLs

After successful upload, records are accessible at:
```
https://arweave.net/{transactionId}
```

Transaction IDs are stored in MariaDB `TTICKHASH` column.
