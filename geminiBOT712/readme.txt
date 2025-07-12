# Autonomous Trading System

## 1. Project Overview

This project is a professional-grade, autonomous trading system designed to generate consistent returns by analyzing a wide array of real-time data sources. The system leverages a multi-model AI pipeline running on a local GPU to identify high-probability trading opportunities and executes them within a strict, volatility-aware risk management framework.

The entire architecture is containerized with Docker and designed for high availability, low latency, and scalability. It makes extensive use of free data sources to minimize operational costs while maximizing data-driven insights.

### Key Features

-   **Multi-Source Data Ingestion:** Real-time data from options flow, institutional filings, news (RSS & direct scraping), social media (Twitter, Reddit, Stocktwits), economic releases (FRED), and market data (Yahoo Finance).
-   **Advanced Local AI Analysis:** An ensemble of models for sentiment analysis, pattern recognition, and predictive analytics, all running locally for speed and cost-effectiveness.
-   **High-Confidence Signal Generation:** Confluence-based signal validation requiring multiple confirming indicators from our diverse data sources.
-   **Dynamic Risk Management:** Volatility-adjusted stop losses (ATR-based), dynamic position sizing, and portfolio-level circuit breakers.
-   **Real-Time Monitoring & Execution:** A full monitoring suite for system and API health, with a Telegram bot for alerts and control.
-   **Advanced Backtesting Engine:** A pluggable, event-driven backtester for rigorously validating strategies against historical data.

---

## 2. System Architecture

The system is composed of over a dozen microservices, each running in its own container and communicating via a Redis message queue. This decoupled design ensures that a failure in one component does not bring down the entire system.

1.  **Data Ingestion Engine:** A collection of concurrent workers fetching data.
2.  **AI Analysis Pipeline (`EnsembleManager`):** The "brain" that processes raw data to extract actionable insights.
3.  **Signal Generation Engine (`SignalAggregator`):** Aggregates insights to produce high-confidence trading signals.
4.  **Risk Management System (`PortfolioMonitor`, `VolatilityManager`):** Enforces risk rules on every trade and the overall portfolio.
5.  **Execution Engine (`PaperTrader`, `LiveBroker` framework):** Manages trades and order lifecycle.
6.  **Database & Caching:** PostgreSQL (ideally with TimescaleDB) for persistent data storage and Redis for real-time messaging and caching.
7.  **Monitoring & Alerting (`SystemMonitor`, `ApiMonitor`):** A dedicated suite of tools to ensure system health and reliability.

---

## 3. Technology Stack

-   **Backend:** Python 3.11+ (asyncio)
-   **AI/ML:** PyTorch, Transformers (`DistilBERT`), Scikit-learn, Pandas
-   **Database:** PostgreSQL (TimescaleDB recommended), Redis
-   **Deployment:** Docker, Nginx
-   **Communication:** Telegram Bot API
-   **System Monitoring:** `psutil`

---

## 4. Deployment Instructions

Follow these steps to deploy the system on your production VPS (e.g., a Vultr GPU instance).

### Step 1: Clone the Repository
```bash
git clone <your-repo-url>
cd trading-system

Step 2: Configure Environment
Copy the example environment file and fill it out with your credentials.
cp .env.example .env
nano .env

You must fill in:
	•	All PostgreSQL variables.
	•	Your TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID.
	•	A new ENCRYPTION_KEY (generate one with python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())").
	•	Any API keys for the paid/private services you intend to use.
Step 3: Encrypt Your API Keys
This script reads the keys from your .env file, encrypts them, and saves them to a secure file. The system will only read keys from this encrypted file at runtime.
python3 scripts/encrypt_keys.py

After this, you can optionally remove the plaintext keys from your .env file for added security.
Step 4: Build and Launch the System
Use Docker Compose to build the images and launch all services in detached mode.
docker-compose up --build -d

Step 5: Initialize the Database
With the containers running, execute the database initialization script inside the app container.
docker-compose exec app python scripts/initialize_db.py

This will create all the necessary tables and indexes.
Step 6: Monitor the System
You can view the logs for all services to ensure they started correctly.
docker-compose logs -f

To view the logs for a specific service (e.g., the EnsembleManager):
docker-compose logs -f app

You should start receiving INFO level alerts in your Telegram channel as the system comes online.
5. Using the System
	•	Interaction: All alerts and primary interactions are handled via the Telegram bot.
	•	Trading Mode: By default, the system runs in paper mode. To switch to live trading, you must implement the LiveBroker module and change the TRADING_MODE in config/trading_config.py.
	•	Backtesting: To test new strategies, create a new strategy class in src/backtesting/strategy.py, load your historical data into the data/historical directory, and run the scripts/run_backtest.py script.
# To run the backtester inside the container
docker-compose exec app python scripts/run_backtest.py

