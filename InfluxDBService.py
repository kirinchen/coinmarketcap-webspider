from influxdb import InfluxDBClient
import Config

client = InfluxDBClient(Config.env('influxdb.url'), Config.envInt('influxdb.port'), Config.env('influxdb.username'),
                        Config.env('influxdb.password'), Config.env('influxdb.db'))

INSER_BATCH_SIZE = 1


def insertData(ps: []):
    # arr = [p.__dict__ for p in ps]
    # # js = json.dumps(arr)
    # print(arr)
    # client.write_points(points=arr,batch_size=100)
    iList = []
    for i in range(len(ps)):
        iList.append(ps[i].__dict__)
        if len(iList) >= INSER_BATCH_SIZE:
            print(iList)
            client.write_points(points=iList, batch_size=100)
            iList = []


def queryToPoints(q: str, measurement: str):
    rss = client.query(q)
    ans = list(rss.get_points(measurement=measurement))
    return ans


def deleteByTags(measurement: str, tags={}):
    client.delete_series(measurement=measurement, tags=tags)


if __name__ == '__main__':
    client.drop_measurement('quote')
    client.query('DROP SERIES FROM "quote"')
    results = client.query('select * from "quote"')
    print(results.raw)

    results = client.query('show series')
    print(results.raw)


    # client.delete_series(measurement='quote', tags={
    # })
    # p = Point(measurement='test', fields={
    #     'testV': 123
    # })
    # insertData([p])
    # # js = json.dumps(ps)
    # # print(js)
    # print(p)
