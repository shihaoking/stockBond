# -*- coding: utf8 -*-
import os, urllib, urllib2, re, time, codecs
import json, copy


class StockInfo:
    def __init__(self, code, onSellStockCount, winRate, maxTingBan, maxPercent, startPrice, maxPrice, startMarketValue):
        self.code = code
        self.onSellStockCount = onSellStockCount
        self.winRate = winRate
        self.maxTingBan = maxTingBan
        self.maxPercent = maxPercent
        self.startPrice = startPrice
        self.maxPrice = maxPrice
        self.startMarketValue = startMarketValue


def downLoadJSONFromUrl(url):
    req = urllib2.Request(url)
    req.add_header("Accept", "application/json, text/javascript, */*; q=0.01")
    req.add_header("Content-Type", "text/html; charset=utf-8")
    req.add_header("User-Agent", "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/44.0.2403.125 Safari/537.36")
    req.add_header("Cookie", "_ga=GA1.2.383540459.1539436561; device_id=bdef9d1665d60a114ac57e0cb804b361; _gid=GA1.2.506762489.1544268790; xq_a_token=6125633fe86dec75d9edcd37ac089d8aed148b9e; xq_a_token.sig=CKaeIxP0OqcHQf2b4XOfUg-gXv0; xq_r_token=335505f8d6608a9d9fa932c981d547ad9336e2b5; xq_r_token.sig=i9gZwKtoEEpsL9Ck0G7yUGU42LY; u=321544322897483; Hm_lvt_1db88642e346389874251b5a1eded6e3=1544268785,1544322897; Hm_lpvt_1db88642e346389874251b5a1eded6e3=1544322906")
    

    try:
        fd = urllib2.urlopen(req).read()
    except Exception, e:
        print '--->Falid'
        print str(e)
        return ''

    return fd.decode('utf-8')


def getStockBondPage():
    url = "https://www.jisilu.cn/data/cbnew/cb_list/?___jsl=LST___t=1544269387771"
    return downLoadJSONFromUrl(url)


def getStockPage(stock_code):
    url = "https://stock.xueqiu.com/v5/stock/quote.json?symbol=" + stock_code
    return downLoadJSONFromUrl(url)


def getStockBondList():
    result = getStockBondPage()
    jsonResult = json.loads(result)
    stockList = jsonResult['rows']
    return stockList


def getStockInfo(stock_code):
    result = getStockPage(stock_code)
    jsonResult = json.loads(result)
    stockInfo = jsonResult['data']['quote']
    return stockInfo


def getStockBondInfo(stockBondInfoJson):
    stockBondInfo = stockBondInfoJson['cell']

    #过滤特殊债券
    if stockBondInfo['qflag'] == 'Q' or stockBondInfo['redeem_price_ratio'] is None:
        return None

    newStockBondInfo = {}
    newStockBondInfo[u'代码'] = stockBondInfo['bond_id']
    newStockBondInfo[u'名称'] = stockBondInfo['bond_nm']
    newStockBondInfo[u'股票代码'] = stockBondInfo['stock_id']
    newStockBondInfo[u'股票名称'] = stockBondInfo['stock_nm']

    newStockBondInfo[u'现价'] = float( stockBondInfo['price'])
    newStockBondInfo[u'溢价率'] = stockBondInfo['premium_rt'] #溢价率
    
    newStockBondInfo[u'转股价'] = float(stockBondInfo['convert_price']) #转股价
    newStockBondInfo[u'股票最新价'] = stockBondInfo['stock_net_value']
    
    stockInfo = getStockInfo(stockBondInfo['stock_id'])
    market_capital = float(stockInfo['market_capital']) #总股本
    newStockBondInfo[u'股票市值'] = round(market_capital / 100000000, 2) #总市值，单位：亿

    newStockBondInfo[u'强赎触发价'] = -1 if stockBondInfo['force_redeem_price'] == "-" else float(stockBondInfo['force_redeem_price']) #强赎触发价
    newStockBondInfo[u'回售触发价'] = -1 if stockBondInfo['put_convert_price'] == "-" else float(stockBondInfo['put_convert_price']) #回售触发价
    newStockBondInfo[u'赎回价'] = float(stockBondInfo['redeem_price']) #赎回价
    newStockBondInfo[u'赎回理论价'] = float(stockBondInfo['redeem_price_ratio']) #赎回触时转债的理论市场价格
    newStockBondInfo[u'市值'] = round(float(stockBondInfo['orig_iss_amt']), 2) #发行规模
    newStockBondInfo[u'剩余市值'] = -1 if stockBondInfo['curr_iss_amt'] == "-" else round(float(stockBondInfo['curr_iss_amt']), 2) #剩余规模
    newStockBondInfo[u'转债占比'] = stockBondInfo['convert_amt_ratio'] #转债占比=转债余额/总市值
    newStockBondInfo[u'转股日期'] = stockBondInfo['convert_dt'] #转股日期
    newStockBondInfo[u'到期日'] = stockBondInfo['maturity_dt']  #到期日
    newStockBondInfo[u'强赎触发天'] = stockBondInfo['redeem_count_days'] #赎回触发需要的连续交易日
    newStockBondInfo[u'强赎有效天'] = stockBondInfo['redeem_total_days'] #赎回触发需要的有效最大交易日
    newStockBondInfo[u'评级'] = stockBondInfo['rating_cd'] #评级
    newStockBondInfo[u'是否在转股期'] = stockBondInfo['convert_cd'] #是否移到转股期
    newStockBondInfo[u'到期税收收益'] = stockBondInfo['ytm_rt_tax']  #到期税后收益

    return newStockBondInfo


def downLoadStockBondInfos():
    stock_bond_list = getStockBondList()

    stock_bond_infos = []
    for stockBondLine in stock_bond_list:
        stock_bond_info = getStockBondInfo(stockBondLine)
        if stock_bond_info is not None:
            stock_bond_infos.append(stock_bond_info)
            print stock_bond_info[u'代码']

    return stock_bond_infos


def startDownload():
    stock_bond_infos = downLoadStockBondInfos()

    finalResult = json.dumps(stock_bond_infos, ensure_ascii=False)

    fp = codecs.open("bond_infos.json", 'w', 'utf-8')
    fp.write(finalResult)
    fp.close()

    print '-----Done-----'
startDownload()
