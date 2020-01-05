from functools import lru_cache
from datetime import datetime
from collections import namedtuple
import subprocess
import shlex
import logging
import os

import pandas as pd

from backtest.database import InfluxDB

log = logging.getLogger(__name__)


@lru_cache(maxsize=1024)
def get_equity_price(symbol: str,
                     start_date: datetime,
                     end_date: datetime) -> pd.DataFrame:

    idb = InfluxDB()
    prices = idb.get_assets('AV', fromdate=start_date.date(), todate=end_date.date(), tickers=[symbol])['close']
    prices.index = pd.to_datetime(prices.index.get_level_values(0), utc=True)
    prices.name = 'price'

    return prices


def result_str(self: 'Result') -> str:
    result = ''
    if self.returncode:
        result += "Error code: {}\n".format(self.returncode)
    result += "STDOUT:\n{}".format(self.output)
    if self.error:
        result += "STDERR:\n{}".format(self.error)
    return result.rstrip()


Result = namedtuple('Result', ['returncode', 'output', 'error'])
Result.__str__ = result_str  # type: ignore


def run(cmd: str, ignore_error: bool = False, shell: bool = False) -> Result:
    class ShellException(Exception):
        pass

    log.debug('%s $ %s', os.getcwd(), cmd)
    if not shell:
        cmd = shlex.split(cmd)  # type: ignore
    process = subprocess.Popen(
        cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=shell)
    out, err = process.communicate()
    out = out.decode('utf-8')
    err = err.decode('utf-8')
    result = Result(process.returncode, out, err)
    if result.returncode != 0 and not ignore_error:
        raise ShellException(str(result))
    log.debug(result)
    return result
