import logging
# from log_setup import logger
import pandas as pd

logger = logging.getLogger(__name__)

# logger.setLevel(logging.INFO)
# log_format = logging.Formatter('%(levelname)s:%(name)s:%(message)s')
# logfile_handler = logging.FileHandler('stock.log')
# logfile_handler.setFormatter(log_format)
# logger.addHandler(logfile_handler)


class Stock:
    def __init__(self, api, lot, symbol, state):
        self.symbol = symbol
        self.api = api
        self.lot = lot
        self.algo_state = state

    def set_state(self, new_state) -> str:
        self.algo_state = new_state

    def cancel_order(self):
        o = Order(self.api, self.symbol)
        if o.order is not None:
            self.api.cancel_order(o.order.id)

    def submit_buy(self):
        trade = self.api.polygon.last_trade(self.symbol)
        amount = int(self.lot / trade.price)
        try:
            order = self.api.submit_order(
                symbol=self.symbol,
                side='buy',
                type='limit',
                qty=amount,
                time_in_force='day',
                limit_price=trade.price,
            )
        except Exception as e:
            logger.info('order submission failed')
            logger.info(e)
            self.set_state('TO_BUY')
            return

        logger.info(f'submitted buy {order}')
        self.set_state('BUY_SUBMITTED')

    def submit_sell(self, bailout=False):
        p = Position(self.api, self.symbol)
        params = dict(
            symbol=self.symbol,
            side='sell',
            qty=p.position['qty'],
            time_in_force='day',
        )
        if bailout:
            params['type'] = 'market'
        else:
            now_price = float(self.api.polygon.last_trade(self.symbol).price)
            cost_basis = float(p.position['avg_entry_price'])
            limit_price = max(cost_basis + 0.01, now_price)
            params.update(dict(
                type='limit',
                limit_price=limit_price,
            ))
        try:
            self.api.submit_order(**params)
        except Exception as e:
            logger.error(e)
            self.set_state('TO_SELL')
            return
        self.set_state('SELL_SUBMITTED')


class Position:
    def __init__(self, api, symbol):
        self.api = api
        self.symbol = symbol
        self.position = self.get()

    def get(self) -> dict:
        pos = self.api.get_positions(self.symbol)
        _pos = pos[0] if len(pos) > 0 else None
        return _pos

    def check(self):
        pass


class Order:
    def __init__(self, api, symbol):
        self.api = api
        self.symbol = symbol
        self.order = self.get()

    def get(self) -> dict:
        order = self.api.get_orders(self.symbol)
        _ord = order[0] if len(order) > 0 else None
        return order

    def check(self):
        pass
