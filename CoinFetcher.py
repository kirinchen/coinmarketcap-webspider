from influxdb.exceptions import InfluxDBClientError

from Coin import CoinInfo, BuiltInCoin
from datetime import datetime, date, timedelta
from CMCBrowserUtils import getBrowser, WebDriverWait, EC, By
import requests, json
from InfluxDBService import insertData, queryToPoints, deleteByTags
import dateutil.parser
import Config
from dto.QuoteDto import Point

measurement = Config.env('influxdb.quote.measurement')


# https://web-api.coinmarketcap.com/v1/cryptocurrency/ohlcv/historical?id=1&convert=USD&time_start=1201245530&time_end=1615218330


class CoinFetcher:

    def __init__(self, ci: CoinInfo):
        self.info = ci

    def parseHistorical(self, s: datetime, e: datetime):
        url = self.info.getOhlcvHistoricalUrl(s, e)
        resp = requests.get(url)
        jr = json.loads(resp.text)
        return jr['data']['quotes']

    def getInitAt(self):
        queryTemp = 'SELECT * FROM "quote" WHERE "category"=\'{0}\' AND "name" = \'{1}\'   ORDER BY time ASC LIMIT 1'
        qstr = queryTemp.format("cryptocurrency", self.info.name)
        try:
            points = queryToPoints(qstr, measurement)
            if len(points) <= 0:
                return dateutil.parser.parse(Config.env("coinmarketcap.init.time"))
        except InfluxDBClientError:
            pass
        lAt: datetime = dateutil.parser.parse(points[0]['time'])
        # lAt = lAt + timedelta(days=1)
        return lAt

    def saveUntilNow(self):
        sAt = self.getInitAt()
        eAt = datetime.now()
        self.saveInfluxDB(sAt, eAt)

    def saveInfluxDB(self, s: datetime, e: datetime):
        idata = self.parseHistorical(s, e)
        iList = [self.toPoint(q) for q in idata]
        insertData(iList)

    def deleteAll(self):
        deleteByTags(measurement=measurement, tags={
            "name": self.info.name
        })

    def toPoint(self, q):
        # {
        #     "time_open": "2021-03-04T00:00:00.000Z",
        #     "time_close": "2021-03-04T23:59:59.999Z",
        #     "time_high": "2021-03-04T02:11:49.000Z",
        #     "time_low": "2021-03-04T20:13:59.000Z",
        #     "quote": {
        #         "USD": {
        #             "open": 50522.30503036,
        #             "high": 51735.09105293,
        #             "low": 47656.92904603,
        #             "close": 48561.1661539,
        #             "volume": 52343816679.73,
        #             "market_cap": 905414104807.24,
        #             "timestamp": "2021-03-04T23:59:59.999Z"
        #         }
        #     }
        # }
        vals = q['quote']['USD']
        tt = dateutil.parser.parse(vals['timestamp'])
        point = Point(measurement=measurement,
                      tags={
                          "symbol": self.info.symbol,
                          "name": self.info.name,
                          "category": 'cryptocurrency'
                      },
                      fields={
                          "time_open": q['time_open'],
                          "time_close": q['time_close'],
                          "time_high": q['time_high'],
                          "time_low": q['time_low'],
                          "open": toFloat(vals['open']),
                          "high": toFloat(vals['high']),
                          "low": toFloat(vals['low']),
                          "close": toFloat(vals['close']),
                          "volume": toFloat(vals['volume']),
                          "market_cap": toFloat(vals['market_cap']),
                      },
                      time=tt,
                      source='coinmarketcap'
                      )
        return point


def toFloat(i):
    ans = float(i)
    return ans


if __name__ == '__main__':
    import unittest


    class SymbolTest(unittest.TestCase):
        def test_saveUntilNow(self):
            cf = CoinFetcher(BuiltInCoin.BTC.getCoinInfo())
            cf.saveUntilNow()
            print(cf)
            self.assertIsNotNone(cf)

        def test_getInitAt(self):
            cf = CoinFetcher(BuiltInCoin.BTC.getCoinInfo())
            ans = cf.getInitAt()
            print(ans)
            self.assertIsNotNone(ans)


    tests = [
        SymbolTest('test_saveUntilNow'),
        SymbolTest('test_getInitAt'),

    ]
    suite = unittest.TestSuite()
    suite.addTests(tests)

    runner = unittest.TextTestRunner()
    runner.run(suite)
