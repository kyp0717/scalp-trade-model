import argparse
import algo
import stock
import logging
from log_setup import logger

import alpaca_trade_api as alpaca
import asyncio
import pandas as pd
import sys
import yaml
import os
import logging

logger = logging.getLogger(__name__)

with open(r'/home/phage/.config/alpaca/keys.paper.yaml') as k:
    keys = yaml.load(k, Loader=yaml.FullLoader)

os.environ['APCA_API_BASE_URL'] = keys['urltrade']
os.environ['APCA_API_DATA_URL'] = keys['urldata']
os.environ['APCA_API_KEY_ID'] = keys['key']
os.environ['APCA_API_SECRET_KEY'] = keys['secret']


def main(args):
    logger.info("Inside main function")
    api = alpaca.REST()
    stream = alpaca.StreamConn()
    logger.info("Instantiating scalp object with arguments ...")

    scalp = algo.Algo(api=api, symbol=args.symbol, lot=args.lot)

    @stream.on(r'^AM')
    async def on_bars(conn, channel, data):
        scalp.on_bar(data)

    @stream.on(r'trade_updates')
    async def on_trade_updates(conn, channel, data):
        logger.info(f'trade_updates {data}')
        symbol = data.order['symbol']
        if symbol == args.symbol:
            scalp.on_order_update(data.event, data.order)

    async def periodic():
        while True:
            if not api.get_clock().is_open:
                logger.info('exit as market is not open')
                sys.exit(0)
            await asyncio.sleep(30)
            positions = api.list_positions()
            pos = [p for p in positions if p.symbol == args.symbol]
            scalp.checkup(pos[0] if len(pos) > 0 else None)

    channels = ['trade_updates', args.symbol]

    loop = stream.loop
    loop.run_until_complete(asyncio.gather(
        stream.subscribe(channels),
        periodic(),
    ))


if __name__ == '__main__':

    fmt = '%(asctime)s:%(filename)s:%(lineno)d:%(levelname)s:%(name)s:%(message)s'
    # logger.basicConfig(level=logging.INFO, format=fmt)
    logger.setLevel(logging.INFO)
    fh = logging.FileHandler('test.log')
    fh.setFormatter(logging.Formatter(fmt))
    logger.addHandler(fh)

    parser = argparse.ArgumentParser()
    parser.add_argument('symbol', nargs='+')
    parser.add_argument('--lot', type=float, default=2000)
    logger.info("Calling main ....")

    main(parser.parse_args())
