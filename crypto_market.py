from config import COINMARKETCAP_TOKEN
import requests

def get_current_eth_usd():
    """
    Get market price ETH/USDT from coinmarketcap
    :return: int market price ETH
    """

    url = 'https://pro-api.coinmarketcap.com/v1/cryptocurrency/quotes/latest?symbol=ETH&convert=USD'
    headers = {
        'Accepts': 'application/json',
        'X-CMC_PRO_API_KEY': COINMARKETCAP_TOKEN,
    }
    response = requests.get(url, headers=headers).json()
    return round(float(response['data']['ETH']['quote']['USD']['price']))

def get_current_btc_usd():
    """
    Get market price BTC/USDT from blockchain.com
    :return:
    """
    url = 'https://api.blockchain.com/v3/exchange/tickers/BTC-USD'
    response = requests.get(url).json()
    return round(response['price_24h'])