# E-Commerce Data Engineering & Analytics Platform

An end-to-end batch data engineering portfolio project using Microsoft Fabric, Azure, SQL Server, PySpark, Delta Lake, and dimensional modeling.

## 1. Business Problem

E-commerce platforms generate operational data across customers, products, sellers, orders, order items, payments, and customer activity events. This data needs to be ingested, validated, transformed, and organized into reliable analytical datasets.

This project demonstrates how to build a batch-oriented data platform that moves operational data through Bronze, Silver, and Gold layers and prepares curated data for analytical reporting.

## 2. Architecture

**Source system:** SQL Server hosted on AWS RDS  
**Data platform:** Microsoft Fabric

The planned end-to-end flow is:

1. **Source system** — SQL Server tables containing e-commerce operational data.
2. **Ingestion** — Fabric Data Factory pipelines copy source data into the Bronze Lakehouse.
3. **Bronze layer** — Raw ingested data retained for downstream processing.
4. **Silver layer** — PySpark-based transformations, data-quality checks, deduplication, and incremental processing.
5. **Gold layer** — Curated dimensional and fact tables loaded into a Fabric Warehouse.
6. **Consumption** — Analytical datasets designed for semantic modeling and Power BI reporting.

Customer activity events are generated separately as JSON Lines files and processed through the data platform.

## 3. Technology Stack

- Microsoft Fabric Data Factory and pipelines
- OneLake and Lakehouse
- PySpark notebooks
- Delta tables
- Fabric Warehouse and SQL
- SQL Server on AWS RDS
- Python and pandas
- Git and GitHub
- Power BI for analytical consumption

## 4. Source Data

The source schema contains eight operational tables:

- `locations`
- `customers`
- `sellers`
- `categories`
- `products`
- `orders`
- `order_items`
- `payments`

The SQL Server schema is maintained in `source-system/sql/source_schema.sql`.

The Python data generator creates synthetic e-commerce source data and supports initial loading and incremental batch generation.

## 5. Data Processing Design

### Bronze

Stores source data ingested from the operational system. Incremental extraction uses configured watermarks for eligible source tables, while selected reference data uses full loading.

### Silver

Processes incoming data, applies data-quality rules, handles duplicates and invalid records, and prepares cleaned datasets for analytical loading.

### Gold

Loads curated dimensional and fact tables into the Fabric Warehouse. The loading workflow uses staging, batch manifests, checkpoints, and commit procedures to coordinate processing.

The analytical model includes dimensions such as customers, products, sellers, categories, and regions, along with sales, payment, and customer-event fact tables.

## 6. Incremental Processing

The project demonstrates incremental batch generation and ingestion, watermark-based extraction, data-quality validation, and controlled downstream processing.

The implementation also includes checkpoint management and staged Gold processing. Failure recovery and restart behavior should be evaluated against the recorded batch state rather than assuming that every pipeline rerun is safe.

## 7. Repository Structure

```text
.
├── data_generator/
│   ├── config/
│   ├── database/
│   ├── generators/
│   ├── reference-data/
│   ├── scripts/
│   └── validation/
├── source-system/
│   └── sql/
│       └── source_schema.sql
├── .env.example
├── .gitignore
└── requirements.txt
```

## 8. Local Setup

### Prerequisites

- Python 3.11 or a compatible project Python version
- SQL Server ODBC Driver 18
- Access to a compatible SQL Server instance
- Git

### Install dependencies

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Create a local `.env` file based on `.env.example` and supply your own database connection settings. Do not commit `.env` or real credentials.

### Generate initial source data

After configuring and verifying the source database connection, use the project module entry point:

```powershell
python -m data_generator.scripts.generate_initial_data
```

Incremental batches can be generated using the corresponding incremental generator. Review each script's arguments and configuration before running it against a database.

**Important:** Data generation and database loading can modify source-system data. Use a controlled development database and review the target environment before executing loading or rollback scripts.

## 9. Data Quality and Validation

The repository contains validation modules for initial data, orders, payments, customer events, and related configuration.

The Fabric processing workflow also applies data-quality checks before promoting data to downstream analytical layers.

Validation should include row counts, duplicate business keys, referential integrity, rejected records, checkpoint advancement, and staging cleanup.

## 10. Security

- Database credentials are supplied through environment variables.
- `.env` is excluded from version control.
- `.env.example` documents the required configuration without containing actual credentials.
- Never publish database passwords, cloud access keys, connection strings, or private environment-specific details.

## 11. Current Status

**Project status: In progress**

The source schema and Python data-generator components have been committed to Git. Batch ingestion and Bronze/Silver/Gold processing have been implemented and exercised in Microsoft Fabric.

Remaining portfolio work includes documenting the Fabric architecture and orchestration, publishing appropriate pipeline and notebook artifacts where feasible, adding validation evidence and screenshots, and documenting reproducible setup and recovery procedures.

## 12. Future Improvements

- Publish a reviewed architecture diagram.
- Document pipeline parameters, dependencies, and watermark behavior.
- Add representative data-quality and reconciliation evidence.
- Document failure scenarios and recovery procedures.
- Add sanitized screenshots of the Fabric implementation.
- Complete the README with verified setup instructions and known limitations.

## Disclaimer

This project uses synthetic e-commerce data for educational and portfolio purposes. Cloud resources, connection settings, and Fabric workspace artifacts may require separate configuration and are not automatically provisioned by the Python repository.
