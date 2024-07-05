#import sys

#getframe_expr = 'sys._getframe({}).f_code.co_name'

import requests
import time
import hmac
import hashlib
import base64
from urllib.parse import urlencode

class Korbit:
    BASE_URL = "https://api.korbit.co.kr"

    def __init__(self, api_key, api_secret):
        self.api_key = api_key
        self.api_secret = api_secret

    def _get_timestamp(self):
        return int(time.time() * 1000)

    def _create_signature(self, params):
        query_string = urlencode(params)
        message = query_string.encode('utf-8')
        secret = self.api_secret.encode('utf-8')
        signature = hmac.new(secret, message, hashlib.sha256).hexdigest()
        #print("Query String:", query_string)
        #print("Signature:", signature)
        return signature

    def _send_request(self, method, endpoint, params):
        url = f"{self.BASE_URL}{endpoint}"
        headers = {"X-KAPI-KEY": self.api_key}

        if method in ["GET", "DELETE"]:
            params['timestamp'] = self._get_timestamp()
            signature = self._create_signature(params)
            params['signature'] = signature
            response = requests.request(method, url, headers=headers, params=params)
        else:  # POST
            params['timestamp'] = self._get_timestamp()
            signature = self._create_signature(params)
            params['signature'] = signature
            headers["Content-Type"] = "application/x-www-form-urlencoded"
            response = requests.request(method, url, headers=headers, data=urlencode(params))

        json_data = None
        try:
            json_data = response.json()
            response.raise_for_status()
        except requests.exceptions.HTTPError as e:
            '''
            if response.status_code == 422 :
                return response.json()
            raise e
            '''
            if json_data is not None :
                return json_data
            else:
                print(f"HTTPError: {e}")
                print(f"    Response Status Code: {response.status_code}")
                print(f"    Response Text: {response.text}")
                print("    Request URL:", url)
                print("    Request Headers:", headers)
                print("    Request Params:", params)

                raise e

        #return response.json()
        return json_data

    def _normalize_symbol(self, symbol):
        symbol = symbol.lower()
        if not symbol.endswith('_krw'):
            symbol += '_krw'
        return symbol

    def adjust_price(self, price):
        price = float(price)
        if price < 1:
            tick_size = 0.0001
        elif price < 10:
            tick_size = 0.001
        elif price < 100:
            tick_size = 0.01
        elif price < 1000:
            tick_size = 0.1
        elif price < 5000:
            tick_size = 1
        elif price < 10000:
            tick_size = 5
        elif price < 50000:
            tick_size = 10
        elif price < 100000:
            tick_size = 50
        elif price < 500000:
            tick_size = 100
        elif price < 1000000:
            tick_size = 500
        else:
            tick_size = 1000
        return round(price / tick_size) * tick_size

    def get_ticker(self, symbol):
        symbol = self._normalize_symbol(symbol)
        endpoint = "/v2/tickers"
        params = {"symbol": symbol}
        return self._send_request("GET", endpoint, params)

    def place_order(self, symbol, side, price=None, qty=None, order_type="limit", time_in_force="gtc", amount=None):
        symbol = self._normalize_symbol(symbol)
        if order_type == "limit" and price is not None:
            price = self.adjust_price(price)
        endpoint = "/v2/orders"
        params = {
            "symbol": symbol,
            "side": side,
            "orderType": order_type,
            "timeInForce": time_in_force,
        }
        if price is not None:
            params["price"] = price
        if qty is not None:
            params["qty"] = qty
        if amount is not None:
            params["amount"] = amount
        return self._send_request("POST", endpoint, params)

    def cancel_order(self, symbol, order_id):
        symbol = self._normalize_symbol(symbol)
        endpoint = "/v2/orders"
        params = {
            "symbol": symbol,
            "orderId": order_id,
        }
        return self._send_request("DELETE", endpoint, params)

    def get_order(self, symbol, order_id=None, client_order_id=None):
        symbol = self._normalize_symbol(symbol)
        endpoint = "/v2/orders"
        params = {
            "symbol": symbol,
        }
        if order_id is not None:
            params["orderId"] = order_id
        if client_order_id is not None:
            params["clientOrderId"] = client_order_id
        return self._send_request("GET", endpoint, params)

    def get_open_orders(self, symbol, limit=10):
        symbol = self._normalize_symbol(symbol)
        endpoint = "/v2/openOrders"
        params = {
            "symbol": symbol,
            "limit": limit,
        }
        return self._send_request("GET", endpoint, params)

    def get_recent_trades(self, symbol, limit=100):
        symbol = self._normalize_symbol(symbol)
        endpoint = "/v2/trades"
        params = {
            "symbol": symbol,
            "limit": limit
        }
        return self._send_request("GET", endpoint, params)


    def get_my_recent_trades(self, symbol, start_time=None, end_time=None, limit=500):
        symbol = self._normalize_symbol(symbol)
        endpoint = "/v2/myTrades"
        params = {
            "symbol": symbol,
            "limit": limit
        }
        if start_time is not None:
            params["startTime"] = start_time
        if end_time is not None:
            params["endTime"] = end_time
        return self._send_request("GET", endpoint, params)

    def get_account_info(self, currencies=None):
        endpoint = "/v2/balance"
        params = {}
        if currencies:
            params['currencies'] = ','.join(currencies)
        return self._send_request("GET", endpoint, params)

    def sell_limit_order(self, symbol, price, amount):
        return self.place_order(symbol, "sell", price=price, qty=amount, order_type="limit")

    def buy_limit_order(self, symbol, price, amount):
        return self.place_order(symbol, "buy", price=price, qty=amount, order_type="limit")

    def buy_market_order(self, symbol, amount):
        return self.place_order(symbol, "buy", amount=amount, order_type="market", time_in_force="ioc")

    def sell_market_order(self, symbol, amount):
        return self.place_order(symbol, "sell", amount=amount, order_type="market", time_in_force="ioc")


if __name__ == "__main__":
    import os
    import time
    import pprint
    #api_key = "your_api_key"
    #api_secret = "your_api_secret"
    api_key = os.environ.get('KORBIT_APIKEY')
    api_secret = os.environ.get('KORBIT_SECRET')

    korbit = Korbit(api_key, api_secret)


    # 내 최근 체결 내역 조회
    my_recent_trades = korbit.get_my_recent_trades("etc_krw", start_time=0,limit=100)
    #print("My Recent Trades:", my_recent_trades)
    pprint.pprint(my_recent_trades)

    '''
    # 최근체결내역
    trades = korbit.get_recent_trades("etc_krw")
    #print("Ticker:", trades)
    pprint.pprint(trades)

    # 시세 조회
    ticker = korbit.get_ticker("etc_krw")
    print("Ticker:", ticker)

    # 매수 주문
    order = korbit.place_order("etc_krw", "buy", "30000", "0.3")
    print("Order:", order)
    time.sleep(1)

    # 주문 취소
    #cancel = korbit.cancel_order("etc_krw", order["orderId"])
    cancel = korbit.cancel_order("etc_krw", order["data"]["orderId"])
    print("Cancel:", cancel)
    time.sleep(1)

    # 미체결 주문 조회
    open_orders = korbit.get_open_orders("etc_krw")
    print("Open Orders:", open_orders)
    time.sleep(1)

    # 자산 현황 조회
    account_info = korbit.get_account_info(["btc", "eth"])
    print("Account Info:", account_info)
    '''

