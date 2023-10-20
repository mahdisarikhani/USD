# USD

A small script to crawl USD/IRR data from [TGJU](https://www.tgju.org/).

## Quick Start

Install [Python](https://www.python.org/) and [PostgreSQL](https://www.postgresql.org/).
Clone this repository and install required packages.

```shell
git clone https://github.com/mahdisarikhani/USD.git
cd USD/
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Change `config.py` based on your local PostgreSQL database.
Run `main.py` to crawl and plot the data.

```shell
python main.py crawl
python main.py plot
```
