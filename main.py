"""A small script to crawl USD/IRR data."""

import argparse
import json
from datetime import datetime
from urllib.parse import urlencode
from urllib.request import urlopen

import matplotlib.pyplot as plt
import pandas as pd
import psycopg2

from config import DBNAME, HOST, PASSWORD, USER


class Price:
    """Store daily price data."""

    def __init__(
        self,
        open_price: str,
        low_price: str,
        high_price: str,
        close_price: str,
        diff: str,
        diff_percent: str,
        date: str,
    ):
        self.open = int(open_price.replace(",", ""))
        self.low = int(low_price.replace(",", ""))
        self.high = int(high_price.replace(",", ""))
        self.close = int(close_price.replace(",", ""))
        first_index = diff.find(">") + 1
        last_index = diff.find("/") - 1
        self.diff = int(diff[first_index:last_index])
        first_index = diff_percent.find(">") + 1
        last_index = diff_percent.find("%")
        self.diff_percent = float(diff_percent[first_index:last_index])
        self.date = datetime.strptime(date, "%Y/%m/%d").date()


class DataBase:
    """Create and manage a postgresql database."""

    def __init__(self):
        self.conninfo = f"postgresql://{USER}:{PASSWORD}@{HOST}/{DBNAME}"

    def create(self):
        """Create the database."""
        with psycopg2.connect(self.conninfo) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "CREATE TABLE IF NOT EXISTS usd_irr ("
                    "   id serial PRIMARY KEY,"
                    "   open integer,"
                    "   low integer,"
                    "   high integer,"
                    "   close integer,"
                    "   diff integer,"
                    "   diff_percent real,"
                    "   date date UNIQUE"
                    ")"
                )
            conn.commit()

    def insert(self, prices: list[Price]):
        """Insert a list of prices into database."""
        with psycopg2.connect(self.conninfo) as conn:
            with conn.cursor() as cur:
                for price in prices:
                    cur.execute(
                        "INSERT INTO usd_irr (open, low, high, close, diff, diff_percent, date) "
                        "VALUES (%s, %s, %s, %s, %s, %s,%s) ON CONFLICT DO NOTHING",
                        (
                            price.open,
                            price.low,
                            price.high,
                            price.close,
                            price.diff,
                            price.diff_percent,
                            price.date,
                        ),
                    )
            conn.commit()


class Crawler:
    """Crawl TGJU webite by api."""

    def __init__(self, from_date: str):
        params = urlencode({"from": from_date})
        url = "https://api.accessban.com/v1/market/indicator/summary-table-data/price_dollar_rl"
        self.url = f"{url}?{params}"

    def run(self) -> list[Price]:
        """Crawl the data and return a list of prices."""
        with urlopen(self.url) as f:
            data = json.loads(f.read())
        prices = []
        for price in data["data"]:
            try:
                prices.append(Price(*price[:-1]))
            except ValueError as e:
                print(e)
        return sorted(prices, key=lambda x: x.date, reverse=False)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("operation", choices=["crawl", "plot"])
    args = parser.parse_args()

    db = DataBase()
    db.create()

    if args.operation == "crawl":
        crawler = Crawler("1400/03/01")
        db.insert(crawler.run())
    elif args.operation == "plot":
        df = pd.read_sql_table("usd_irr", db.conninfo)

        plt.figure(figsize=(16, 9), dpi=200)
        plt.title("Close prices")
        plt.xlabel("date")
        plt.xticks(rotation=90)
        plt.ylabel("price (IRR)")
        plt.plot(df.date, df.close, ".-")
        plt.savefig("close.png")

        up = df[df.close >= df.open]
        down = df[df.close < df.open]

        plt.figure(figsize=(16, 9), dpi=200)
        plt.title("Daily candlestick")
        plt.xlabel("date")
        plt.xticks(rotation=90)
        plt.ylabel("price (IRR)")
        plt.bar(up.date, up.close - up.open, bottom=up.open, color="green")
        plt.bar(up.date, up.high - up.close, 0.1, bottom=up.close, color="green")
        plt.bar(up.date, up.low - up.open, 0.1, bottom=up.open, color="green")
        plt.bar(down.date, down.close - down.open, bottom=down.open, color="red")
        plt.bar(down.date, down.high - down.open, 0.1, bottom=down.open, color="red")
        plt.bar(down.date, down.low - down.close, 0.1, bottom=down.close, color="red")
        plt.savefig("candle.png")


if __name__ == "__main__":
    main()
