import csv

async def saveWallet(wallet_id, user_id, chat_id,address):
    try:
        with open('wallets.csv', mode="a", encoding="utf-8") as file:
            writer = csv.writer(file)
            writer.writerow([wallet_id, user_id, chat_id,address,'Not Named', True, True,True,True])
    except Exception as e:
        print(f"Error : {e}")
    return wallet_id

async def userWalletsCheck(user_id):
    counter = []
    try:
        with open('wallets.csv', mode="r", encoding="utf-8") as existing_csv:
            csv_reader = csv.reader(existing_csv)
            for row in csv_reader:
                if str(user_id) in row:
                    counter.append(row)
    except Exception as e:
        print(f"Error : {e}")
        return None
    return counter
async def userWalletdata(user_id, wallet):
    try:
        with open('wallets.csv', mode="r", encoding="utf-8") as existing_csv:
            csv_reader = csv.reader(existing_csv)
            for row in csv_reader:
                if str(user_id) in row and str(wallet) in row:
                    return row
    except Exception as e:
        print(f"Error : {e}")
        return None
async def checkwalletofuser(user_id):
    wallets = []
    try:
        with open('wallets.csv', mode="r", encoding="utf-8") as existing_csv:
            csv_reader = csv.reader(existing_csv)
            
            for row in csv_reader:
                # print(row)
                if len(row) > 1:
                    if str(row[1]) == str(user_id):
                        wallets.append(row[0])
        return wallets
    except Exception as e:
        print(f"Error : {e}")
        return None

def readWallets():
    try:
        wallets = {}
        with open('wallets.csv', mode="r", encoding="utf-8") as existing_csv:
            csv_reader = csv.reader(existing_csv)
            for row in csv_reader:
                if len(row) == 9:
                    if row[3] not in wallets:
                            wallets[row[3]] = {'users': [], 'chats': [], 'address':row[0], 'tag': {}, 'notifications':{}}
                    wallets[row[3]]['users'].append(row[1])
                    wallets[row[3]]['chats'].append(row[2])
                    wallets[row[3]]['tag'][row[2]] = row[4]
                    wallets[row[3]]['notifications'][row[2]] = [row[5],row[6],row[7],row[8]]
        return wallets
    except Exception as e:
        print(f"Error : {e}")
        return None
async def removeWallet(wallet,user_id):
    try:
        wallets = []
        with open('wallets.csv', mode="r", encoding="utf-8") as existing_csv:
            csv_reader = csv.reader(existing_csv)
            for row in csv_reader:
                if len(row) == 9:
                    if row[0] != str(wallet) or row[1] != str(user_id):
                        wallets.append(row)
        with open('wallets.csv', mode="w", encoding="utf-8") as file:
            writer = csv.writer(file)
            writer.writerows(wallets)
    except Exception as e:
        print(f"Error : {e}")
        return None
async def AddWalletTag(wallet,user_id,tag):
    try:
        wallets = []
        with open('wallets.csv', mode="r", encoding="utf-8") as existing_csv:
            csv_reader = csv.reader(existing_csv)
            for row in csv_reader:
                if len(row) == 9:
                    if row[0] == str(wallet) and row[1] == str(user_id):
                        newTagged = [row[0], row[1], row[2], row[3], str(tag),row[5], row[6], row[7], row[8]]
                    if row[0] != str(wallet) or row[1] != str(user_id):
                        wallets.append(row)
            wallets.append(newTagged)
        with open('wallets.csv', mode="w", encoding="utf-8") as file:
            writer = csv.writer(file)
            writer.writerows(wallets)
    except Exception as e:
        print(f"Error : {e}")
        return None
async def walletnotifications(user_id, wallet, enabling):
    print(enabling)
    all =''
    userdata = await userWalletdata(user_id, wallet)
    if userdata:
        await removeWallet(wallet,user_id)
        newData = [userdata[0],userdata[1],userdata[2],userdata[3],userdata[4]]
        newData.append(not (userdata[5] == 'True') if 'swap' in enabling else (userdata[5] == 'True'))
        newData.append(not (userdata[6] == 'True') if 'nft' in enabling else (userdata[6] == 'True'))
        newData.append(not (userdata[7] == 'True') if 'sent' in enabling else (userdata[7] == 'True'))
        newData.append(not (userdata[8] == 'True') if 'recieved' in enabling else (userdata[8] == 'True'))
        try:
            with open('wallets.csv', mode="a", encoding="utf-8") as existing_csv:
                writer = csv.writer(existing_csv)
                writer.writerow(newData)
        except Exception as e:
            print(f"Error : {e}")
            return None
        return {'swap':str(newData[5]),'nft':str(newData[6]),'sent':str(newData[7]),'recieved':str(newData[8]), 'all':all}
    
# print(list(readWallets().keys()))
