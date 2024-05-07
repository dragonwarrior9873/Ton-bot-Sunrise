import aiohttp
import requests as req

async def fetch_image(url):
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            if response.status == 200:
                return await response.read()
            else:
                raise Exception(f"Failed to fetch image from {url}")
            
def transactionsNFT(hash):
    trx = str(hash)
    url = f'https://tonapi.io/v2/nfts/{trx}'
    headers = {'Accept': 'application/json'}
    response = req.get(url, headers=headers)
    if response.status_code == 200:
        transdata = response.json()
        return {'url':transdata['previews'][-1]['url'], 'name':transdata['metadata']['name']}
    else:
        print(f"Error: {response.status_code}")
def transactionsEvent(wallet,hash):
    trx = str(hash)
    url = f'https://tonapi.io/v2/accounts/{wallet}/events/{trx}'
    headers = {'Accept': 'application/json'}
    response = req.get(url, headers=headers)
    if response.status_code == 200:
        transdata = response.json()
        # print(transdata)
        # print(len(transdata['actions']))
        transtype = ''
        transaction_info = {}
        if 'actions' in transdata:
            for action in transdata['actions']:
                if action['type'] == 'NftPurchase':
                    if 'NftPurchase' in action:
                        if transdata['account']['address'] == action['NftPurchase']['buyer']['address']:
                            transtype = 'Buy NFT'
                        elif transdata['account']['address'] == action['NftPurchase']['seller']['address']:
                            transtype = 'Sell NFT'

                        previews = action['NftPurchase']['nft']['previews']
                        highest_resolution_preview_link = previews[-1]['url']  # Last item in the list
                        
                        transaction_info2 = {
                                                'TXid': transdata['event_id'],
                                                'Transaction Type': transtype,
                                                'Buyer Address': action['NftPurchase']['buyer']['address'],
                                                'Seller Address': action['NftPurchase']['seller']['address'],
                                                'Purchase Value': action['NftPurchase']['amount']['value'],
                                                'Token Name': action['NftPurchase']['amount']['token_name'],
                                                'NFT Address': action['NftPurchase']['nft']['address'],
                                                'Imagelink': highest_resolution_preview_link, 
                                                'NFT Name': action['NftPurchase']['nft']['metadata']['name']
                                            }
                        return transaction_info2

                if action['type'] == 'NftItemTransfer':
                    if transdata['account']['address'] == action['NftItemTransfer']['sender']['address']:
                            transtype = 'Sent NFT'
                            nftdata = transactionsNFT(action['NftItemTransfer']['nft'])
                            transaction_info2 = {
                                                        'TXid': transdata['event_id'],
                                                        'Transaction Type': transtype,
                                                        'Sender Address': action['NftItemTransfer']['sender']['address'],
                                                        'Receiver Address': action['NftItemTransfer']['recipient']['address'],
                                                        'NFT Address': action['NftItemTransfer']['nft'],
                                                        'Imagelink': nftdata['url'], 
                                                        'NFT Name': nftdata['name']
                                                    }
                            return transaction_info2
                    elif transdata['account']['address'] == action['NftItemTransfer']['recipient']['address']:
                            transtype = 'Received NFT'
                            nftdata = transactionsNFT(action['NftItemTransfer']['nft'])
                            transaction_info2 = {
                                                        'TXid': transdata['event_id'],
                                                        'Transaction Type': transtype,
                                                        'Sender Address': action['NftItemTransfer']['sender']['address'],
                                                        'Receiver Address': action['NftItemTransfer']['recipient']['address'],
                                                        'NFT Address': action['NftItemTransfer']['nft'],
                                                        'Imagelink': nftdata['url'], 
                                                        'NFT Name': nftdata['name']
                                                    }
                            return transaction_info2
                # print(action)
                # print('---------------')
                if len(transdata['actions']) >= 3:
                    
                    if 'JettonTransfer' in action or 'SmartContractExec' in action or 'TonTransfer' in action:
                        if action['type'] == 'JettonTransfer':

                            
                                # print(action)
                                # print('---------------')
                                if transdata['account']['address'] == action['JettonTransfer']['sender']['address']:
                                    transtype = 'Sent Token Swap'
                                elif transdata['account']['address'] == action['JettonTransfer']['recipient']['address']:
                                    transtype = 'Received Token Swap'
                                
                                
                                transaction_info['TXid'] = transdata['event_id']
                                transaction_info['Transaction Type'] = transtype
                                transaction_info['Address'] = transdata['account']['address']
                                transaction_info['Amount token'] = action['JettonTransfer']['amount']
                                transaction_info['Token Name'] = action['JettonTransfer']['jetton']['symbol']
                                transaction_info['Token Address'] = action['JettonTransfer']['jetton']['address']
                                # print(action)      
                        if action['type'] == 'TonTransfer':

                            
                                # print(action)
                                # print('---------------')
                                if transdata['account']['address'] == action['TonTransfer']['sender']['address']:
                                    transtype = 'Sent TON Swap'
                                elif transdata['account']['address'] == action['TonTransfer']['recipient']['address']:
                                    transtype = 'Received TON Swap'
                                
                                transaction_info['TXid'] = transdata['event_id']
                                transaction_info['Transaction Type'] = transtype
                                transaction_info['Address'] = transdata['account']['address']
                                transaction_info['Amount Ton'] = action['TonTransfer']['amount']
                                transaction_info['Token Name 2'] = 'TON'

                        if action['type'] == 'SmartContractExec':
                                transaction_info['Amount Ton'] = action['SmartContractExec']['ton_attached']
                                transaction_info['Operation'] = action['SmartContractExec']['operation']
                                # return transaction_info
                if len(transdata['actions']) == 2:
                    
                    if 'JettonTransfer' in action or 'SmartContractExec' in action or 'TonTransfer' in action:
                        if action['type'] == 'JettonTransfer':

                            
                                # print(action)
                                # print('---------------')
                                if transdata['account']['address'] == action['JettonTransfer']['sender']['address']:
                                    transtype = 'Sent Token Swap'
                                elif transdata['account']['address'] == action['JettonTransfer']['recipient']['address']:
                                    transtype = 'Received Token Swap'
                                
                                
                                transaction_info['TXid'] = transdata['event_id']
                                transaction_info['Transaction Type'] = transtype
                                transaction_info['Address'] = transdata['account']['address']
                                transaction_info['Amount token'] = action['JettonTransfer']['amount']
                                transaction_info['Token Name'] = action['JettonTransfer']['jetton']['symbol']
                                transaction_info['Token Address'] = action['JettonTransfer']['jetton']['address']
                                # print(action)      
                        if action['type'] == 'TonTransfer':

                            
                                print(action)
                                # print('---------------')
                                if transdata['account']['address'] == action['TonTransfer']['sender']['address']:
                                    transtype = 'Sent TON Swap'
                                elif transdata['account']['address'] == action['TonTransfer']['recipient']['address']:
                                    transtype = 'Received TON Swap'
                                
                                transaction_info['TXid'] = transdata['event_id']
                                transaction_info['Transaction Type'] = transtype
                                transaction_info['Address'] = transdata['account']['address']
                                transaction_info['Amount Ton'] = action['TonTransfer']['amount']
                                transaction_info['Token Name 2'] = 'TON'

                        if action['type'] == 'SmartContractExec':
                                transaction_info['Amount Ton'] = action['SmartContractExec']['ton_attached']
                                transaction_info['Operation'] = action['SmartContractExec']['operation']
                        #                  
                        # return
                            
                elif len(transdata['actions']) == 1:
                    if action['type'] == 'JettonSwap':
                        #  print(action['JettonSwap'])
                         if 'JettonSwap' in action:
                            # print(action)
                            # print('---------------')
                            if 'ton_in' in action['JettonSwap']:
                                transtype = 'Sent Token Swap'
                                amountton =action['JettonSwap']['ton_in']
                                amounttoken= action['JettonSwap']['amount_out']
                                tokendata= action['JettonSwap']['jetton_master_out']
                            elif 'ton_out' in action['JettonSwap']:
                                transtype = 'Received Token Swap'
                                amountton =action['JettonSwap']['ton_out']
                                amounttoken= action['JettonSwap']['amount_in']
                                tokendata= action['JettonSwap']['jetton_master_in']
                            
                            transaction_info = {
                                                    'TXid': transdata['event_id'],
                                                    'Transaction Type': transtype,
                                                    'Address': transdata['account']['address'],
                                                    'Amount token': amounttoken,
                                                    'Token Name': tokendata['symbol'],
                                                    'Token Address': tokendata['address'],
                                                    'Amount Ton' : amountton,
                                                     'Token Name 2': 'TON'
                                                }
                            return transaction_info
                    if action['type'] == 'JettonTransfer':

                        if 'JettonTransfer' in action:
                            # print(action)
                            # print('---------------')
                            if transdata['account']['address'] == action['JettonTransfer']['sender']['address']:
                                transtype = 'Sent Token'
                            elif transdata['account']['address'] == action['JettonTransfer']['recipient']['address']:
                                transtype = 'Received Token'
                            
                            
                            transaction_info = {
                                                    'TXid': transdata['event_id'],
                                                    'Transaction Type': transtype,
                                                    'Sender Address': action['JettonTransfer']['sender']['address'],
                                                    'Receiver Address': action['JettonTransfer']['recipient']['address'],
                                                    'Amount': action['JettonTransfer']['amount'],
                                                    'Token Name': action['JettonTransfer']['jetton']['symbol'],
                                                    'Token Address': action['JettonTransfer']['jetton']['address']
                                                }
                            return transaction_info
                    if action['type'] == 'TonTransfer':
                        if 'TonTransfer' in action:
                            # print(action)
                            # print('---------------')
                            if transdata['account']['address'] == action['TonTransfer']['sender']['address']:
                                transtype = 'Sent TON'
                            elif transdata['account']['address'] == action['TonTransfer']['recipient']['address']:
                                transtype = 'Received TON'
                            
                            
                            transaction_info = {
                                                    'TXid': transdata['event_id'],
                                                    'Transaction Type': transtype,
                                                    'Sender Address': action['TonTransfer']['sender']['address'],
                                                    'Receiver Address': action['TonTransfer']['recipient']['address'],
                                                    'Amount': action['TonTransfer']['amount'],
                                                    'Token Name 2': 'TON'
                                                }
                            return transaction_info
        return transaction_info
    else:
        print(f"Error: {response.status_code}") 
