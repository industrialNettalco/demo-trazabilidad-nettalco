# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**Nettalco Digital Passport** - A blockchain-based garment traceability visualization system that provides transparent, immutable tracking of textile manufacturing from raw materials to finished products. The system combines blockchain storage (Arweave) with an interactive web-based viewer showing the complete production journey.

## High-Level Architecture

This project has **two main components**:

### 1. Backend (Blockchain Data Pipeline) - `Arweave/` directory
- Extracts production data from Oracle databases (DBIN/DBNET)
- Generates cryptographic hashes and stores metadata in MariaDB
- Uploads immutable JSON records to Arweave blockchain via Irys
- See [Arweave/CLAUDE.md](Arweave/CLAUDE.md) for complete backend documentation

### 2. Frontend (Digital Passport Viewer) - `index.html`
- Single-file React application (no build step required)
- Loads traceability JSON data and renders interactive timeline
- Displays production stages, workers, chemical compliance, and blockchain verification
- Bilingual support (Spanish/English)
- Deployed on Vercel at https://demo-trazabilidad-nettalco.vercel.app

## Data Flow

```
Oracle DB → Python extraction → JSON files → Arweave blockchain
                                      ↓
                             data/ directory (local copy)
                                      ↓
                             index.html (React viewer)
```

1. **Extraction**: `Arweave/main_mariadb.py` queries Oracle databases for garment data
2. **Storage**: JSON files saved to `data/` directory (named by hash or tickbar)
3. **Upload**: `Arweave/subida_mariadb.js` uploads to Arweave and stores transaction ID
4. **Display**: User scans QR code → `index.html?id={hash}` → loads `data/{hash}.json`

## Frontend Architecture (`index.html`)

### Stack
- **React 18** (loaded via CDN, no build process)
- **Framer Motion** for animations
- **Tailwind CSS** (JIT via CDN)
- **Babel Standalone** for JSX transformation

### Key Components

**App** - Main component, handles data loading via URL parameter `?id={hash}`
```javascript
// URL format: index.html?id=092686113013
// Loads: ./data/092686113013.json
```

**StepCard** - Renders each production stage with:
- Stage information (title, date, description)
- Team members with photos (3 fallback sources)
- Chemical compliance accordion (ZDHC MRSL V3.1)
- Stage image/video

**AuditorBadge** - Displays certification and audit information

**PersonCard** - Worker profile card with photo and role

### Internationalization
All UI strings defined in `TRANSLATIONS` object (lines 30-120):
- `es`: Spanish (default)
- `en`: English
Toggle via language switcher in header

### Data Structure
JSON files in `data/` directory contain Oracle tables:
- `tztotrazwebinfo`: General garment information
- `tztotrazwebacab`: Header/tracking data
- `tztotrazwebcost`: Production order details
- `tztotrazweboper`: Worker operations
- `tztotrazwebmate`: Materials used
- `tztotrazmaquproc`: Machine/process details
- Plus 8 more tables (see Arweave/CLAUDE.md for complete schema)

### Arweave Integration
Lines 572-575 in `index.html`:
```javascript
const ARWEAVE_MAP = {
    "hash_name": "arweave_transaction_id"
};
```
Maps local JSON hashes to Arweave transaction IDs for blockchain verification button.

## Development Workflows

### Frontend Development

**Local Testing**:
```bash
# Serve locally (any HTTP server works)
python -m http.server 8000
# Open: http://localhost:8000/index.html?id=092686113013
```

**Edit Translations**:
Modify `TRANSLATIONS` object in [index.html](index.html:30-120)

**Add New Stage Icons**:
Update `Icons` object in [index.html](index.html:130-150)

**Modify Stage Rendering**:
Edit `StepCard` component in [index.html](index.html:424-564)

### Backend Development

See [Arweave/CLAUDE.md](Arweave/CLAUDE.md) for complete backend commands.

**Quick Reference**:
```bash
cd Arweave

# Extract data for date in .env TARGET_DATE
python main_mariadb.py

# Generate QR code stickers for new JSON files
python generar_qr.py

# Upload to Arweave blockchain
node subida_mariadb.js
```

### QR Code Generation

[Arweave/generar_qr.py](Arweave/generar_qr.py) creates printable stickers with QR codes:

```python
# Configuration
BASE_URL = "https://demo-trazabilidad-nettalco.vercel.app"
CARPETA_SALIDA = "stickers_qr"

# Generates QR pointing to: {BASE_URL}/index.html?id={hash_id}
```

**Output**: PNG stickers in `stickers_qr/` directory suitable for garment labels

## Chemical Compliance (ZDHC MRSL)

The system tracks chemical inputs used in production and displays ZDHC MRSL V3.1 compliance.

