
import requests as req
import time

def walletverification(address):

    hash = str(address)
    url = f'https://tonapi.io/v2/accounts/{hash}'
    headers = {'Accept': 'application/json'}
    response = req.get(url, headers=headers)
    if response.status_code == 200:
        adressdata = response.json()  
        # print(adressdata)
        balance = f"{adressdata['balance'] / 1000000000:,.9f}"
        status = adressdata['status']
        is_wallet = adressdata['is_wallet']
        wallet_data = {'address':adressdata['address'],'balance':balance,'status':status,'is_wallet':is_wallet}
        return wallet_data
    elif response.status_code == 404:
        print("Transaction not found.")
    else:
        print(f"Error: {response.status_code}")

def walletbalance(address, dolval):
    hash = str(address)
    url = f'https://tonapi.io/v2/accounts/{hash}/jettons'
    headers = {'Accept': 'application/json'}
    response = req.get(url, headers=headers)

    if response.status_code == 200:
        tokens = []
        adressdata = response.json()
        
        for jetton in adressdata["balances"]:

            if float(jetton["balance"]) > 0:

                balancenot = round(float(jetton['balance']) / 1e9, 0)
                balance = f"{int(balancenot):,}"
                
                tokens.append({'Token Name': jetton["jetton"]["symbol"], 'Token Address': jetton["jetton"]["address"], 'Balance':balance, 'balanceNot':balancenot})
                # print(tokens)
        tokens_sorted = sorted(tokens, key=lambda k: float(k['Balance'].replace(',', '')), reverse=True)  
        tokens_sorted =   tokens_sorted[:10]
        adresses = ''
        for i in range(0, len(tokens_sorted)):
            # , "Dolarval": dolarvalFormatted
            # , "Dolarval": "Not Available" ['rates'][coin]['prices']['USD']
            # time.sleep(0.2)
            if i == 10:
                break
            adresses += f",{tokens_sorted[i]['Token Address']}"

        if dolval:
            price = dolarPricing(adresses)
            if price:
                ton = price['rates']['TON']['prices']['USD']
            else:
                ton = 0
            
            for i in range(0, len(tokens_sorted)):
                if i == 10:
                    break
                if price:
                    
                    addresss = tokens_sorted[i]['Token Address']
                    dolarval = float(price['rates'][addresss]['prices']['USD']) * float(tokens_sorted[i]['balanceNot'])
                    tokens_sorted[i]["Dolarval"] = str(dolarval)
                else:
                    
                    tokens_sorted[i]["Dolarval"] = "Not Available"
            # print(tokens_sorted)
            tokens_sorted = sorted(tokens_sorted, key=lambda k: (k['Dolarval'] == "Not Available", float(k['Dolarval'].replace(',', '')) if k['Dolarval'] != "Not Available" else 0), reverse=True)
            return tokens_sorted,ton
        return tokens_sorted
        
        
    elif response.status_code == 404:
        print("Transaction not found.")
    else:
        print(f"Error: {response.status_code}")
def formatexpchart(x, pos=None):  # Add pos argument, default to None if not used
    str_num = str(x)
    if 'e' in str_num:
        parts = str_num.split('e')
        base = float(parts[0])
        exponent = int(parts[1].lstrip('-')) 
        x = int(str(base).split('.')[-1]) 
        y = int(str(base).split('.')[-2]) 
        value = str(y) + str(x)
        zeros = exponent - 1 
        formatted_num = "0.0({}){}".format(zeros, value)
        return formatted_num
    else:
        if x >= 0.001:
            formatted_num = "{:.4f}".format(x)
        elif x >= 0.00001:
            formatted_num = "{:.8f}".format(x)
        else:
            formatted_num = str(x)
        return formatted_num
def dolarPricing(coin):
        if str(coin).lower() == 'ton':
            hash = 'ton'
        else:
            hash = f'ton{coin}'
        url = f'https://tonapi.io/v2/rates'
        params = {'tokens':hash, 'currencies': 'usd,ton'}
        headers = {'Accept': 'application/json'}
        response = req.get(url, headers=headers, params=params)
        if response.status_code == 200:
            
            adressdata = response.json()
            if str(coin).lower() == 'ton':
                return {'coin':coin, 'price': adressdata['rates'][coin]['prices']['USD'], 'priceinton': adressdata['rates'][coin]['prices']['TON']}
            return adressdata
        else:
            print(response.json())
# print(dolarPricing('TON'))

