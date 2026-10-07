# 🚀 Universal Prospecting Platform (V9.0 "Turbo Core")

🌐 **[Visit the Official Website & Features Overview](https://codigo-origami.github.io/universal-prospecting-platform/)**

Open-source, local B2B lead generation and outreach engine built with Python, Streamlit, Playwright and SQLite.
**Everything runs and is stored on your computer**: no spreadsheets, no cloud accounts, no external database.

Created by **Código Origami · Alejandro Moreno** · MIT License

*Versión en español más abajo.* · 📝 **[Changelog](CHANGELOG.md)**

---

## ✨ What's new in V9.0

- **Much faster discovery**: one browser tab searches Google Maps while 1–4 tabs read company pages in parallel, and websites are analysed in a thread pool at the same time.
- **Reliable with Google**: detects CAPTCHAs / rate limits, pauses every tab automatically, lets you solve the CAPTCHA in the visible window, and stops cleanly (everything saved) if the block persists. Uses your real Chrome with a persistent profile when installed.
- **Better emails**: contact pages discovered from the site's own links (any language), JavaScript websites rendered in a real browser, Cloudflare-protected and obfuscated emails decoded, Facebook pages read, and a throttled search-engine fallback.
- **Verified data**: every email gets a confidence level (HIGH = company domain, MEDIUM = free mail on their own site, LOW = another company's domain), domains are checked for MX records, and phones/WhatsApp are normalised to international format with mobile detection.
- **Known prospects are skipped** (unless older than N days or your ICP changed) — re-runs are very fast.
- **English / Spanish interface**, with an explanation (ⓘ) on every field.
- **Formatted Excel export**: the same columns and colours as the screen, clickable links, filters, score bars and a summary sheet.
- **Email preview, test send to yourself and several templates** (`template_en.html`, `template_es.html`, …).
- **One-click installer**: `start.bat` installs everything the first time in a private environment and starts the app.

## 🛠️ Installation (Windows)

1. Download and unzip this folder.
2. Double-click **`start.bat`**.
   - The first time it installs everything automatically (Python 3.12 if missing, libraries and the browser) in a private `.venv` folder, so it never conflicts with other Python programs. It takes 3–5 minutes.
   - The next times it starts directly.
3. The app opens in your browser.

`install.bat` can be run on its own to repair or update the installation.

## 📖 User manual

### Tab 1 · DISCOVER
- **Locations** — `City, Country`, one per line. The country is used to read phone numbers. Google Maps returns at most ~120 places per search: add several cities to get more.
- **Target queries** — what to search in Google Maps, one per line.
- **Enrichment mode** — FAST (Maps + homepage), SMART (recommended: goes deeper only for promising or uncertain prospects), DEEP (everything for everyone).
- **⚙️ Speed & reliability** — parallel tabs (2 is safe), fast browser (no images), show browser (to solve CAPTCHAs), MX verification, search-engine fallback, social search, re-enrichment age, debug.
- **ICP qualification** — Required gate (AND per line, `|` = OR), strong and bonus signals with weights, absolute exclusions (negations such as "we do not do rentals" are understood).

### Tab 2 · QUALIFY
Funnel metrics, filters (ICP status, badge, location, text search, email/phone required, minimum score), the prospect table with clickable links and score bars, **Excel export (formatted)**, CSV export, recovery of stuck sends and the database reset (with confirmation).

### Tab 3 · PROSPECT
Gmail/Google Workspace sending with **App Password**, template selection, preview, test email to yourself, badge targeting, daily limit and humanised delays. Global recipient locks guarantee nobody is emailed twice. `[Company Name]` is replaced with each prospect's name (also in the subject).

### Gmail App Password
Google Account → Security → turn on 2-Step Verification → App passwords → create one → paste the 16-letter code in the app.

---

## 🇪🇸 Guía rápida en español

**Instalación:** descomprime la carpeta y haz doble clic en **`start.bat`**. La primera vez instala todo solo (Python 3.12 si falta, librerías y navegador) en un entorno privado `.venv`, sin interferir con otros programas de Python. Tarda 3–5 minutos; las siguientes veces arranca directamente.

**Idioma:** arriba a la derecha puedes cambiar entre English y Español. Cada campo tiene un icono ⓘ con su explicación.

**Pestaña 1 · Descubrir:** indica ubicaciones (`Ciudad, País`) y búsquedas de Google Maps, elige el modo (RÁPIDO, INTELIGENTE o PROFUNDO) y define tu cliente ideal (filtro obligatorio, señales y exclusiones). En "⚙️ Velocidad y fiabilidad" ajustas las pestañas en paralelo, la verificación de emails, etc. Si Google muestra un CAPTCHA, la app se pausa sola; con el navegador visible puedes resolverlo y continúa.

**Pestaña 2 · Cualificar:** embudo, filtros, tabla con enlaces y **exportación a Excel con el mismo aspecto que en pantalla** (colores por prioridad, enlaces clicables, filtros y hoja de resumen).

**Pestaña 3 · Prospectar:** envío con Gmail mediante **contraseña de aplicación**, elección de plantilla (`template_en.html`, `template_es.html`…), vista previa y email de prueba. Nadie recibe el email dos veces.

**Tus datos** se guardan en `origami_leads.db`, en la misma carpeta. Para hacer copia de seguridad, copia ese archivo.

---

## 🤝 Contributing
Pull requests are welcome!

## 📜 License
MIT License. Created by [Código Origami - Alejandro Moreno](https://github.com/Codigo-origami).