**Database**: `Arweave/db_quimicos_simple.csv` contains approved chemicals
**Display**: Collapsible accordion in stage 3 (Dyeing) shows chemical list with suppliers
**Implementation**: Lines 476-523 in [index.html](index.html:476-523)

## Deployment

**Platform**: Vercel
**Configuration**: [vercel.json](vercel.json)
- Proxies photo API requests to `http://app.nettalco.com.pe/php/foto.php`
- Caching: 1 hour browser, 24 hours CDN
- CORS enabled for demo domain

**Deploy**:
```bash
# Via Vercel CLI
vercel deploy --prod

# Or via GitHub integration (auto-deploys on push to main)
```

## Directory Structure

```
├── index.html              # Main React viewer application
├── data/                   # JSON traceability files (hash-named)
├── assets/                 # Static assets
│   ├── fase1-6.png        # Production stage images
│   ├── logos/             # Client logos
│   └── videos/            # Production stage videos
├── stickers_qr/           # Generated QR code stickers
├── Arweave/               # Blockchain backend (separate CLAUDE.md)
│   ├── main_mariadb.py    # Data extraction script
│   ├── subida_mariadb.js  # Arweave upload script
│   ├── generar_qr.py      # QR code generator
│   └── CLAUDE.md          # Backend documentation
└── vercel.json            # Deployment configuration
```

## Photo Loading Strategy

Worker photos use 3-tier fallback system ([index.html](index.html:278-290)):
1. **Local API**: `/api/foto/{codigo}` (proxied to internal server)
2. **Public API**: `http://app.nettalco.com.pe/php/foto.php?codigo={codigo}`
3. **Fallback Avatar**: Generic user icon

This ensures photos display even if internal servers are unreachable.

## Common Tasks

### Add New Production Stage
1. Add stage data to Oracle database tables
2. Run `Arweave/main_mariadb.py` to extract
3. Update stage images in `assets/` (fase7.png, etc.)
4. Modify `formatData()` function in [index.html](index.html:200-380) if needed

### Update Chemical Compliance List
1. Edit `Arweave/db_quimicos_simple.csv`
2. Reload data extraction to pick up new chemicals
3. Frontend automatically displays via existing accordion logic

### Link Arweave Transaction
After uploading to Arweave:
1. Get transaction ID from MariaDB `apdobloctrazhash.TTICKHASH`
2. Add mapping to `ARWEAVE_MAP` in [index.html](index.html:572-575)
3. Redeploy to Vercel

### Create QR Codes for New Batch
```bash
cd Arweave
python generar_qr.py
# Generates QR stickers in stickers_qr/ directory
# Print and attach to garment labels
```

## Important Implementation Notes

### React Without Build Tools
This project intentionally uses **no build step**. React, Babel, and Tailwind are loaded via CDN for:
- Rapid prototyping and iteration
- Zero configuration deployment
- Easy hosting on static platforms
Do not introduce webpack, vite, or other bundlers unless specifically required.

### Data Naming Convention
JSON files in `data/` use **SHA-256 hashes** as filenames (generated by `Arweave/hash_utils.py`).
- Pattern: `{hash}.json` (e.g., `092686113013.json`)
- Hash ensures uniqueness and integrity
- Never rename files manually - use hash_utils.py

### Blockchain Verification
"Verificar Registro" button only activates when:
1. Hash exists in `ARWEAVE_MAP`
2. Links to ViewBlock explorer: `https://viewblock.io/arweave/tx/{txid}`
This provides third-party verification of blockchain storage.

### Video Autoplay
Stage videos use aggressive autoplay strategy:
```javascript
defaultMuted = true
muted = true
playsInline = true
webkit-playsinline = "true"
```
If autoplay fails, falls back to static image automatically.

## External Dependencies

### APIs
- **Photo API**: `app.nettalco.com.pe/php/foto.php` (internal worker photos)
- **Arweave Gateway**: `arweave.net` (blockchain data retrieval)
- **ViewBlock**: `viewblock.io` (blockchain explorer)

### CDN Resources
- React 18 (unpkg.com)
- Framer Motion 10.16.4
- Tailwind CSS (CDN)
- Babel Standalone
- Google Fonts (Inter)

## Gotchas

1. **Case Sensitivity**: Oracle table names are uppercase in JSON (e.g., `TCODICLIE`)
2. **Date Formats**: Oracle dates stored as strings in ISO format
3. **Photo Loading**: Always check browser console for photo loading errors during development
4. **Language Toggle**: Changing language reformats data, causing component re-renders
5. **Vercel Rewrites**: Local development won't have photo API proxy - photos will fail locally
6. **Hash Consistency**: Never modify hash generation logic in `hash_utils.py` - existing blockchain records depend on it
