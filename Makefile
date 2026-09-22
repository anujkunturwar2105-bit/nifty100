# Makefile for Nifty 100 Financial Intelligence Platform

.PHONY: setup load ratios test dashboard api reports all clean

PYTHON = python
PIP = pip

setup:
	$(PIP) install -r requirements.txt

load:
	$(PYTHON) -m src.etl.loader

ratios:
	$(PYTHON) -m src.analytics.ratios
	$(PYTHON) -m src.analytics.health_score
	$(PYTHON) -m src.analytics.sector
	$(PYTHON) -m src.analytics.peer
	$(PYTHON) -m src.analytics.cashflow_kpis
	$(PYTHON) -m src.analytics.clustering
	$(PYTHON) -m src.analytics.valuation

reports:
	$(PYTHON) -m src.reports.tearsheet
	$(PYTHON) -m src.reports.sector_report
	$(PYTHON) -m src.reports.portfolio_report
	$(PYTHON) -m src.reports.screener_report

test:
	pytest -q
	pytest --cov=src --cov-report=term-missing

dashboard:
	streamlit run src/dashboard/app.py

api:
	uvicorn src.api.main:app --reload --host 127.0.0.1 --port 8000

all: load ratios reports test

clean:
	rm -rf output/* reports/tearsheets/* data/nifty100.db