def trxDetails(trx_id):
    trx = str(trx_id)
    url = f'https://tonapi.io/v2/blockchain/transactions/{trx}'
    headers = {'Accept': 'application/json'}
    response = req.get(url, headers=headers)
    if response.status_code == 200:
        transdata = response.json()  
        # print(trx_id)
        print(transdata)
        outdecode = []
        indecode = ''
        type = ''
        nftadress = ''
        first_in_msg = transdata['in_msg']
        # Check if 'decoded_op_name' is in the first out-message
        if 'decoded_op_name' in first_in_msg:
            indecode= first_in_msg['decoded_op_name']
            print("Decoded in Operations Name:", indecode)
        else:
            print("Decoded Operation Name not found in the first in-message.")
        if 'out_msgs' in transdata and len(transdata['out_msgs']) > 0:
            # Access the first out-message (index 0)
            first_out_msg = transdata['out_msgs']
            for msg in first_out_msg:
                if 'decoded_op_name' in msg:
                    outdecode.append(msg['decoded_op_name'])
                
            print("Decoded out Operations Name:", outdecode)
        else:
            print("No out-messages found in the transaction data.")
        if  'nft_ownership_assigned' ==  str(indecode):  
            type = 'Recieved NFT'
            nftadress = transdata['in_msg']['destination']['address']
        elif 'nft_transfer' in outdecode and len(outdecode) == 1:
            type = 'Sent NFT'
            nftadress = transdata['out_msgs'][0]['destination']['address']


        link = f'https://tonviewer.com/{trx_id}'
        filteredData = {'TRX_hash': trx_id, 'explorer_link':link }
        return {'data':filteredData, 'type': type, 'nft':nftadress}
    elif response.status_code == 404:
        print("Transaction not found.")
    else:
        print(f"Error: {response.status_code}")
def Getpools(address):
     url = f'https://api.geckoterminal.com/api/v2/networks/ton/tokens/{address}/pools'
     headers = {'Accept': 'application/json'}
     response = req.get(url=url,headers=headers)
    #  print(response.json())
     data = response.json()
     if 'data' in data:
          
        return str(data['data'][0]['id']).strip('ton_')
# transaac = trxDetails('e1b28bc0af9c59fe66ea379da1a83a930124930662d3857a227a66bf68db1fe2')
# transaac = trxDetails('0363d9dfe1588917a2e80917cbbf724033b6c2e7cd58ec8886a9c4f6547563ee')
# print(transaac)
# print(transactionsEvent('0:7270a85fb946f9e4160d69af20588e8247ab68ff7dbac70f52cc4b30910ec194', '626de877da6780a217011fa6ce353ebed7e4536192c84a6eafda8c9bf90e0eb9'))
# print(Getpools('EQBZ_cafPyDr5KUTs0aNxh0ZTDhkpEZONmLJA2SNGlLm4Cko'))