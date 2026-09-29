# 🚀 Universal Prospecting Platform (V8.12 Enterprise Core)

🌐 **[Visit the Official Website & Features Overview](https://codigo-origami.github.io/universal-prospecting-platform/)**

An open-source, highly professional automated B2B lead generation and outreach engine built with Python, Streamlit, and Playwright. 

This application acts as your local, autonomous B2B data extraction and qualification engine. It goes far beyond a simple scraper by employing an **Ideal Customer Profile (ICP)** filtering system, Hierarchical Deduplication, Smart Cascading Enrichment, and a built-in Cold Email automation module.

## 🛠️ Zero-Setup Installation (Windows)

We designed this tool to be accessible for non-technical users. You do not need to configure environments or manually install Python.

1. Download and unzip this repository.
2. Double-click on `install.bat`. 
   * *The installer will automatically detect your system, download Python 3.12 (if missing), install it silently, and configure all dependencies.*
3. Double-click on `start.bat` to launch the application in your browser.

---

## 📖 Comprehensive User Manual

The platform is divided into three main operational tabs.

### TAB 1: DISCOVER (Ideal Customer Profile)
This is the engine room where you define what leads to find and how to score them.

**Discovery Parameters:**
* **Locations (City, Country):** The geographical areas you want to target. Enter one location per line. Example: `Austin, Texas`.
* **Target Queries (Maps Search):** The search terms the engine will use on Google Maps. Enter one per line. Example: `software development agency`.
* **Max prospects per query:** The absolute limit of raw businesses the engine will scrape per query-location combination before enrichment.
* **Enrichment Mode:**
  * *FAST:* Only scrapes Maps and the company's Homepage.
  * *SMART (Recommended):* Dynamically decides whether to perform deep scraping (searching sub-pages and social media) only if the lead meets specific score thresholds.
  * *DEEP:* Forces the engine to scrape contact pages, about pages, and search social networks for every single prospect (slower, but highly comprehensive).
* **Headless Mode / Debug Mode:** Check Headless to run the scraping browser invisibly in the background. Check Debug to print exact error logs on screen.

**ICP Qualification (Gate & Weighted Signals):**
* **Required GATE:** The ultimate filter. If the prospect's website does NOT contain these keywords, they are immediately marked as "NOT ICP" and score 0. (Use `|` for OR conditions).
* **Strong Signals:** Keywords that strongly indicate a good fit. Format is `keyword : weight`. Example: `B2B : 25`.
* **Bonus Signals:** Secondary keywords that add slight value to the score.
* **Absolute Exclusion:** If any of these words are found (e.g., `rental`, `student`), the prospect is immediately marked as "EXCLUDED". The engine understands contextual negation (e.g., "we do not offer rentals" bypasses the exclusion).

### TAB 2: QUALIFY (Funnel Dashboard)
Review, filter, and manage the extracted database.

* **Metrics Dashboard:** Instantly view your funnel health (Total, ICP Qualified, Email Ready).
* **Database Filters:** Filter the table by ICP Status, Priority Badge (🔥 Excellent, 🟢 Good, 🟡 Normal, 🔴 Low), minimum score, or enforce that leads must have an email/phone number.
* **Export CSV:** Downloads the currently filtered view directly to your computer.
* **Recover Stuck Sends:** If a mass email campaign crashes or you close the app mid-send, click this to unlock leads stuck in "Sending..." status.
* **Clear Local Database:** Wipes the local SQLite database completely to start a fresh project.

### TAB 3: PROSPECT (Native Email Outreach)
A built-in, atomic mailing engine with global concurrency locks, ensuring you never email the same prospect twice across different campaigns.

**Email Configuration Fields:**
* **Sender Email Address:** Your sending email (e.g., your Google Workspace or Gmail address).
* **App Password:** **DO NOT** use your regular email password. You must generate a 16-digit App Password (see the Email Setup Guide below).
* **Email Subject:** The subject line of your cold outreach.
* **Target Quality:** Choose which lead tiers receive the email (e.g., only send to 🔥 EXCELLENT and 🟢 GOOD).
* **Max emails / Humanized Delay:** Set a limit to protect your email deliverability, and adjust the random waiting time between sends to simulate human behavior.

---

## 📧 Email Setup Guide (Gmail / Google Workspace)

To use the outreach module safely, you must create a dedicated **App Password**. Standard passwords are blocked by Google for security reasons.

**Step-by-Step Configuration:**
1. Go to your [Google Account Management](https://myaccount.google.com/).
2. Navigate to the **Security** tab on the left menu.
3. Scroll down to the "How you sign in to Google" section.
4. Ensure **2-Step Verification** is turned ON. (You cannot generate App Passwords without this).
5. Click on **2-Step Verification**, scroll to the bottom, and click on **App Passwords**.
6. Create a new app password (name it something like "Origami Prospector").
7. Google will provide a **16-letter code** in a yellow box (e.g., `abcd efgh ijkl mnop`).
8. Copy this 16-letter code (without spaces) and paste it into the **"App Password"** field in Tab 3 of the application.

*Note: Edit the `template_en.html` file in the root folder to customize your email copy. The placeholder `[Company Name]` will dynamically inject the prospect's normalized company name.*
---

## 🤝 Contributing
Pull requests are welcome! If you'd like to improve the scraping logic, add new data enrichment methods, or optimize the scoring algorithms, feel free to fork this repository.

## 📜 License
This project is licensed under the MIT License. Created by [Código Origami - Alejandro Moreno](https://github.com/Codigo-origami).
