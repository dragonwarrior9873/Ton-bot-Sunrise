import csv
import os
import aiofiles
from database_handler import userWalletsCheck
from telebot.async_telebot import asyncio_helper


async def updateSub(user_id, plan, ts):
    temp_filename = 'temp_subscriptions.csv'
    user_found = False

    try:
        # Reading the content of the original file asynchronously
        async with aiofiles.open('subscriptions.csv', mode='r', encoding='utf-8') as csvfile:
            content = await csvfile.read()
        
        rows = csv.reader(content.splitlines())
        updated_rows = []

        # Checking and updating rows or appending a new user
        for row in rows:
            if row[0] == str(user_id):
                row[1], row[2] = plan, str(ts)
                user_found = True
            updated_rows.append(row)
        
        if not user_found:
            updated_rows.append([user_id, plan, str(ts)])
        
        # Writing updates to the temporary file asynchronously
        async with aiofiles.open(temp_filename, mode='w', encoding='utf-8') as temp_file:
            for row in updated_rows:
                await temp_file.write(','.join(map(str, row)) + '\n')

        # Replacing the original file with the updated temporary file
        os.replace(temp_filename, 'subscriptions.csv')

    except Exception as e:
        print(f"Error updating subscription: {e}")
        if os.path.exists(temp_filename):
            os.remove(temp_filename)
async def readUserdata(user_id):
    try:
        with open('users.csv', mode="r", encoding="utf-8") as existing_csv:
            csv_reader = csv.reader(existing_csv)
            for row in csv_reader:
                if len(row) > 1:
                    if str(user_id) == str(row[0]):
                        return row
    except Exception as e:
        print(f"Error : {e}")
        return None
async def userSettings(user_id, enabling):
    users = []
    userdata = await readUserdata(user_id)
    newData = [str(user_id)]
    
    newData.append(not (userdata[1]== 'True') if 'charts' in enabling else (userdata[1]== 'True'))
    newData.append(not (userdata[2]== 'True') if 'dolarval' in enabling else (userdata[2]== 'True'))
    if enabling in ["eng", "fr", "pl", "ar","fa","be","rum","uzb","ua","ru","de","es","ja","zh"]:
        newData.extend([enabling,userdata[4],userdata[5],userdata[6],userdata[7],userdata[8],userdata[9]])
    else:
        newData.extend([userdata[3],userdata[4],userdata[5],userdata[6],userdata[7],userdata[8],userdata[9]])
    users.append(newData)
    try:
        with open('users.csv', mode="r", encoding="utf-8") as existing_csv:
            csv_reader = csv.reader(existing_csv)
            for row in csv_reader:

                if str(user_id) not in row:
                    users.append(row)
    except Exception as e:
        print(f"Error : {e}")
        return None
    try:
        with open('users.csv', mode="w", encoding="utf-8") as existing_csv:
            writer = csv.writer(existing_csv)
            for user in users:
                if len(user) > 1:
                    writer.writerow(user)
    except Exception as e:
        print(f"Error : {e}")
        return None
    return {'charts':newData[1],'dolarval':newData[2],'lang':newData[3]}
# userid, swap, nft, sent,recieved,referals,subscription, referee
async def create_user(user_id, referal,username):
    userdata =[user_id, True,True, 'eng',0,'free',referal,username,'free', True]
    await updateSub(user_id, 'free', 0)
    try:
        with open('users.csv', mode="a", encoding="utf-8") as existing_csv:
            writer = csv.writer(existing_csv)
            writer.writerow(userdata)
    except Exception as e:
        print(f"Error : {e}")
        return None
async def update_subscription_plan(user_id, new_subscription_plan, time):
    temp_filename = 'temp_users.csv'
    is_user_found = False
    
    try:
        with open('users.csv', mode="r", encoding="utf-8") as csvfile, open(temp_filename, mode="w", encoding="utf-8") as temp_file:
            reader = csv.reader(csvfile)
            writer = csv.writer(temp_file)
            
            for row in reader:
                if row[0] == str(user_id):
                    row[5] = new_subscription_plan  
                    row[8] = time
                    is_user_found = True
                writer.writerow(row)
                
       
        if is_user_found:
            os.replace(temp_filename, 'users.csv')
        else:
            os.remove(temp_filename)
            print(f"User {user_id} not found.")
    except Exception as e:
        print(f"Error : {e}")
        return None
