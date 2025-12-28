"""Ingestion package."""
from ingestion.coinpaprika_ingester import CoinPaprikaIngester
from ingestion.coingecko_ingester import CoinGeckoIngester
from ingestion.csv_ingester import CSVIngester

__all__ = [
    "CoinPaprikaIngester",
    "CoinGeckoIngester",
    "CSVIngester",
]

