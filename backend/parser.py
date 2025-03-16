import csv
import requests
import sys
import json


def getGengi(date, currency):
    currencyToId = {'EUR': 4064, 'USD': 4055}
    url = f'http://www.sedlabanki.is/xmltimeseries/Default.aspx?DagsFra={date}&DagsTil={date}T23:59:59&TimeSeriesID={currencyToId[currency]}&Type=csv'
    res = requests.get(url)
    return float(res.content.decode('UTF-8').split(';')[-1])



def parseActivityStatement(file):
    with open(file, newline='') as csvfile:
        data = csv.reader(csvfile, delimiter=',')

        trades = []
        summary = []
        total_price = 0
        for row in data:
            if row[0] == 'Trades' and row[3] == 'Stocks':
                if row[1] == 'Data':
                    quantity = float(row[7])
                    price = float(row[8])
                    #price = quantity * pricePerShare
                    costBasis = float(row[12]) #costBasis = quantity * pricePerShare + commission
                    date = row[6].split(',')[0]
                    currency = row[4]
                    gengi = getGengi(date, currency)
                    priceISK = gengi*costBasis
                    total_price += priceISK
                    trades.append({"symbol" : row[5], 'date': date, "quantity": quantity, 'currency': currency, 'gengi': gengi, "basis": costBasis, "basisISK": priceISK})
                elif row[1] == 'SubTotal':
                    summary.append({"symbol": row[5], "kaupverd": round(total_price), "quantity": float(row[7])})
                    total_price = 0

    return {"trades": trades, "summary": summary}


csvFile = sys.argv[1]
try:
    data = parseActivityStatement(csvFile)
    print(json.dumps(data))
except Exception as e:
    print(str(e))


    