def reverseHashReferal(referal, is_negative=False):
    alpha = 'ABCDEFGHIJ'
    alpha2 = 'KLMNOPQRST'
    # Create reverse mappings
    reverse_alpha = {char: str(index) for index, char in enumerate(alpha)}
    reverse_alpha2 = {char: str(index) for index, char in enumerate(alpha2)}
    
    user_id_str = ''
    # Choose the correct mapping based on the sign (assumed known)
    if not is_negative:
        for char in referal:
            user_id_str += reverse_alpha[char]
    else:
        user_id_str = '-'
        for char in referal:
            user_id_str += reverse_alpha2[char]
    
    return int(user_id_str)
async def update_balance(balance,user_id):
    temp_filename = 'temp_users.csv'
    is_user_found = False
    user = await readUserdata(user_id)
    userRef = user[6]
    if userRef == '':
         return
    elif userRef[0] in 'ABCDEFGHIJ':
        referee = reverseHashReferal(userRef)
    else: 
         referee = reverseHashReferal(userRef, is_negative=True)
    try:
        with open('users.csv', mode="r", encoding="utf-8") as csvfile, open(temp_filename, mode="w", encoding="utf-8") as temp_file:
            reader = csv.reader(csvfile)
            writer = csv.writer(temp_file)
            
            for row in reader:
                if row[0] == str(referee):
                    row[4] = float(row[4]) + balance
                    is_user_found = True
                writer.writerow(row)
                
       
        if is_user_found:
            os.replace(temp_filename, 'users.csv')
        else:
            os.remove(temp_filename)
            print(f"User {referee} not found.")
    except Exception as e:
        print(f"Error : {e}")
        return None
async def alertSub(bot, UserId, until):
    wallets = await userWalletsCheck(UserId)
    if until >1:
        try:
                            await bot.send_message(wallets[0][2], f'Alert Your Subscription End in {until} Days' , parse_mode='HTML')
        except asyncio_helper.ApiException as e:
                            if e.result.status_code in (400,401,403,404,429,500,502):
                                        print("message cant be sent")
                            else:
                                raise
    else:
        try:
                            await bot.send_message(wallets[0][2], f'Alert Your Subscription End in Today' , parse_mode='HTML')
        except asyncio_helper.ApiException as e:
                            if e.result.status_code in (400,401,403,404,429,500,502):
                                        print("message cant be sent")
                            else:
                                raise

async def getUserReferrals(referal):
    ref = hashReferal(referal)
    referrals = []
    try:
        with open('users.csv', mode="r", encoding="utf-8") as existing_csv:
            csv_reader = csv.reader(existing_csv)
            for row in csv_reader:
                if len(row) > 7:
                    if str(ref) == str(row[6]):
                        referrals.append(row)
            return referrals
    except Exception as e:
        print(f"Error : {e}")
        return None
def hashReferal(user_id):
    alpha = 'ABCDEFGHIJ'
    alpha2 = 'KLMNOPQRST'
    user_id_str = str(user_id)
    referal = ''
    if user_id_str[0] != '-':
        for i in user_id_str:
    
            # print(alpha[int(i)])
            referal += alpha[int(i)]
    else:
        for i in user_id_str[1:]:
            referal += alpha2[int(i)]
    return referal
def toggle_ads(user_id):
    modified_data = []  
    newRow = []
    with open('users.csv', 'r') as file:
        reader = csv.reader(file)
        for row in reader:
            if len(row) > 0:
                if row[0] == str(user_id):
                    # print('row[9] ',row[9])
                    row[9] = 'False' if row[9] == 'True' else 'True'
                    newRow = row
                modified_data.append(row)

    with open('users.csv', 'w', newline='') as file:
        writer = csv.writer(file)
        writer.writerows(modified_data)
    # print('yes')
    return newRow