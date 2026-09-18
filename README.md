# 🚀 Universal Prospecting Platform (v8.12 Enterprise)

An open-source, highly professional automated B2B lead generation and outreach engine built with Python, Streamlit, and Playwright. Designed by **Codigo Origami**.

This application acts as your local, autonomous B2B data extraction and qualification engine. It goes far beyond a simple scraper by employing an **Ideal Customer Profile (ICP)** filtering system, Hierarchical Deduplication, Smart Cascading Enrichment, and a built-in Cold Email automation module.

## ⚙️ Key Features
- **Local Persistence (SQLite):** Your leads and campaigns are safely stored on your machine in a robust local database. No cloud spreadsheets or external APIs required.
- **Hierarchical Deduplication:** Intelligent rules that check Maps ID, Domain, Phone, and Normalized Company Name across regions to protect your database from duplicates.
- **Dual Business Scoring:** The engine extracts high-signal text (Title, Meta, H1/H2 tags) from websites to evaluate Contactability and Business Fit based on your custom required, strong, and bonus keywords.
- **Smart Enrichment Architecture:** Save immense bandwidth and time. The engine only performs heavy, deep enrichment (Social Media, Subpages, Search Engine fallbacks) if the lead shows promise based on an initial fast pass.
- **Atomic Campaign Engine:** Safely send cold emails directly from your SMTP server. Features global recipient-level concurrency locks to ensure a company never receives duplicate emails across different branches.

## 🛠️ Easy Setup (Windows)

1. Unzip this folder.
2. Double-click on `install.bat`. Wait for all Python dependencies to install.
3. Double-click on `start.bat` to launch the application in your browser.

## 🗺️ The 3-Step Process
1. **DISCOVER:** Tell the engine what to search for (Location + Target Query) and define your ICP with weighted scoring (e.g., `b2b:25, distributor:15`).
2. **QUALIFY:** Review the generated database. View the `Matched Keywords` evidence to understand why a lead scored high. Export your pristine list to CSV.
3. **PROSPECT:** Configure your SMTP credentials (e.g., Gmail + 16-digit App Password) and launch an automated email campaign to leads marked as "Ready to Contact".

---

## 🤝 Contributing
Pull requests are welcome! If you'd like to improve the scraping logic, add new data enrichment methods, or optimize the scoring algorithms, feel free to fork this repository.

## 📜 License
This project is licensed under the MIT License. Created by [Código Origami - Alejandro Moreno](https://github.com/Codigo-origami).
