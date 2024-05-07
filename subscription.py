import requests as req
import ccxt
import csv
import os
import aiofiles
import time
from userHandler import update_subscription_plan

def to_nano(amount):
    """
    Convert TON to nano TON.
    """
    return int(amount * 1e9)

def generate_payment_link(to_wallet, amount, comment, app):
    """
    Generate a payment link for subscription.
    """
    nano_amount = to_nano(amount)
    if app == "tonhub":
        return f"https://tonhub.com/transfer/{to_wallet}?amount={nano_amount}&text={comment}"
    else: 
        return f"https://app.tonkeeper.com/transfer/{to_wallet}?amount={nano_amount}&text={comment}"
def checkTransactions(ownerWallet, user_id):
    url = 'https://toncenter.com/api/v2/getTransactions'
    headers = {'Accept': 'application/json'}
    params = {'address':ownerWallet,
              'limit':100}
    response = req.get(url, headers=headers, params=params)
    if response.status_code == 200:
        transactions = response.json() 
        for trans in transactions['result']: 
            if user_id in str(trans['in_msg']['message']):
                print(trans['in_msg']['message'])
                value = int(trans['in_msg']['value']) / 1e9
                print(value)
        # print(transactions)
    elif response.status_code == 404:
        print("Transaction not found.")
    else:
        print(f"Error: {response.status_code}")
    return
def checkTransactions(wallet,trx, user_id):
    url = f'https://tonapi.io/v2/accounts/{wallet}/events/{trx}'
    headers = {'Accept': 'application/json'}
    response = req.get(url, headers=headers)
    if response.status_code == 200:
        transactions = response.json() 
        if 'actions' in transactions:
            for action in transactions['actions']:
                if 'TonTransfer' in action:
                    if user_id in str(action['TonTransfer']['comment']):
                            print(action['TonTransfer']['comment'])
                            value = int(action['TonTransfer']['amount']) / 1e9
                            print(value)
                            data = {'comment': str(action['TonTransfer']['comment']), 'value':value}
                            return data
        
    elif response.status_code == 404:
        print("Transaction not found.")
    else:
        print(f"Error: {response.status_code}")
def livetonprice():
    exchange_name = 'bybit'
    exchange = getattr(ccxt, exchange_name)()
    price = exchange.fetchTicker('TON/USDT')
    if price:
        return float(price['info']['lastPrice'])
    else:
        return 0
async def getsubByUser(user_id):
    try:
        with open('subscriptions.csv', mode="r", encoding="utf-8") as existing_csv:
            csv_reader = csv.reader(existing_csv)
            for row in csv_reader:
                if len(row) > 1:
                    if str(user_id) == str(row[0]):
                        return row
    except Exception as e:
        print(f"Error : {e}")
        return None

async def verifyTimestamp(User):
    temp_filename = 'temp_subscriptions_update.csv'
    updated = False  

    try:
        async with aiofiles.open('subscriptions.csv', mode='r', encoding='utf-8') as csvfile, \
                aiofiles.open(temp_filename, mode='w', encoding='utf-8') as temp_file:
            original_content = await csvfile.read()
            reader = csv.reader(original_content.splitlines())
            for row in reader:
                if len(row) == 0: continue 
                user_id, plan, ts_str = row
                if User == user_id:
                    
                    if plan != 'free':
                        ts = int(ts_str)  
                        now = int(time.time())  
                        print(ts,now)
                        print(now > ts)
                        if now > ts:
                            row[1] = 'free'  
                            row[2] = 0
                            updated = True 
                            await update_subscription_plan(row[0],'free')   
                        
                        await temp_file.write(','.join(row) + '\n')

        if updated:
            os.replace(temp_filename, 'subscriptions.csv')
            return True
        else:
            os.remove(temp_filename)
            return False
    except Exception as e:
        print(f"Error: {e}")
        if os.path.exists(temp_filename):
            os.remove(temp_filename)
async def ReadAllplans():
    plans = []
    try:
        with open('wallets.csv', mode="r", encoding="utf-8") as existing_csv:
            csv_reader = csv.reader(existing_csv)
            
            for row in csv_reader:
                # print(row)
                if len(row) > 1:
                        plans.append(row)
        return plans
    except Exception as e:
        print(f"Error : {e}")
        return None
# print(livetonprice())
# print(checkTransactions('0:57eb74407604a19f7e04005315ef70aeb7b675e6551977586756f6baf12125ee', '7cacd60b69c6fa23d456d5cf61b207815f105a3541988fbb46f893722d67e3b1', 'gia'))