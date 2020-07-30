import pandas as pd


def current_time():
    return pd.Timestamp.now(tz='America/New_York')


def set_state(new_state) -> str:
    self._state = new_state


def outofmarket():
    return current_time().time() >= pd.Timestamp('15:55').time()
