import pandas as pd
import stock
import logging

logger = logging.getLogger(__name__)


class Algo():
    def __init__(self, api, symbol, lot):
        self.symbol = symbol
        self.lot = lot
        self.api = api
        self.algo_state = "TO_BUY"
        self.stx = stock.Stock(self.api, self.symbol,
                               self.lot, self.algo_state)
        logger.info("Inside algo instance ...")

        now = pd.Timestamp.now(tz='America/New_York').floor('1min')
        market_open = now.replace(hour=9, minute=30)
        today = now.strftime('%Y-%m-%d')
        tomorrow = (now + pd.Timedelta('1day')).strftime('%Y-%m-%d')
        data = self.api.polygon.historic_agg_v2(
            self.symbol, 1, 'minute', today, tomorrow, unadjusted=False).df
        bars = data[market_open:]
        self.barlist = bars

    def current_time(self):
        return pd.Timestamp.now(tz='America/New_York')

    def set_state(self, new_state) -> str:
        self.algo_state = new_state

    def outofmarket(self):
        return self.current_time().time() >= pd.Timestamp('15:55').time()

    def calc_buy_signal(self):
        mavg = self.barlist.rolling(20).mean().close.values
        closes = self.barlist.lose.values
        if closes[-2] < mavg[-2] and closes[-1] > mavg[-1]:
            return True
        else:
            return False

    def on_bar(self, single_bar):
        print('Bar data (raw format)')
        print(single_bar)
        print('------------')
        self.barlist = self.barlist.append(pd.DataFrame({
            'open': single_bar.open,
            'high': single_bar.high,
            'low': single_bar.low,
            'close': single_bar.close,
            'volume': single_bar.volume,
        }, index=[single_bar.start]))

        if len(self.barlist) < 21:
            return
        if self.outofmarket():
            return
        if self.algo_state == 'TO_BUY':
            signal = self.calc_buy_signal()
            if signal:
                self.stx.submit_buy()

    def on_order_update(self, event, order):
        p = stock.Position(self.api, self.symbol)
        if event == 'fill':
            if self.algo_state == 'BUY_SUBMITTED':
                self.set_state('TO_SELL')
                self.stx.submit_sell()
                return
            elif self.algo_state == 'SELL_SUBMITTED':
                self.set_state('TO_BUY')
                return
        elif event == 'partial_fill':
            return
        elif event in ('canceled', 'rejected'):
            if event == 'rejected':
                # self._l.warn(f'order rejected: current order = {self._order}')
                pass
            if self.algo_state == 'BUY_SUBMITTED':
                if p.position is not None:
                    self.set_state('TO_SELL')
                    self.stx.submit_sell()
                else:
                    self.set_state('TO_BUY')
            elif self.algo_state == 'SELL_SUBMITTED':
                self.set_state('TO_SELL')
                self.stx.submit_sell(bailout=True)
            else:
                logger.warn(f'unexpected state for {event}: {self.algo_state}')

    def checkup(self, position):
        logger.info('periodic task')
        o = stock.Order(self.api, self.symbol)
        p = stock.Position(self.api, self.symbol)
        now = self.current_time()

        if (o.order is not None and
            o.order.side == 'buy' and now -
                pd.Timestamp(o.order.submitted_at, tz='America/New_York') > pd.Timedelta('2 min')):
            last_price = self.api.polygon.last_trade(self.symbol).price
            logger.info(
                f'canceling missed buy order {o.order.id} at {o.order.limit_price} '
                f'(current price = {last_price})')
            self.stx.cancel_order()

        if p.position is not None and self.outofmarket():
            self.stx.submit_sell(bailout=True)
