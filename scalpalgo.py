import alpaca_trade_api as alpaca
import asyncio
import pandas as pd
import sys
import yaml
import os
import logging


def main():
    api = alpaca.REST()
    stream = alpaca.StreamConn()

    symbol = args.symbol
    scalpalgo = Algo(api, symbol, lot=args.lot)

    @stream.on(r'^AM')
    async def on_bars(conn, channel, data):
        if data.symbol in fleet:
            fleet[data.symbol].on_bar(data)

