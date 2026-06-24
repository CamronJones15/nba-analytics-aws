# 🏀 NBA Analytics AWS Pipeline

A end-to-end data engineering project that ingests NBA statistics, processes them
through an AWS cloud pipeline, and visualizes insights via an interactive Streamlit dashboard.

## 📊 What It Does

- **Ingests** live NBA data (player stats, team standings, shot charts) using the `nba_api`
- **Stores** raw data in AWS S3 as a data lake
- **Transforms** raw JSON → Parquet via AWS Glue ETL jobs
- **Queries** processed data with AWS Athena (serverless SQL)
- **Orchestrates** daily data pulls via AWS Lambda
- **Visualizes** insights through a Streamlit dashboard with Plotly charts

## 🏗️ Architecture

```
nba_api → Lambda → S3 (raw/) → Glue ETL → S3 (processed/) → Athena → Streamlit
```

## 🛠️ Tech Stack

| Layer         | Technology          |
|---------------|---------------------|
| Data Source   | nba_api (Python)    |
| Storage       | AWS S3              |
| ETL           | AWS Glue + PySpark  |
| Querying      | AWS Athena          |
| Orchestration | AWS Lambda          |
| Dashboard     | Streamlit + Plotly  |
| IaC           | Terraform           |
| CI/CD         | GitHub Actions      |

## 📁 Project Structure

```
nba-analytics-aws/
├── ingestion/              # NBA data ingestion scripts
│   ├── lambda_handler.py   # AWS Lambda entry point
│   └── nba_client.py       # nba_api wrapper
├── glue_jobs/              # AWS Glue ETL scripts
│   └── transform_stats.py
├── athena/                 # SQL query templates
│   ├── player_performance.sql
│   ├── team_standings.sql
│   └── shot_analysis.sql
├── dashboard/              # Streamlit app
│   └── app.py
├── terraform/              # AWS infrastructure as code
│   ├── main.tf
│   ├── s3.tf
│   ├── lambda.tf
│   ├── glue.tf
│   └── variables.tf
├── .github/workflows/
│   └── deploy.yml
├── .env.example
├── requirements.txt
└── README.md
```

## 🚀 Getting Started

### Prerequisites
- Python 3.11+
- AWS CLI configured (`aws configure`)
- Terraform 1.5+
- Git

### 1. Clone the repo
```bash
git clone https://github.com/CamronJones15/nba-analytics-aws.git
cd nba-analytics-aws
```

### 2. Set up Python environment
```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Configure environment variables
```bash
cp .env.example .env
# Edit .env with your AWS credentials and bucket name
```

### 4. Provision AWS infrastructure
```bash
cd terraform
terraform init
terraform plan
terraform apply
```

### 5. Run the dashboard locally
```bash
streamlit run dashboard/app.py
```

## 👤 Author
**Camron Jones** — [GitHub](https://github.com/CamronJones15)

Data Engineering Portfolio Project | AWS | Python | SQL
