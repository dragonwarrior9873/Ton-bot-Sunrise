import os
from telebot.async_telebot import AsyncTeleBot, types, asyncio_helper
# from telebot import util
import websockets
import json
import asyncio
import time
import math
import yaml
from dotenv import load_dotenv, find_dotenv

from wallet_data import walletverification, walletbalance, dolarPricing, formatexpchart
from database_handler import readWallets, userWalletsCheck, saveWallet, checkwalletofuser, removeWallet, AddWalletTag, \
    userWalletdata, walletnotifications
from formating import format_wallets, serialize_inline_keyboard
from userHandler import userSettings, readUserdata, create_user, update_subscription_plan, alertSub, updateSub, \
    update_balance, getUserReferrals, hashReferal, toggle_ads
from dataprocess import fetch_image, transactionsEvent, Getpools
from subscription import generate_payment_link, checkTransactions, livetonprice, getsubByUser, verifyTimestamp, \
    ReadAllplans
from candlestick import chart

import telegram
from telegram import ReplyKeyboardMarkup, KeyboardButton

# from test import transactionsNFT

load_dotenv(find_dotenv())
TELEKEY = os.getenv('API_KEY')
Hotwallets = os.getenv('Hotwallets')
bot = AsyncTeleBot(TELEKEY)


async def deleteMsg(bot, chat_id, msg_id):
    try:
        await bot.delete_message(chat_id, msg_id)
    except Exception as e:
        print(f"Failed to delete message : {e}")


@bot.message_handler(commands=['start'])
@bot.message_handler(func=lambda message: message.text == "𝐇𝐎𝐌𝐄")
async def start(message):
    referral_id = message.text.split()[1] if len(message.text.split()) > 1 else None
    user = await readUserdata(str(message.from_user.id))
    username = message.from_user.username
    if not user:
        await create_user(str(message.from_user.id), referral_id, username)
        file_path = 'languages/eng.yml'

        przycisk = types.ReplyKeyboardMarkup(row_width=1, resize_keyboard=True)
        menu = types.InlineKeyboardButton("𝐇𝐎𝐌𝐄")
        przycisk.row(menu)

        await bot.send_message(message.chat.id, '🪂', reply_markup=przycisk)
    else:
        if str(user[5]) != 'free':
            await verifyTimestamp(user[0])
        lang = user[3]
        file_path = f'languages/{lang}.yml'

    # Specify UTF-8 encoding when opening the file
    with open(file_path, 'r', encoding='utf-8') as file:
        language = yaml.safe_load(file)

    markup = types.InlineKeyboardMarkup()

    walletss = types.InlineKeyboardButton(f"💼 {language['Wallets']}", callback_data="Edit")
    markup.row(walletss)

    coin = types.InlineKeyboardButton(f"\U0001F4B0 {language['Coins']}", callback_data="coin")
    nfts = types.InlineKeyboardButton(f"🌅️ {language['NFTs']}", callback_data="nfts")
    markup.row(coin, nfts)

    Referals = types.InlineKeyboardButton(f"\U0001F465 {language['Referals']}", callback_data="ref")
    subscription = types.InlineKeyboardButton(f"\U0001F4B3 {language['Subscription']}", callback_data="sub")
    markup.row(Referals, subscription)

    faq = types.InlineKeyboardButton(f"📬 AD", callback_data="faq")
    settings = types.InlineKeyboardButton(f"\U00002699 {language['Settings']}", callback_data="setting")
    markup.row(faq, settings)

    msg = f" <b>{language['Welcome']} {username}!️ </b>"

    try:
        # await bot.send_message(message.chat.id, msg, reply_markup=markup, parse_mode='HTML')
        with open('logomsg.jpg', 'rb') as file:
            await bot.send_photo(message.chat.id, photo=file, caption=msg, reply_markup=markup, parse_mode='HTML')
    except asyncio_helper.ApiException as e:
        print(e)
        if e.result.status_code in (400, 401, 403, 404, 429, 500, 502):
            print("Message can't be sent")
        else:
            raise


# @bot.message_handler(commands=['start2'])
# async def start(message):
#     # if message.chat.type == 'private':
#         referral_id = message.text.split()[1] if len(message.text.split())> 1 else None
#         user = await readUserdata(str(message.from_user.id))
#         username = message.from_user.first_name
#         if not user:
#                await create_user(str(message.from_user.id), referral_id)
#         else:
#                 if str(user[5]) != 'free':
#                        await verifyTimestamp(user[0])
#         markup = types.InlineKeyboardMarkup()
#         stars1 = types.InlineKeyboardButton("⭐⭐⭐⭐⭐⭐", callback_data="star")
#         markup.row(stars1)
#         naame = types.InlineKeyboardButton(f"Welcome {username}!", callback_data="nae")
#         markup.row(naame)
#         stars2 = types.InlineKeyboardButton("⭐⭐⭐⭐⭐⭐", callback_data="star")
#         markup.row(stars2)
#         walletss = types.InlineKeyboardButton("💼 Wallets", callback_data="Edit")
#         markup.row(walletss)
#         coin = types.InlineKeyboardButton("\U0001F4B0 Coins", callback_data="coin")
#         nfts = types.InlineKeyboardButton("🌅️ NFTs", callback_data="nfts")
#         markup.row(coin, nfts)

#         Referals = types.InlineKeyboardButton("\U0001F465 Referals", callback_data="ref")
#         subscription = types.InlineKeyboardButton("\U0001F4B3 Subscription", callback_data="sub")
#         markup.row(Referals, subscription)
#         faq = types.InlineKeyboardButton("\U00002753 FAQ", url="https://t.me/c/1874312718/31")
#         settings = types.InlineKeyboardButton("\U00002699 Settings", callback_data="setting")
#         markup.row(faq, settings)
#         msg = "🤖"
#         try:
#             await bot.send_message(message.chat.id, msg, reply_markup=markup, parse_mode='HTML')
#         except asyncio_helper.ApiException as e:
#                     if e.result.status_code in (400,401,403,404,429,500,502):
#                                 print("message cant be sent")
#                     else:
#                         raise


# else:
# try:
#     await bot.send_message(message.chat.id, "This command is not supported in group chats.")
# except asyncio_helper.ApiException as e:
#             if e.result.status_code in (400,401,403,404,429,500,502):
#                         print("message cant be sent")
#             else:
#                 raise
is_wallet_processed = False
is_tag_processed = False
is_awaiting_wallet_name = False


@bot.callback_query_handler(func=lambda call: True)
async def handle_button_click(call):
    global is_wallet_processed, is_tag_processed
    user = await readUserdata(str(call.from_user.id))
    subplan = user[5]
    print(subplan)
    username = call.from_user.username

    if not user:
        await create_user(str(call.from_user.id), '', username)
    else:
        if str(user[5]) != 'free':
            userupdated = await verifyTimestamp(user[0])
            if userupdated:
                subplan = 'free'

    wallets = await userWalletsCheck(str(call.from_user.id))
    userWallets = await checkwalletofuser(str(call.from_user.id))
    langflag = {'ar': '🇸🇦', "be": '🇧🇾', "de": "🇩🇪", 'eng': '🇬🇧', "es": "🇪🇸", "fa": '🇮🇷', 'fr': '🇫🇷', "ja": "🇯🇵",
                'pl': '🇵🇱', "ru": '🇷🇺', "rum": '🇷🇴',
                "ua": '🇺🇦', "uzb": '🇺🇿', "zh": "🇨🇳"}

    print(user)
    if subplan.upper() == 'STANDARD':
        allowedwallets = 50
        allowedcoins = 30
        allowednfts = 12
        allowedmsgperh = 150
    elif subplan.upper() == 'PREMIUM':
        allowedwallets = 250
        allowedcoins = 250
        allowednfts = 250
        allowedmsgperh = 500
    elif subplan.upper() == 'PRO':
        allowedwallets = 1000
        allowedcoins = 1000
        allowednfts = 1000
        allowedmsgperh = 1000
    else:
        until = '♾️'
        allowedwallets = 7
        allowedcoins = 5
        allowednfts = 2
        allowedmsgperh = 10
    if not user:
        await create_user(str(call.from_user.id), '')
        file_path = 'languages/eng.yml'
    else:
        if str(user[5]) != 'free':
            await verifyTimestamp(user[0])
        lang = user[3]
        file_path = f'languages/{lang}.yml'
    with open(file_path, 'r', encoding='utf-8') as file:
        language = yaml.safe_load(file)
    if call.data in ['coin', 'nfts']:
        try:
            await bot.send_message(call.message.chat.id, "🌒 SOON❗")
        except asyncio_helper.ApiException as e:
            if e.result.status_code in (400, 401, 403, 404, 429, 500, 502):
                print("message cant be sent")
            else:
                raise

    if call.data == "Add":
        if len(userWallets) < allowedwallets:
            is_wallet_processed = False
            try:
                await bot.send_message(call.message.chat.id, language["Send Wallet Address"], parse_mode='HTML')
            except asyncio_helper.ApiException as e:
                if e.result.status_code in (400, 401, 403, 404, 429, 500, 502):
                    print("message cant be sent")
                else:
                    raise

            @bot.message_handler(func=lambda message: True and not is_wallet_processed, content_types=["text"])
            async def saveWallets(message):
                global is_wallet_processed, is_awaiting_wallet_name
                #   print(message.text)
                if str(message.text).lower() == 'exit':
                    is_wallet_processed = True
                else:
                    if not is_awaiting_wallet_name:
                        print(str(message.text))
                        walletcheck = walletverification(str(message.text))
                        # print(walletcheck)
                        if walletcheck:
                            # print(message.from_user.id)

                            # print(userWallets)
                            if not userWallets or (str(message.text) not in userWallets):

                                walletmsg = f'\U00002705 {language["Wallet Saved Successfully"]}! {language["Send A Name! (20 Characters Max)"]}'
                                try:
                                    await bot.send_message(message.chat.id, walletmsg, parse_mode='HTML')
                                except asyncio_helper.ApiException as e:
                                    if e.result.status_code in (400, 401, 403, 404, 429, 500, 502):
                                        print("message cant be sent")
                                    else:
                                        raise
                                await saveWallet(str(message.text), str(message.from_user.id), str(message.chat.id),
                                                 str(walletcheck['address']))

                                is_awaiting_wallet_name = True
                            else:
                                walletdataa = await userWalletdata(str(message.from_user.id), str(message.text))
                                msssg = str(walletdataa[4]) + ' ' + str(language[
                                                                            "This Wallet Is Already Being Tracked By this User! Send Another One Or Type Exit"]).split(
                                    '!')[0] + '! '
                                try:
                                    await bot.send_message(message.chat.id, msssg)
                                except asyncio_helper.ApiException as e:
                                    if e.result.status_code in (400, 401, 403, 404, 429, 500, 502):
                                        print("message cant be sent")
                                    else:
                                        raise
                        else:
                            try:
                                await bot.send_message(message.chat.id, language[
                                    "This Address Is Not Associated With Any Wallet On Ton Network! Try Another One"])
                            except asyncio_helper.ApiException as e:
                                if e.result.status_code in (400, 401, 403, 404, 429, 500, 502):
                                    print("message cant be sent")
                                else:
                                    raise
                    else:
                        if len(message.text) < 21:
                            wallet = await checkwalletofuser(str(message.from_user.id))
                            await AddWalletTag(str(wallet[-1]), str(message.from_user.id), str(message.text))
                            mssg = language['The wallet name has been set to'] + ' <b>' + str(message.text) + '</b>'
                            try:
                                await bot.send_message(call.message.chat.id, mssg, parse_mode='HTML')
                            except asyncio_helper.ApiException as e:
                                if e.result.status_code in (400, 401, 403, 404, 429, 500, 502):
                                    print("message cant be sent")
                                else:
                                    raise
                            is_wallet_processed = True
                            is_awaiting_wallet_name = False
                            markup1 = types.InlineKeyboardMarkup()
                            wallets = await userWalletsCheck(str(call.from_user.id))
                            if not wallets:

                                msg = f"<b>{language['You Have No Saved Wallets']}</b>"
                                Add = types.InlineKeyboardButton(f"➕ {language['Add']}", callback_data="Add")
                                markup1.add(Add)
                                Back = types.InlineKeyboardButton(f"🔙 {language['Back']}",
                                                                  callback_data="back")
                                markup1.add(Back)

                                try:
                                    await bot.edit_message_text(chat_id=call.message.chat.id,
                                                                message_id=call.message.message_id,
                                                                text=msg,
                                                                reply_markup=markup1,
                                                                parse_mode='HTML')
                                except asyncio_helper.ApiException as e:
                                    if e.result.status_code in (400, 401, 403, 404, 429, 500, 502):
                                        print("message cant be sent")
                                    else:
                                        raise
                            else:
                                if len(wallets) < 8:

                                    for wallet in wallets:
                                        # if str(wallet[0]) == str(walleti):
                                        #         continue
                                        if wallet[4] == 'Not Named':
                                            wal = types.InlineKeyboardButton(wallet[0], callback_data=wallet[0])
                                            markup1.row(wal)
                                        else:
                                            wlmsg = str(wallet[4])
                                            wal = types.InlineKeyboardButton(wlmsg, callback_data=wallet[0])
                                            markup1.row(wal)
                                else:

                                    for i in range(0, 7):

                                        if wallets[i][4] == 'notag':
                                            wal = types.InlineKeyboardButton(wallets[i][0], callback_data=wallets[i][0])
                                            markup1.row(wal)

                                        else:

                                            wlmsg = str(wallets[i][4])
                                            wal = types.InlineKeyboardButton(wlmsg, callback_data=wallets[i][0])
                                            markup1.row(wal)

                                    current = types.InlineKeyboardButton("O", callback_data="0")
                                    Nextpage = types.InlineKeyboardButton(">>", callback_data="next")
                                    markup1.row(current, Nextpage)
                                msg = f"<b>{language['Choose Saved Wallet']}</b>"
                                Add = types.InlineKeyboardButton(f"➕ {language['Add']}", callback_data="Add")
                                markup1.add(Add)
                                Back = types.InlineKeyboardButton(f"🔙 {language['Back']}",
                                                                  callback_data="back")
                                markup1.add(Back)
                                # await deleteMsg(bot, call.message.chat.id, call.message.message_id)
                                try:
                                    await bot.send_message(chat_id=call.message.chat.id,
                                                           text=msg,
                                                           reply_markup=markup1,
                                                           parse_mode='HTML')
                                except asyncio_helper.ApiException as e:
                                    if e.result.status_code in (400, 401, 403, 404, 429, 500, 502):
                                        print("message cant be sent")
                                    else:
                                        raise
                        else:
                            try:
                                await bot.send_message(call.message.chat.id, language[
                                    'Tag Exceeded Maximum Length Of 20 Characters! Try Another One'], parse_mode='HTML')
                            except asyncio_helper.ApiException as e:
                                if e.result.status_code in (400, 401, 403, 404, 429, 500, 502):
                                    print("message cant be sent")
                                else:
                                    raise


        else:
            markup = types.InlineKeyboardMarkup()
            subscription = types.InlineKeyboardButton(f"\U0001F4B3 {language['Change Plan']}", callback_data="sub")
            markup.row(subscription)
            try:
                await bot.send_message(call.message.chat.id,
                                       language["You Reached The Maximum Number of Wallets of Your Subscription Plan"],
                                       reply_markup=markup)
            except asyncio_helper.ApiException as e:
                if e.result.status_code in (400, 401, 403, 404, 429, 500, 502):
                    print("message cant be sent")
                else:
                    raise
    elif call.data == "Edit":
        markup1 = types.InlineKeyboardMarkup()

        if not wallets:

            msg = f'<b>{language["You Have No Saved Wallets"]}</b>'
            Add = types.InlineKeyboardButton(f"➕ {language['Add']}", callback_data="Add")
            markup1.row(Add)
            Back = types.InlineKeyboardButton(f"🔙 {language['Back']}", callback_data="back")
            markup1.row(Back)
            # await deleteMsg(bot, call.message.chat.id, call.message.message_id)
            try:
                await bot.send_message(chat_id=call.message.chat.id,
                                       text=msg,
                                       reply_markup=markup1,
                                       parse_mode='HTML')
            except asyncio_helper.ApiException as e:
                if e.result.status_code in (400, 401, 403, 404, 429, 500, 502):
                    print("message cant be sent")
                else:
                    raise
        else:
            if len(wallets) < 8:

                for wallet in wallets:
                    # print(wallet)
                    if wallet[4] == 'Not Named':
                        wal = types.InlineKeyboardButton(wallet[0], callback_data=wallet[0])
                        markup1.row(wal)
                    else:
                        # + ':  ' + str(format_wallets(wallet[0]))
                        wlmsg = str(wallet[4])
                        # print(wallet[0])
                        wal = types.InlineKeyboardButton(wlmsg, callback_data=wallet[0])
                        markup1.row(wal)
            else:
                for i in range(0, 7):
                    if wallets[i][4] == 'notag':
                        wal = types.InlineKeyboardButton(wallets[i][0], callback_data=wallets[i][0])
                        markup1.row(wal)
                    else:
                        wlmsg = str(wallets[i][4])
                        wal = types.InlineKeyboardButton(wlmsg, callback_data=wallets[i][0])
                        markup1.row(wal)
                current = types.InlineKeyboardButton("O", callback_data="0")
                Nextpage = types.InlineKeyboardButton(">>", callback_data="next")
                markup1.row(current, Nextpage)
            msg = f"<b>{language['Choose Saved Wallet']}</b>"
            Adds = types.InlineKeyboardButton(f"➕ {language['Add']}", callback_data="Add")
            markup1.row(Adds)
            Back = types.InlineKeyboardButton(f"🔙 {language['Back']}", callback_data="back")
            markup1.row(Back)
            # print(call.message.message_id)
            # await deleteMsg(bot, call.message.chat.id, call.message.message_id)
            try:
                await bot.send_message(chat_id=call.message.chat.id,
                                       text=msg,
                                       reply_markup=markup1,
                                       parse_mode='HTML')
            except asyncio_helper.ApiException as e:
                if e.result.status_code in (400, 401, 403, 404, 429, 500, 502):
                    print("message cant be sent")
                else:
                    raise
    elif call.data in userWallets:
        walletDATa = await userWalletdata(str(call.from_user.id), str(call.data))
        emojis = []

        # print(len(walletDATa))

        if 'False' in walletDATa:
            for i in range(5, 9):
                if walletDATa[i] == 'False':
                    emojis.append('')
                elif walletDATa[i] == 'True':
                    emojis.append('\U00002705')
        else:
            emojis.extend(['\U00002705'] * 4)

        wallet = str(call.data)
        markup7 = types.InlineKeyboardMarkup()
        wals = types.InlineKeyboardButton(str(walletDATa[4]), url=f"https://tonviewer.com/{wallet}")
        markup7.row(wals)
        sentfrom = types.InlineKeyboardButton(f"{emojis[2]} {language['Transfers In']}", callback_data="received")
        sento = types.InlineKeyboardButton(f"{emojis[3]} {language['Transfers Out']}", callback_data="sent")
        markup7.row(sentfrom, sento)
        swap = types.InlineKeyboardButton(f"{emojis[0]} {language['Swap']}", callback_data="swap")
        nft = types.InlineKeyboardButton(f"{emojis[1]} {language['NFT']}", callback_data="nft")
        markup7.row(swap, nft)
        balanc = types.InlineKeyboardButton(f"🔍 {language['Balance']}", callback_data="balance")
        markup7.row(balanc)
        tag = types.InlineKeyboardButton(f"\U0001F3F7 {language['Rename']}", callback_data="tag")
        remove = types.InlineKeyboardButton(f"\U00002716 {language['Delete']}", callback_data="remove")
        markup7.row(tag, remove)
        back = types.InlineKeyboardButton(f"🔙 {language['Back']}", callback_data="back")
        markup7.row(back)
        msg = f"<b>{language['Wallet Details']}</b>"

        try:
            await bot.edit_message_text(chat_id=call.message.chat.id,
                                        message_id=call.message.message_id,
                                        text=msg,
                                        reply_markup=markup7,
                                        parse_mode='HTML')
        except asyncio_helper.ApiException as e:
            if e.result.status_code in (400, 401, 403, 404, 429, 500, 502):
                print("message cant be sent")
            else:
                raise

    elif call.data == 'balance':
        for row in call.message.reply_markup.keyboard:
            for button in row:
                url = getattr(button, 'url', None)
                if url:
                    break
            if url:
                break
        wallet = url.replace("https://tonviewer.com/", "")
        # print(wallet)
        walletcheck = walletverification(str(wallet))
        dolarval = user[2]
        if str(dolarval).lower() == 'false':
            walletjettons = walletbalance(str(wallet), False)
        else:
            walletjettons, tonprice = walletbalance(str(wallet), True)
        if walletcheck:
            if str(dolarval).lower() == 'false':
                msgbalance = f"<b>{language['Wallet Balance']}</b>: \n🪙 " + str(
                    int(round(float(walletcheck['balance']), 0))) + ' TON'
            else:

                amount = round(float(walletcheck['balance']), 0) * float(tonprice)
                amountformated = formatexpchart(amount)
                msgbalance = f"🔍 <b>{language['Wallet Balance']}</b>: \n‎\n🪙 " + str(
                    int(round(float(walletcheck['balance']), 0))) + ' TON' + ' (' + str(amountformated) + '$)'

            if len(walletjettons) > 9:
                jettons = walletjettons[:9]
            else:
                jettons = walletjettons
            print(jettons)
            for jetton in jettons:

                if str(dolarval).lower() == 'false':
                    msgbalance += "\n🪙 " + str(jetton['Balance']) + ' <a href="https://tonviewer.com/' + jetton[
                        'Token Address'] + '">' + str(jetton['Token Name']) + '</a>'
                else:

                    if float(jetton['Dolarval']) > 0:
                        msgbalance += "\n🪙 " + str(jetton['Balance']) + ' <a href="https://tonviewer.com/' + jetton[
                            'Token Address'] + '">' + str(jetton['Token Name']) + '</a>' + ' (' + str(
                            formatexpchart(float(jetton['Dolarval']))) + '$)'
                    else:
                        msgbalance += "\n🪙 " + str(jetton['Balance']) + ' <a href="https://tonviewer.com/' + jetton[
                            'Token Address'] + '">' + str(jetton['Token Name']) + '</a>' + ' (Not Available)'
            try:
                await bot.send_message(call.message.chat.id, msgbalance, parse_mode='HTML',
                                       disable_web_page_preview=True)
            except asyncio_helper.ApiException as e:
                if e.result.status_code in (400, 401, 403, 404, 429, 500, 502):
                    print("message cant be sent")
                else:
                    raise
    elif call.data == 'remove':
        for row in call.message.reply_markup.keyboard:
            for button in row:
                url = getattr(button, 'url', None)
                if url:
                    break
            if url:
                break
        walleti = url.replace("https://tonviewer.com/", "")
        await removeWallet(walleti, call.from_user.id)

        try:
            await bot.send_message(call.message.chat.id, language['Wallet Removed'], parse_mode='HTML')
        except asyncio_helper.ApiException as e:
            if e.result.status_code in (400, 401, 403, 404, 429, 500, 502):
                print("message cant be sent")
            else:
                raise
        markup1 = types.InlineKeyboardMarkup()

        if not wallets:

            msg = f"<b>{language['You Have No Saved Wallets']}</b>"
            Add = types.InlineKeyboardButton(f"➕ {language['Add']}", callback_data="Add")
            markup1.add(Add)
            Back = types.InlineKeyboardButton(f"🔙 {language['Back']}", callback_data="back")
            markup1.add(Back)

            try:
                await bot.edit_message_text(chat_id=call.message.chat.id,
                                            message_id=call.message.message_id,
                                            text=msg,
                                            reply_markup=markup1,
                                            parse_mode='HTML')
            except asyncio_helper.ApiException as e:
                if e.result.status_code in (400, 401, 403, 404, 429, 500, 502):
                    print("message cant be sent")
                else:
                    raise
        else:
            if len(wallets) < 8:

                for wallet in wallets:
                    if str(wallet[0]) == str(walleti):
                        continue
                    if wallet[4] == 'Not Named':
                        wal = types.InlineKeyboardButton(wallet[0], callback_data=wallet[0])
                        markup1.row(wal)
                    else:
                        wlmsg = str(wallet[4])
                        wal = types.InlineKeyboardButton(wlmsg, callback_data=wallet[0])
                        markup1.row(wal)
            else:

                for i in range(0, 7):

                    if wallets[i][4] == 'notag':
                        wal = types.InlineKeyboardButton(wallets[i][0], callback_data=wallets[i][0])
                        markup1.row(wal)

                    else:

                        # wlmsg = str(wallets[i][4]) + ':  ' + str(format_wallets(wallets[i][0]))
                        wal = types.InlineKeyboardButton(str(wallets[i][4]), callback_data=wallets[i][0])
                        markup1.row(wal)

                current = types.InlineKeyboardButton("O", callback_data="0")
                Nextpage = types.InlineKeyboardButton(">>", callback_data="next")
                markup1.row(current, Nextpage)
            msg = f"<b>{language['Choose Saved Wallet']}</b>"
            Add = types.InlineKeyboardButton(f"➕ {language['Add']}", callback_data="Add")
            markup1.add(Add)
            Back = types.InlineKeyboardButton(f"🔙 {language['Back']}", callback_data="back")
            markup1.add(Back)
            try:
                await bot.edit_message_text(chat_id=call.message.chat.id,
                                            message_id=call.message.message_id,
                                            text=msg,
                                            reply_markup=markup1,
                                            parse_mode='HTML')
            except asyncio_helper.ApiException as e:
                if e.result.status_code in (400, 401, 403, 404, 429, 500, 502):
                    print("message cant be sent")
                else:
                    raise
    elif call.data == 'next':
        markup1 = types.InlineKeyboardMarkup()
        if (len(wallets) - 8) < 8:

            for i in range(7, len(wallets)):
                if wallets[4] == 'Not Named':
                    wal = types.InlineKeyboardButton(wallets[i][0], callback_data=wallets[i][0])
                    markup1.row(wal)
                else:
                    wlmsg = str(wallets[i][4])
                    wal = types.InlineKeyboardButton(wlmsg, callback_data=wallets[i][0])
                    markup1.row(wal)
            current = types.InlineKeyboardButton("<<", callback_data="previous")
            Nextpage = types.InlineKeyboardButton("O", callback_data="0")
            markup1.row(current, Nextpage)
        else:

            for i in range(7, 16):

                if wallets[i][4] == 'notag':
                    wal = types.InlineKeyboardButton(wallets[i][0], callback_data=wallets[i][0])
                    markup1.row(wal)

                else:

                    # wlmsg = str(wallets[i][4]) + ':  ' + str(format_wallets(wallets[i][0]))
                    wal = types.InlineKeyboardButton(str(wallets[i][4]), callback_data=wallets[i][0])
                    markup1.row(wal)

            current = types.InlineKeyboardButton("<<", callback_data="previous")
            Nextpage = types.InlineKeyboardButton(">>", callback_data="nextnext")
            markup1.row(current, Nextpage)
        msg = f"<b>{language['Choose Saved Wallet']}</b>"
        Add = types.InlineKeyboardButton(f"➕ {language['Add']}", callback_data="Add")
        markup1.add(Add)
        Back = types.InlineKeyboardButton(f"🔙 {language['Back']}", callback_data="back")
        markup1.add(Back)
        try:
            await bot.edit_message_text(chat_id=call.message.chat.id,
                                        message_id=call.message.message_id,
                                        text=msg,
                                        reply_markup=markup1,
                                        parse_mode='HTML')
        except asyncio_helper.ApiException as e:
            if e.result.status_code in (400, 401, 403, 404, 429, 500, 502):
                print("message cant be sent")
            else:
                raise

    elif call.data == "previous":
        markup1 = types.InlineKeyboardMarkup()
        if len(wallets) < 8:

            for wallet in wallets:
                if wallet[4] == 'Not Named':
                    wal = types.InlineKeyboardButton(wallet[0], callback_data=wallet[0])
                    markup1.row(wal)
                else:
                    wlmsg = str(wallet[4])
                    wal = types.InlineKeyboardButton(wlmsg, callback_data=wallet[0])
                    markup1.row(wal)
        else:
            for i in range(0, 7):

                if wallets[i][4] == 'notag':
                    wal = types.InlineKeyboardButton(wallets[i][0], callback_data=wallets[i][0])
                    markup1.row(wal)

                else:

                    # wlmsg = str(wallets[i][4]) + ':  ' + str(format_wallets(wallets[i][0]))
                    wal = types.InlineKeyboardButton(str(wallets[i][4]), callback_data=wallets[i][0])
                    markup1.row(wal)

            current = types.InlineKeyboardButton("O", callback_data="0")
            Nextpage = types.InlineKeyboardButton(">>", callback_data="next")
            markup1.row(current, Nextpage)
        msg = f"<b>{language['Choose Saved Wallet']}</b>"
        Add = types.InlineKeyboardButton(f"➕ {language['Add']}", callback_data="Add")
        markup1.add(Add)
        Back = types.InlineKeyboardButton(f"🔙 {language['Back']}", callback_data="back")
        markup1.add(Back)
        try:
            await bot.edit_message_text(chat_id=call.message.chat.id,
                                        message_id=call.message.message_id,
                                        text=msg,
                                        reply_markup=markup1,
                                        parse_mode='HTML')
        except asyncio_helper.ApiException as e:
            if e.result.status_code in (400, 401, 403, 404, 429, 500, 502):
                print("message cant be sent")
            else:
                raise
    elif call.data == 'tag':
        for row in call.message.reply_markup.keyboard:
            for button in row:
                url = getattr(button, 'url', None)
                if url:
                    break
            if url:
                break
        wallet = url.replace("https://tonviewer.com/", "")
        is_tag_processed = False
        try:
            await bot.send_message(call.message.chat.id, language['Send A Name! (20 Characters Max)'],
                                   parse_mode='HTML')
        except asyncio_helper.ApiException as e:
            if e.result.status_code in (400, 401, 403, 404, 429, 500, 502):
                print("message cant be sent")
            else:
                raise

        @bot.message_handler(func=lambda message: True and not is_tag_processed, content_types=["text"])
        async def SaveTag(message):
            global is_tag_processed
            if str(call.from_user.id) == str(message.from_user.id):
                if len(message.text) < 21:
                    await AddWalletTag(str(wallet), str(message.from_user.id), str(message.text))
                    mssg = language['The wallet name has been set to'] + ' <b>' + str(message.text) + '</b>'
                    try:
                        await bot.send_message(call.message.chat.id, mssg, parse_mode='HTML')
                    except asyncio_helper.ApiException as e:
                        if e.result.status_code in (400, 401, 403, 404, 429, 500, 502):
                            print("message cant be sent")
                        else:
                            raise
                    is_tag_processed = True
                else:
                    try:
                        await bot.send_message(call.message.chat.id, language[
                            'Tag Exceeded Maximum Length Of 20 Characters! Try Another One'], parse_mode='HTML')
                    except asyncio_helper.ApiException as e:
                        if e.result.status_code in (400, 401, 403, 404, 429, 500, 502):
                            print("message cant be sent")
                        else:
                            raise

    elif 'back' in call.data:
        text_conditions = [
            language['Choose Saved Wallet'] in call.message.text,
            language['Your Settings'] in call.message.text,
            language['Your Referrals'] in call.message.text,
            language['You Have No Saved Wallets'] in call.message.text,
            language['Subscription'] in call.message.text,
            'Banner' in call.message.text
        ]
        if any(text_conditions):
            username = str(call.from_user.first_name)
            markup2 = types.InlineKeyboardMarkup()
            walletss = types.InlineKeyboardButton(f"💼 {language['Wallets']}", callback_data="Edit")
            markup2.row(walletss)
            coin = types.InlineKeyboardButton(f"\U0001F4B0 {language['Coins']}", callback_data="coin")
            nfts = types.InlineKeyboardButton(f"🌅️ {language['NFTs']}", callback_data="nfts")
            markup2.row(coin, nfts)

            Referals = types.InlineKeyboardButton(f"\U0001F465 {language['Referals']}", callback_data="ref")
            subscription = types.InlineKeyboardButton(f"\U0001F4B3 {language['Subscription']}", callback_data="sub")
            markup2.row(Referals, subscription)
            faq = types.InlineKeyboardButton(f"📬 AD", callback_data="faq")
            settings = types.InlineKeyboardButton(f"⚙️ {language['Settings']}", callback_data="setting")
            # settings = types.InlineKeyboardButton(f"\U00002699 {language['Settings']}", callback_data="setting")
            markup2.row(faq, settings)
            msg = f" <b>{language['Welcome']} {username}!️ </b>"
            # msg = f"\n ⭐⭐⭐⭐⭐⭐\n \n <b>{language['Welcome']} {username}!</b> \n \n⭐⭐⭐⭐⭐⭐ \n "

            # try:
            #     await bot.edit_message_text(chat_id=call.message.chat.id,
            #                                         message_id=call.message.message_id,
            #                                         text=msg,
            #                                         reply_markup=markup2,
            #                                         parse_mode='HTML')
            # except asyncio_helper.ApiException as e:
            #     if e.result.status_code in (400,401,403,404,429,500,502):
            #         print("message cant be sent")
            #     else:
            #         raise
            # await deleteMsg(bot, call.message.chat.id, call.message.message_id)
            try:
                with open('logomsg.jpg', 'rb') as file:
                    await bot.send_photo(call.message.chat.id, photo=file, caption=msg, reply_markup=markup2,
                                         parse_mode='HTML')
            except asyncio_helper.ApiException as e:
                if e.result.status_code in (400, 401, 403, 404, 429, 500, 502):
                    print("message cant be sent")
                else:
                    raise
        elif (language['You can request a withdrawal after earning $100.'] in call.message.text
              or language['Monthly list'] in call.message.text
              or 'Thank' in call.message.text):
            markup8 = types.InlineKeyboardMarkup()
            withdraw = types.InlineKeyboardButton(f"🛍️{language['Withdraw']}", callback_data="withdraw")
            markup8.row(withdraw)
            info = types.InlineKeyboardButton(f"ℹ️ {language['Info']}", callback_data="info")
            purchase = types.InlineKeyboardButton(f"📝 {language['List']}", callback_data="list")
            markup8.add(info, purchase)
            Back = types.InlineKeyboardButton(f"🔙 {language['Back']}", callback_data="back")
            markup8.row(Back)
            UserBalance = await readUserdata(str(call.from_user.id))
            UserReferrals = await getUserReferrals(str(call.from_user.id))
            referalcode = hashReferal(str(call.from_user.id))
            referallink = f'https://t.me/TonNetworkTracker_bot?start={referalcode}'
            msgreferal = (
                f"________ 👇🏼<b>ONE CLICK</b>👇🏼 ________\n\n<code>{referallink}</code>\n_________________________________\n\n\n👥 "
                f"<b>{language['Your Referrals']}:</b> {len(UserReferrals)}/10    \n\n💰 <b>{language['Your Balance']}:</b> {UserBalance[4]}$")            # <b>{language['Your Referal Code']}: </b>{referalcode}
            try:
                await bot.edit_message_text(chat_id=call.message.chat.id,
                                            message_id=call.message.message_id,
                                            text=msgreferal,
                                            reply_markup=markup8,
                                            parse_mode='HTML')
            except asyncio_helper.ApiException as e:
                if e.result.status_code in (400, 401, 403, 404, 429, 500, 502):
                    print("message cant be sent")
                else:
                    raise
        elif language['Wallet Details'] in call.message.text:
            #    Wallet Details
            markup1 = types.InlineKeyboardMarkup()

            if not wallets:

                msg = f"<b>{language['You Have No Saved Wallets']}</b>"
                Add = types.InlineKeyboardButton(f"➕ {language['Add']}", callback_data="Add")
                markup1.add(Add)
                Back = types.InlineKeyboardButton(f"🔙 {language['Back']}", callback_data="back")
                markup1.add(Back)

                try:
                    await bot.edit_message_text(chat_id=call.message.chat.id,
                                                message_id=call.message.message_id,
                                                text=msg,
                                                reply_markup=markup1,
                                                parse_mode='HTML')
                except asyncio_helper.ApiException as e:
                    if e.result.status_code in (400, 401, 403, 404, 429, 500, 502):
                        print("message cant be sent")
                    else:
                        raise
            else:
                if len(wallets) < 8:

                    for wallet in wallets:
                        if wallet[4] == 'Not Named':
                            wal = types.InlineKeyboardButton(wallet[0], callback_data=wallet[0])
                            markup1.row(wal)
                        else:
                            wlmsg = str(wallet[4])
                            wal = types.InlineKeyboardButton(wlmsg, callback_data=wallet[0])
                            markup1.row(wal)
                else:

                    for i in range(0, 7):

                        if wallets[i][4] == 'notag':
                            wal = types.InlineKeyboardButton(wallets[i][0], callback_data=wallets[i][0])
                            markup1.row(wal)

                        else:

                            wlmsg = str(wallets[i][4])
                            wal = types.InlineKeyboardButton(wlmsg, callback_data=wallets[i][0])
                            markup1.row(wal)

                    current = types.InlineKeyboardButton("O", callback_data="0")
                    Nextpage = types.InlineKeyboardButton(">>", callback_data="next")
                    markup1.row(current, Nextpage)
                msg = f"<b>{language['Choose Saved Wallet']}</b>"
                Add = types.InlineKeyboardButton(f"➕ {language['Add']}", callback_data="Add")
                markup1.add(Add)
                Back = types.InlineKeyboardButton(f"🔙 {language['Back']}", callback_data="back")
                markup1.add(Back)
                try:
                    await bot.edit_message_text(chat_id=call.message.chat.id,
                                                message_id=call.message.message_id,
                                                text=msg,
                                                reply_markup=markup1,
                                                parse_mode='HTML')
                except asyncio_helper.ApiException as e:
                    if e.result.status_code in (400, 401, 403, 404, 429, 500, 502):
                        print("message cant be sent")
                    else:
                        raise
        elif language['Choose Prefered Language'] in call.message.text:
            userSetting = await readUserdata(str(call.from_user.id))
            if userSetting[5] == "free":
                ad = 'ON'
            else:
                ad = 'OFF'
            chartem = 'ON' if (userSetting[1] == 'True') else 'OFF'
            valdolem = 'ON' if (userSetting[2] == 'True') else 'OFF'
            markup6 = types.InlineKeyboardMarkup()
            charts = types.InlineKeyboardButton(f"📊 {language['Charts']}: {chartem}", callback_data="charts")
            markup6.add(charts)
            valueindol = types.InlineKeyboardButton(f"💲 {language['Value In Dollar']}: {valdolem}",
                                                    callback_data="dolarval")
            markup6.add(valueindol)
            lang_button_label = f"{langflag.get(lang, lang)} {language['Language']}"
            lang = types.InlineKeyboardButton(lang_button_label, callback_data="lang")
            prog = types.InlineKeyboardButton(f"📣 AD's: {ad}", callback_data="prog")
            markup6.add(lang, prog)
            Back = types.InlineKeyboardButton(f"🔙 {language['Back']}", callback_data="back")
            markup6.add(Back)
            msgsetting = f"\U00002699  <b>{language['Your Settings']}</b>"

            try:
                await bot.edit_message_text(chat_id=call.message.chat.id,
                                            message_id=call.message.message_id,
                                            text=msgsetting,
                                            reply_markup=markup6,
                                            parse_mode='HTML')
            except asyncio_helper.ApiException as e:
                if e.result.status_code in (400, 401, 403, 404, 429, 500, 502):
                    print("message cant be sent")
                else:
                    raise
        elif f'PRO {language["PLAN"]}' in call.message.text:
            messageId = str(call.data).split('/')
            for i in range(1, len(messageId)):
                try:
                    await bot.delete_message(call.message.chat.id, messageId[i])
                except Exception as e:
                    print(f"Failed to delete message : {e}")
            userSetting = await getsubByUser(str(call.from_user.id))
            plan = str(userSetting[1]).upper()

            wallets = len(wallets)
            coins = 0
            nftss = 0

            if plan == 'STANDARD':
                untill = (int(userSetting[2]) - int(time.time())) / (60 * 60 * 24)
                until = str(round(untill, 0)) + f" {language['Days Left']}"
                allowedwallets = 50
                allowedcoins = 30
                allowednfts = 12
                allowedmsgperh = 150
            elif plan == 'PREMIUM':
                untill = (int(userSetting[2]) - int(time.time())) / (60 * 60 * 24)
                until = str(round(untill, 0)) + f" {language['Days Left']}"
                allowedwallets = 250
                allowedcoins = 250
                allowednfts = 250
                allowedmsgperh = 500
            elif plan == 'PRO':
                untill = (int(userSetting[2]) - int(time.time())) / (60 * 60 * 24)
                until = str(round(untill, 0)) + f" {language['Days Left']}"
                allowedwallets = 1000
                allowedcoins = 1000
                allowednfts = 1000
                allowedmsgperh = 1000
            else:
                until = ' '
                allowedwallets = 7
                allowedcoins = 5
                allowednfts = 2
                allowedmsgperh = 10
            markup6 = types.InlineKeyboardMarkup()
            walletss = f"💼 {language['Wallets']} {wallets}/{allowedwallets}"
            coin = f"\U0001F4B0 {language['Coins']} {coins}/{allowedcoins}"
            nfts = f"🌅️ {language['NFTs']} {nftss}/{allowednfts}"
            msgperh = f"{allowedmsgperh} {language['Messages Per Hour']}"

            purchase = types.InlineKeyboardButton(f"💳 {language['Purchase']}", callback_data="purchase")
            markup6.add(purchase)
            Back = types.InlineKeyboardButton(f"🔙 {language['Back']}", callback_data="back")
            markup6.add(Back)
            msgsub = f"<b>{language['Subscription']} {language['Plan']}:</b> \n {plan}\n {until}\n\n{walletss}\n{coin}\n{nfts}\n{msgperh}"

            try:
                await bot.edit_message_text(chat_id=call.message.chat.id,
                                            message_id=call.message.message_id,
                                            text=msgsub,
                                            reply_markup=markup6,
                                            parse_mode='HTML')
            except asyncio_helper.ApiException as e:
                if e.result.status_code in (400, 401, 403, 404, 429, 500, 502):
                    print("message cant be sent")
                else:
                    raise
        else:
            print(call.message.text)

    elif call.data == "sub":
        userSetting = await getsubByUser(str(call.from_user.id))
        plan = str(userSetting[1]).upper()

        wallets = len(wallets)
        coins = 0
        nftss = 0
        if plan == 'STANDARD':
            untill = (int(userSetting[2]) - int(time.time())) / (60 * 60 * 24)
            until = str(round(untill, 0)) + f" {language['Days Left']}"
            allowedwallets = 50
            allowedcoins = 30
            allowednfts = 12
            allowedmsgperh = 150
        elif plan == 'PREMIUM':
            untill = (int(userSetting[2]) - int(time.time())) / (60 * 60 * 24)
            until = str(round(untill, 0)) + f" {language['Days Left']}"
            allowedwallets = 250
            allowedcoins = 250
            allowednfts = 250
            allowedmsgperh = 500
        elif plan == 'PRO':
            untill = (int(userSetting[2]) - int(time.time())) / (60 * 60 * 24)
            until = str(round(untill, 0)) + f" {language['Days Left']}"
            allowedwallets = 1000
            allowedcoins = 1000
            allowednfts = 1000
            allowedmsgperh = 1000
        else:
            until = ' '
            allowedwallets = 7
            allowedcoins = 5
            allowednfts = 2
            allowedmsgperh = 10
        markup6 = types.InlineKeyboardMarkup()
        walletss = f"💼 {language['Wallets']} {wallets}/{allowedwallets}"
        coin = f"\U0001F4B0 {language['Coins']} {coins}/{allowedcoins}"
        nfts = f"🌅️ {language['NFTs']} {nftss}/{allowednfts}"
        msgperh = f"{allowedmsgperh} {language['Messages Per Hour']}"

        purchase = types.InlineKeyboardButton(f"💳 {language['Purchase']}", callback_data="purchase")
        markup6.add(purchase)
        Back = types.InlineKeyboardButton(f"🔙 {language['Back']}", callback_data="back")
        markup6.add(Back)
        msgsub = f"<b>{language['Subscription']} {language['Plan']}:</b> {plan}\n \n{until}\n{walletss}\n{coin}\n{nfts}\n{msgperh}"

        # await deleteMsg(bot, call.message.chat.id, call.message.message_id)
        try:
            await bot.send_message(chat_id=call.message.chat.id,
                                   text=msgsub,
                                   reply_markup=markup6,
                                   parse_mode='HTML')
        except asyncio_helper.ApiException as e:
            if e.result.status_code in (400, 401, 403, 404, 429, 500, 502):
                print("message cant be sent")
            else:
                raise

    elif call.data == "purchase":
        print('purchase')
        plans = ['STANDARD', 'PREMIUM', 'PRO']
        messageids = []
        for plan in plans:
            markupPur = types.InlineKeyboardMarkup()

            if plan == 'STANDARD':
                allowedwallets = 50
                allowedcoins = 30
                allowednfts = 12
                allowedmsgperh = 150
                monthly = 20
                Annual = 200

            elif plan == 'PREMIUM':
                allowedwallets = 250
                allowedcoins = 250
                allowednfts = 250
                allowedmsgperh = 500
                monthly = 60
                Annual = 540
            elif plan == 'PRO':
                allowedwallets = 1000
                allowedcoins = 1000
                allowednfts = 1000
                allowedmsgperh = 1000
                monthly = 100
                Annual = 800
            month = types.InlineKeyboardButton(f"🕑️ {language['Monthly']} ({monthly} $)", callback_data="Monthly")
            year = types.InlineKeyboardButton(f"📅 {language['Annual']} ({Annual} $)", callback_data="Annual")
            markupPur.row(month, year)

            msgPur = f"<b>{plan} {language['PLAN']}</b>\n - {allowedwallets} {language['Wallets']}\n - {allowedcoins} {language['Coins']}\n - {allowednfts} {language['NFTs']}\n - {allowedmsgperh} {language['Messages Per Hour']}"
            if plan == 'STANDARD':

                # await deleteMsg(bot, call.message.chat.id, call.message.message_id)
                try:
                    message = await bot.send_message(chat_id=call.message.chat.id,
                                                     text=msgPur,
                                                     reply_markup=markupPur,
                                                     parse_mode='HTML')
                except asyncio_helper.ApiException as e:
                    if e.result.status_code in (400, 401, 403, 404, 429, 500, 502):
                        print("message cant be sent")
                    else:
                        raise
                messageids.append(message.id)
            else:
                if plan == 'PRO':
                    calback = 'back'
                    for idi in messageids:
                        calback += '/' + str(idi)
                    Back = types.InlineKeyboardButton(f"🔙 {language['Back']}", callback_data=calback)
                    markupPur.row(Back)
                try:
                    planmsg = await bot.send_message(chat_id=call.message.chat.id, text=msgPur, reply_markup=markupPur,
                                                     parse_mode='HTML')

                    if plan == 'PREMIUM':
                        messageids.append(planmsg.id)
                        print(messageids)
                except asyncio_helper.ApiException as e:
                    if e.result.status_code in (400, 401, 403, 404, 429, 500, 502):
                        print("message cant be sent")
                    else:
                        raise

    elif call.data in ["Monthly", "Annual"]:
        print(call.data)
        tonPrice = 0
        while tonPrice == 0:
            tonPrice = livetonprice()
            if tonPrice > 0:
                if "STANDARD" in call.message.text:
                    monthly = round((20 / tonPrice), 2)
                    Annual = round((200 / tonPrice), 2)
                    txmsg = str(call.from_user.id) + '_' + str(call.message.chat.id) + '_STANDARD_SUB_' + str(call.data)
                    if call.data == "Monthly":
                        tonhub = generate_payment_link(Hotwallets, monthly, txmsg, "tonhub")
                        tonkeeper = generate_payment_link(Hotwallets, monthly, txmsg, "tonkeeper")
                    else:
                        tonhub = generate_payment_link(Hotwallets, Annual, txmsg, "tonhub")
                        tonkeeper = generate_payment_link(Hotwallets, Annual, txmsg, "tonkeeper")
                    break
                elif "PREMIUM" in call.message.text:
                    monthly = round((60 / tonPrice), 2)
                    Annual = round((540 / tonPrice), 2)
                    txmsg = str(call.from_user.id) + '_' + str(call.message.chat.id) + '_PREMIUM_SUB_' + str(call.data)
                    if call.data == "Monthly":
                        tonhub = generate_payment_link(Hotwallets, monthly, txmsg, "tonhub")
                        tonkeeper = generate_payment_link(Hotwallets, monthly, txmsg, "tonkeeper")
                    else:
                        tonhub = generate_payment_link(Hotwallets, Annual, txmsg, "tonhub")
                        tonkeeper = generate_payment_link(Hotwallets, Annual, txmsg, "tonkeeper")
                    break
                elif "PRO" in call.message.text:
                    monthly = round((100 / tonPrice), 2)
                    Annual = round((800 / tonPrice), 2)
                    txmsg = str(call.from_user.id) + '_' + str(call.message.chat.id) + '_PRO_SUB_' + str(call.data)
                    if call.data == "Monthly":
                        tonhub = generate_payment_link(Hotwallets, monthly, txmsg, "tonhub")
                        tonkeeper = generate_payment_link(Hotwallets, monthly, txmsg, "tonkeeper")
                    else:
                        tonhub = generate_payment_link(Hotwallets, Annual, txmsg, "tonhub")
                        tonkeeper = generate_payment_link(Hotwallets, Annual, txmsg, "tonkeeper")
                    break
        Purmsg = f'<b> {language["Choose Payment Method"]} </b>'
        Pur = types.InlineKeyboardMarkup()
        print(tonhub)
        tonhubs = types.InlineKeyboardButton("Tonhub", url=str(tonhub))
        tonkeepers = types.InlineKeyboardButton("Tonkeeper", url=str(tonkeeper))
        Pur.row(tonhubs, tonkeepers)
        try:
            paymentmsg = await bot.send_message(chat_id=call.message.chat.id, text=Purmsg, reply_markup=Pur,
                                                parse_mode='HTML')

        except asyncio_helper.ApiException as e:
            print(e.result)
            # if e.result.status_code in (400,401,403,404,429,500,502):
            #             print("message cant be sent")
            # else:
            #     raise

    elif call.data == "ref":
        markup8 = types.InlineKeyboardMarkup()
        withdraw = types.InlineKeyboardButton(f"🛍️{language['Withdraw']}", callback_data="withdraw")
        markup8.row(withdraw)
        info = types.InlineKeyboardButton(f"ℹ️ {language['Info']}", callback_data="info")
        purchase = types.InlineKeyboardButton(f"📝 {language['List']}", callback_data="list")
        markup8.add(info, purchase)
        Back = types.InlineKeyboardButton(f"🔙 {language['Back']}", callback_data="back")
        markup8.row(Back)
        UserBalance = await readUserdata(str(call.from_user.id))
        UserReferrals = await getUserReferrals(str(call.from_user.id))
        referalcode = hashReferal(str(call.from_user.id))
        referallink = f'https://t.me/TonNetworkTracker_bot?start={referalcode}'
        msgreferal = (f"________ 👇🏼<b>ONE CLICK</b>👇🏼 ________\n\n<code>{referallink}</code>\n_________________________________\n\n\n👥 "
                      f"<b>{language['Your Referrals']}:</b> {len(UserReferrals)}/10    \n\n💰 <b>{language['Your Balance']}:</b> {UserBalance[4]}$")
        # <b>{language['Your Referal Code']}: </b>{referalcode}

        # await deleteMsg(bot, call.message.chat.id, call.message.message_id)
        try:
            await bot.send_message(chat_id=call.message.chat.id,
                                   text=msgreferal,
                                   reply_markup=markup8,
                                   parse_mode='HTML')
        except asyncio_helper.ApiException as e:
            if e.result.status_code in (400, 401, 403, 404, 429, 500, 502):
                print("message cant be sent")
            else:
                raise

    elif call.data == "withdraw":
        user_data = await readUserdata(str(call.from_user.id))
        UserBalance = int(user_data[4])
        if UserBalance < 100:
            msgwithdraw = "You haven't recommended us to enough people 🙁"
            try:
                await bot.send_message(chat_id=call.message.chat.id,
                                       text=msgwithdraw,
                                       parse_mode='HTML')
            except asyncio_helper.ApiException as e:
                if e.result.status_code in (400, 401, 403, 404, 429, 500, 502):
                    print("message cant be sent")
                else:
                    raise
        else:
            markup11 = types.InlineKeyboardMarkup()
            contact = types.InlineKeyboardButton("📩 Contact", url='https://t.me/SunriseTonBotContact')
            markup11.row(contact)
            Back = types.InlineKeyboardButton(f"🔙 {language['Back']}", callback_data="back")
            markup11.row(Back)
            msgwithdraw = (
                "<b>Thank you very much for your support!</b> \n‎\n Write to us to withdraw your money! \n‎")
            try:
                await bot.edit_message_text(chat_id=call.message.chat.id,
                                            message_id=call.message.message_id,
                                            text=msgwithdraw,
                                            reply_markup=markup11,
                                            parse_mode='HTML')
            except asyncio_helper.ApiException as e:
                if e.result.status_code in (400, 401, 403, 404, 429, 500, 502):
                    print("message cant be sent")
                else:
                    raise

    elif call.data == "info":
        markup9 = types.InlineKeyboardMarkup()
        Back = types.InlineKeyboardButton(f"🔙 {language['Back']}", callback_data="back")
        markup9.row(Back)
        listmsg = f" {language['If you invite 10 people who purchase the STANDARD package for a month or higher, you will receive the STANDARD package for a year for free.']}\n\n{language['If a person purchases the STANDARD or higher package for a year, you gain 10 percent on its purchase.']}\n\n {language['The right to a bonus is possible once for each new user.']} \n\n {language['You can request a withdrawal after earning $100.']}"
        try:
            await bot.edit_message_text(chat_id=call.message.chat.id,
                                        message_id=call.message.message_id,
                                        text=listmsg,
                                        reply_markup=markup9,
                                        parse_mode='HTML')
        except asyncio_helper.ApiException as e:
            if e.result.status_code in (400, 401, 403, 404, 429, 500, 502):
                print("message cant be sent")
            else:
                raise

    elif call.data == "list":
        markup9 = types.InlineKeyboardMarkup()
        Back = types.InlineKeyboardButton(f"🔙 {language['Back']}", callback_data="back")
        markup9.row(Back)
        UserReferrals = await getUserReferrals(str(call.from_user.id))
        monthy = ''
        yeary = ''
        for refers in UserReferrals:
            if refers[8] == "free":
                continue
            elif refers[8] == 'monthly':
                monthy += '- ' + str(refers[7]) + ' (' + str(refers[5]) + ') \n'
            elif refers[8] == 'annual':
                yeary += '- ' + str(refers[7]) + ' (' + str(refers[5]) + ') \n'
        if monthy == '':
            monthy = 'None \n'
        if yeary == '':
            yeary = 'None \n'

        listmsg = f" {language['Monthly list']}:\n {monthy} --------------- \n {language['Annual list']}:\n {yeary}"
        try:
            await bot.edit_message_text(chat_id=call.message.chat.id,
                                        message_id=call.message.message_id,
                                        text=listmsg,
                                        reply_markup=markup9,
                                        parse_mode='HTML')
        except asyncio_helper.ApiException as e:
            if e.result.status_code in (400, 401, 403, 404, 429, 500, 502):
                print("message cant be sent")
            else:
                raise

    elif call.data == "faq":
        markup10 = types.InlineKeyboardMarkup()
        contact = types.InlineKeyboardButton("📩 Contact", url='https://t.me/SunriseTonBotContact')
        markup10.row(contact)
        Back = types.InlineKeyboardButton(f"🔙 {language['Back']}", callback_data="back")
        markup10.row(Back)
        msgcontact = (
            "<b>Banner on Sunrise Ton Bot:</b> \n ⭐️ $40 for 1 day \n ⭐️ $100 for 3 days \n "
            "⭐️ $200 for 1 week \n ⭐️ $600 for 4 weeks \n‎\n <b>Direct Message to STB users:</b> \n "
            "⭐️ $200 for 1 Mass DM to users \n‎\n <b>Banner and DM Bundle for 1 week:</b> \n ⭐️ Mass DM Post to STB users"
            " \n ⭐️ Banner for 7 days \n ⭐️ $360 (savings of $40) \n‎\n _________________________________ "
            "\n‎\n<strong> Specifications for Banner: </strong>\n - text with maximum 60 characters \n - link(s) embedded in the text"
            "\n - jpg, png, or mp4 with sound \n - 3:1 size ratio, ex: 1920x640. 1200x400 \n‎\n<strong>Specifications for Mass DM:</strong>"
            "\n - Any text as you please \n - Optional banner image or video \n - No custom emoji's \n _________________________________"
            "\n‎\n<i>Note: We reserve the right to refuse a promo. If it's discovered to be a scam, "
            "it will be revoked or cancelled, and not refunded.</i>")
        try:
            await bot.send_message(chat_id=call.message.chat.id,
                                   text=msgcontact,
                                   reply_markup=markup10,
                                   parse_mode='HTML')
        except asyncio_helper.ApiException as e:
            if e.result.status_code in (400, 401, 403, 404, 429, 500, 502):
                print("message cant be sent")
            else:
                raise

    elif call.data == "setting":
        userSetting = await readUserdata(str(call.from_user.id))
        if userSetting[9] == "True":
            ad = 'ON'
        else:
            ad = 'OFF'
        lang = str(userSetting[3])
        chartem = 'ON' if (userSetting[1] == 'True') else 'OFF'
        valdolem = 'ON' if (userSetting[2] == 'True') else 'OFF'
        markup6 = types.InlineKeyboardMarkup()
        charts = types.InlineKeyboardButton(f"📊 {language['Charts']}: {chartem}", callback_data="charts")
        markup6.add(charts)
        valueindol = types.InlineKeyboardButton(f"💲 {language['Value In Dollar']}: {valdolem}", callback_data="dolarval")
        markup6.add(valueindol)
        # Assuming langflag is a dictionary mapping language codes to their flag emoji or name
        lang_button_label = f"{langflag.get(lang, lang)} {language['Language']}"
        lang = types.InlineKeyboardButton(lang_button_label, callback_data="lang")
        # prog = types.InlineKeyboardButton(language['In Progress'], callback_data="prog")
        prog = types.InlineKeyboardButton(f"📣 AD's: {ad}", callback_data="prog")
        markup6.add(lang, prog)
        Back = types.InlineKeyboardButton(f"🔙 {language['Back']}", callback_data="back")
        markup6.add(Back)
        msgsetting = f"\U00002699  <b>{language['Your Settings']}</b>"

        # await deleteMsg(bot, call.message.chat.id, call.message.message_id)
        try:
            await bot.send_message(chat_id=call.message.chat.id,
                                   text=msgsetting,
                                   reply_markup=markup6,
                                   parse_mode='HTML')
        except asyncio_helper.ApiException as e:
            if e.result.status_code in (400, 401, 403, 404, 429, 500, 502):
                print("message cant be sent")
            else:
                raise

    elif call.data == "prog":
        userSetting = await readUserdata(str(call.from_user.id))
        print('ads1: ', userSetting)
        if userSetting[5] == "free":
            markup = types.InlineKeyboardMarkup()
            subscription = types.InlineKeyboardButton(f"\U0001F4B3 {language['Change Plan']}", callback_data="sub")
            markup.row(subscription)
            try:
                await bot.send_message(call.message.chat.id,
                                       language["To Turn Off You Need To Upgrade Your Subscription Plan"],
                                       reply_markup=markup)
            except asyncio_helper.ApiException as e:
                if e.result.status_code in (400, 401, 403, 404, 429, 500, 502):
                    print("message cant be sent")
                else:
                    raise
        else:
            userSetting = toggle_ads(str(call.from_user.id))
            # print('ads: ',userSetting)
            if userSetting[9] == "True":
                ad = 'ON'
            else:
                ad = 'OFF'
            lang = str(userSetting[3])
            chartem = 'ON' if (userSetting[1] == 'True') else 'OFF'
            valdolem = 'ON' if (userSetting[2] == 'True') else 'OFF'
            markup6 = types.InlineKeyboardMarkup()
            charts = types.InlineKeyboardButton(f"📊 {language['Charts']}: {chartem}", callback_data="charts")
            markup6.add(charts)
            valueindol = types.InlineKeyboardButton(f"💲 {language['Value In Dollar']}: {valdolem}",
                                                    callback_data="dolarval")
            markup6.add(valueindol)
            # Assuming langflag is a dictionary mapping language codes to their flag emoji or name
            lang_button_label = f"{langflag.get(lang, lang)} {language['Language']}"
            lang = types.InlineKeyboardButton(lang_button_label, callback_data="lang")
            # prog = types.InlineKeyboardButton(language['In Progress'], callback_data="prog")
            prog = types.InlineKeyboardButton(f"📣 AD's: {ad}", callback_data="prog")
            markup6.add(lang, prog)
            Back = types.InlineKeyboardButton(f"🔙 {language['Back']}", callback_data="back")
            markup6.add(Back)
            msgsetting = f"\U00002699  <b>{language['Your Settings']}</b>"

            try:
                await bot.edit_message_text(chat_id=call.message.chat.id,
                                            message_id=call.message.message_id,
                                            text=msgsetting,
                                            reply_markup=markup6,
                                            parse_mode='HTML')
            except asyncio_helper.ApiException as e:
                if e.result.status_code in (400, 401, 403, 404, 429, 500, 502):
                    print("message cant be sent")
                else:
                    raise

    elif call.data == "lang":
        markup6 = types.InlineKeyboardMarkup()

        ar = types.InlineKeyboardButton("🇸🇦 AR", callback_data="ar")
        be = types.InlineKeyboardButton("🇧🇾 BE", callback_data="be")
        markup6.row(ar, be)
        de = types.InlineKeyboardButton("🇩🇪 DE", callback_data="de")
        es = types.InlineKeyboardButton("🇪🇸 ES", callback_data="es")
        markup6.row(de, es)
        eng = types.InlineKeyboardButton("🇬🇧 ENG", callback_data="eng")
        fa = types.InlineKeyboardButton("🇮🇷 FA", callback_data="fa")
        markup6.row(eng, fa)
        fr = types.InlineKeyboardButton("🇫🇷 FR", callback_data="fr")
        ja = types.InlineKeyboardButton("🇯🇵 JA", callback_data="ja")
        markup6.row(fr, ja)
        pl = types.InlineKeyboardButton("🇵🇱 PL", callback_data="pl")
        ru = types.InlineKeyboardButton("🇷🇺 RU", callback_data="ru")
        markup6.row(pl, ru)
        rum = types.InlineKeyboardButton("🇷🇴 RUM", callback_data="rum")
        ua = types.InlineKeyboardButton("🇺🇦 UA", callback_data="ua")
        markup6.row(rum, ua)
        uzb = types.InlineKeyboardButton("🇺🇿 UZB", callback_data="uzb")
        zh = types.InlineKeyboardButton("🇨🇳 ZH", callback_data="zh")
        markup6.row(uzb, zh)

        Back = types.InlineKeyboardButton(f"🔙 {language['Back']}", callback_data="back")
        markup6.row(Back)
        msgsetting = f"<b>{language['Choose Prefered Language']}: </b>"

        try:
            await bot.edit_message_text(chat_id=call.message.chat.id,
                                        message_id=call.message.message_id,
                                        text=msgsetting,
                                        reply_markup=markup6,
                                        parse_mode='HTML')
        except asyncio_helper.ApiException as e:
            if e.result.status_code in (400, 401, 403, 404, 429, 500, 502):
                print("message cant be sent")
            else:
                raise

    elif call.data in ["charts", "dolarval", "eng", "fr", "pl", "ar", "fa", "be", "rum", "uzb", "ua", "ru", "de", "es",
                       "ja", "zh"]:

        userSetting = await userSettings(str(call.from_user.id), str(call.data))
        user = await readUserdata(str(call.from_user.id))
        if not user:
            file_path = 'languages/eng.yml'
        else:
            if str(user[5]) != 'free':
                await verifyTimestamp(user[0])
            lang = user[3]
            file_path = f'languages/{lang}.yml'
        # print('ads: ',userSetting)
        if user[9] == "True":
            ad = 'ON'
        else:
            ad = 'OFF'
        # Specify UTF-8 encoding when opening the file
        with open(file_path, 'r', encoding='utf-8') as file:
            language = yaml.safe_load(file)
        chartem = 'ON' if userSetting['charts'] else 'OFF'
        valdolem = 'ON' if userSetting['dolarval'] else 'OFF'
        markup6 = types.InlineKeyboardMarkup()
        charts = types.InlineKeyboardButton(f"📊 {language['Charts']}: {chartem}", callback_data="charts")
        markup6.add(charts)
        valueindol = types.InlineKeyboardButton(f"💲 {language['Value In Dollar']}: {valdolem}", callback_data="dolarval")
        markup6.add(valueindol)
        lang_button_label = f"{langflag.get(lang, lang)} {language['Language']}"
        lang = types.InlineKeyboardButton(lang_button_label, callback_data="lang")
        prog = types.InlineKeyboardButton(f"📣 AD's: {ad}", callback_data="prog")
        markup6.add(lang, prog)
        Back = types.InlineKeyboardButton(f"🔙 {language['Back']}", callback_data="back")
        markup6.add(Back)
        msgsetting = f"\U00002699  <b>{language['Your Settings']}</b>"

        try:
            await bot.edit_message_text(chat_id=call.message.chat.id,
                                        message_id=call.message.message_id,
                                        text=msgsetting,
                                        reply_markup=markup6,
                                        parse_mode='HTML')
        except asyncio_helper.ApiException as e:
            if e.result.status_code in (400, 401, 403, 404, 429, 500, 502):
                print("message cant be sent")
            else:
                raise
    elif call.data in ['swap', 'nft', 'sent', 'recieved', 'all']:
        new_markup = types.InlineKeyboardMarkup()
        for row in call.message.reply_markup.keyboard:
            for button in row:
                url = getattr(button, 'url', None)
                if url:
                    wals = button
                    new_markup.row(wals)
                    break
            if url:
                break
        if wals and url:
            wallet = url.replace("https://tonviewer.com/", "")
            notif = await walletnotifications(str(call.from_user.id), wallet, str(call.data))
            recieved = '\U00002705' if (notif['recieved'] == 'True') else ''
            sent = '\U00002705' if (notif['sent'] == 'True') else ''
            swapemoj = '\U00002705' if (notif['swap'] == 'True') else ''
            nftemoj = '\U00002705' if (notif['nft'] == 'True') else ''
            sentfrom = types.InlineKeyboardButton(f"{recieved} {language['Transfers In']}", callback_data="recieved")
            sento = types.InlineKeyboardButton(f"{sent} {language['Transfers Out']}", callback_data="sent")
            new_markup.row(sentfrom, sento)
            swap = types.InlineKeyboardButton(f"{swapemoj} {language['Swap']}", callback_data="swap")
            nft = types.InlineKeyboardButton(f"{nftemoj} {language['NFT']}", callback_data="nft")
            new_markup.row(swap, nft)
            balanc = types.InlineKeyboardButton(f"🔍 {language['Balance']}", callback_data="balance")
            new_markup.row(balanc)
            tag = types.InlineKeyboardButton(f"\U0001F3F7 {language['Rename']}", callback_data="tag")
            remove = types.InlineKeyboardButton(f"\U00002716 {language['Delete']}", callback_data="remove")
            new_markup.row(tag, remove)
            back = types.InlineKeyboardButton(f"🔙 {language['Back']}", callback_data="back")
            new_markup.row(back)
            msg = f" <b> {language['Wallet Details']}</b> "
            current_markup_str = serialize_inline_keyboard(call.message.reply_markup)
            new_markup_str = serialize_inline_keyboard(new_markup)

            if current_markup_str != new_markup_str:
                try:
                    await bot.edit_message_text(chat_id=call.message.chat.id,
                                                message_id=call.message.message_id,
                                                text=msg,
                                                reply_markup=new_markup,
                                                parse_mode='HTML')
                except asyncio_helper.ApiException as e:
                    if e.result:
                        print(e.result)
                    else:
                        print(e)
                        raise
            else:
                print('the same')


async def track_wallets_websocket(bot):
    url = "wss://tonapi.io/v2/websocket"
    while True:
        Wallets1 = readWallets()
        accounts = [Wallets1[key]['address'] for key in Wallets1]
        accounts.append(Hotwallets)
        try:
            async with websockets.connect(url) as websocket:

                # Subscribe to account transactions
                subscribe_message = {
                    "jsonrpc": "2.0",
                    "method": "subscribe_account",
                    "params": list(accounts),
                    "id": 1
                }
                await websocket.send(json.dumps(subscribe_message))

                while True:
                    usersplans = await ReadAllplans()
                    for user in usersplans:
                        subplan = user[1]

                        if str(user[5]) != 'free':
                            userupdated = await verifyTimestamp(user[0])
                            if userupdated:
                                subplan = 'free'
                        userWallets = await checkwalletofuser(str(user[0]))
                        if subplan.upper() == 'STANDARD':
                            until = (int(user[2]) - int(time.time())) / (60 * 60 * 24)
                            allowedmsgperh = 150
                        elif subplan.upper() == 'PREMIUM':
                            until = (int(user[2]) - int(time.time())) / (60 * 60 * 24)
                            allowedmsgperh = 500
                        elif subplan.upper() == 'PRO':
                            until = (int(user[2]) - int(time.time())) / (60 * 60 * 24)
                            allowedmsgperh = 1000
                        else:
                            until = '♾️'
                            allowedmsgperh = 10
                            if len(userWallets) > 7:
                                for i in range(7, len(userWallets)):
                                    await removeWallet(userWallets[i], user[0])
                        if until != '♾️':
                            if math.isclose(until == 4):
                                await alertSub(bot, user[0], until)
                            elif math.isclose(until == 3):
                                await alertSub(bot, user[0], until)
                            elif math.isclose(until == 2):
                                await alertSub(bot, user[0], until)
                            elif math.isclose(until, 1):
                                await alertSub(bot, user[0], until)
                    Wallets = readWallets()
                    accounts1 = [Wallets[key]['address'] for key in Wallets]
                    accounts1.append(Hotwallets)
                    if len(accounts) != len(accounts1):
                        break
                    response = await websocket.recv()
                    try:
                        response_data = json.loads(response)
                        print(response_data)

                        if 'params' in response_data and 'tx_hash' in response_data['params']:

                            if response_data and 'params' in response_data and "account_id" in response_data['params']:
                                if str(Hotwallets) in response_data['params']["account_id"]:
                                    subs = checkTransactions(str(Hotwallets), response_data['params']["tx_hash"], 'SUB')
                                    if subs:
                                        rightamount = False
                                        tonPrice = livetonprice()
                                        Amount = tonPrice * subs['value']
                                        newSub = str(subs['comment']).split('_')
                                        # str(call.from_user.id)+ '_' + str(call.message.chat.id) + '_STANDARD_SUB_' + str(call.data)
                                        if "Monthly" in newSub:
                                            if (('STANDARD' in newSub) and (18 <= Amount)) or (
                                                    ('PREMIUM' in newSub) and (58 <= Amount)) or (
                                                    ('PRO' in newSub) and (98 <= Amount)):
                                                rightamount = True
                                                times = "Monthly"
                                                subdeadline = int(time.time()) + (30 * 24 * 60 * 60)
                                        elif "Annual" in newSub:
                                            if (('STANDARD' in newSub) and (190 <= Amount)) or (
                                                    ('PREMIUM' in newSub) and (520 <= Amount)) or (
                                                    ('PRO' in newSub) and (780 <= Amount)):
                                                rightamount = True
                                                times = "Annual"
                                                subdeadline = int(time.time()) + (30 * 24 * 60 * 60 * 12)
                                        if rightamount:
                                            await updateSub(newSub[0], str(newSub[2]).lower(), subdeadline)
                                            await update_subscription_plan(newSub[0], str(newSub[2]).lower(),
                                                                           times.lower())
                                            await update_balance(Amount / 10, newSub[0])
                                            plan = newSub[2]
                                            msgsub = f'✅ <b> Payment Recieved Successfully </b> \n You Can Now Enjoy The Perks Of The <b>{plan}</b> Plan'
                                            await bot.send_message(newSub[1], msgsub, parse_mode='HTML')

                                trx_details = transactionsEvent(response_data['params']["account_id"],
                                                                response_data['params']["tx_hash"])

                                if 'Transaction Type' not in trx_details:
                                    print(trx_details)
                                    # ----------NFT-------------
                                elif str(trx_details['Transaction Type']) == 'Buy NFT':
                                    Name = '<b>Name:</b> <a href="https://tonviewer.com/' + trx_details[
                                        'NFT Address'] + '">' + str(trx_details['NFT Name']) + '</a>'
                                    price = int(trx_details['Purchase Value']) / 1000000000
                                    buyfor = '<a href="https://tonviewer.com/transaction/' + trx_details[
                                        'TXid'] + '"> <b>Buy For:</b> ' + '</a>' + str(price) + ' ' + str(
                                        trx_details['Token Name'])
                                    fromid = '<b>From:</b> <a href="https://tonviewer.com/' + trx_details[
                                        'Seller Address'] + '">' + format_wallets(
                                        trx_details['Seller Address']) + '</a>'
                                    img_data = await fetch_image(trx_details['Imagelink'])

                                    for i, chat_id in enumerate(
                                            Wallets[str(response_data['params']["account_id"])]['chats']):

                                        notfy = Wallets[str(response_data['params']["account_id"])]['notifications'][
                                            chat_id]
                                        if str(notfy[1]) == 'True':
                                            usser = await readUserdata(
                                                Wallets[str(response_data['params']["account_id"])]['users'][i])
                                            dolarbal = None
                                            if str(usser[2]).lower() == 'true':
                                                tonPrice = livetonprice()
                                                dolarbal = round((float(tonPrice) * price), 2)
                                            header = Wallets[str(response_data['params']["account_id"])]['tag'][chat_id]
                                            if dolarbal:
                                                msg = '<a href="https://tonviewer.com/' + str(response_data['params'][
                                                                                                  "account_id"]) + '">' + header + '</a>\n' + Name + '\n' + buyfor + f'({dolarbal} $)\n' + fromid
                                            else:
                                                msg = '<a href="https://tonviewer.com/' + str(response_data['params'][
                                                                                                  "account_id"]) + '">' + header + '</a>\n' + Name + '\n' + buyfor + '\n' + fromid
                                            await bot.send_photo(chat_id, photo=img_data, caption=msg,
                                                                 parse_mode='HTML')
                                elif str(trx_details['Transaction Type']) == 'Sell NFT':
                                    Name = '<b>Name:</b> <a href="https://tonviewer.com/' + trx_details[
                                        'NFT Address'] + '">' + str(trx_details['NFT Name']) + '</a>'
                                    price = int(trx_details['Purchase Value']) / 1000000000
                                    buyfor = '<a href="https://tonviewer.com/transaction/' + trx_details[
                                        'TXid'] + '"> <b>Sell For:</b> ' + '</a>' + str(price) + ' ' + str(
                                        trx_details['Token Name'])
                                    fromid = '<b>To:</b> <a href="https://tonviewer.com/' + trx_details[
                                        'Buyer Address'] + '">' + format_wallets(trx_details['Buyer Address']) + '</a>'
                                    img_data = await fetch_image(trx_details['Imagelink'])

                                    for i, chat_id in enumerate(
                                            Wallets[str(response_data['params']["account_id"])]['chats']):
                                        notfy = Wallets[str(response_data['params']["account_id"])]['notifications'][
                                            chat_id]
                                        if str(notfy[1]) == 'True':
                                            usser = await readUserdata(
                                                Wallets[str(response_data['params']["account_id"])]['users'][i])
                                            dolarbal = None
                                            if str(usser[2]).lower() == 'true':
                                                tonPrice = livetonprice()
                                                dolarbal = round((float(tonPrice) * price), 2)
                                            header = Wallets[str(response_data['params']["account_id"])]['tag'][chat_id]
                                            if dolarbal:
                                                msg = '<a href="https://tonviewer.com/' + str(response_data['params'][
                                                                                                  "account_id"]) + '">' + header + '</a>\n' + Name + '\n' + buyfor + f'({dolarbal} $)\n' + fromid
                                            else:
                                                msg = '<a href="https://tonviewer.com/' + str(response_data['params'][
                                                                                                  "account_id"]) + '">' + header + '</a>\n' + Name + '\n' + buyfor + '\n' + fromid
                                            await bot.send_photo(chat_id, photo=img_data, caption=msg,
                                                                 parse_mode='HTML')
                                elif str(trx_details['Transaction Type']) == 'Sent NFT':
                                    Operation = str(trx_details['Transaction Type']).upper()
                                    Name = '<b>Name:</b> <a href="https://tonviewer.com/' + trx_details[
                                        'NFT Address'] + '">' + str(trx_details['NFT Name']) + '</a>'
                                    fromid = '<b>To:</b> <a href="https://tonviewer.com/' + trx_details[
                                        'Receiver Address'] + '">' + format_wallets(
                                        trx_details['Receiver Address']) + '</a>'
                                    img_data = await fetch_image(trx_details['Imagelink'])

                                    for chat_id in Wallets[str(response_data['params']["account_id"])]['chats']:
                                        notfy = Wallets[str(response_data['params']["account_id"])]['notifications'][
                                            chat_id]
                                        if str(notfy[1]) == 'True':
                                            header = Wallets[str(response_data['params']["account_id"])]['tag'][chat_id]
                                            msg = '<a href="https://tonviewer.com/' + str(response_data['params'][
                                                                                              "account_id"]) + '">' + header + '</a>\n' + Operation + '\n' + Name + '\n' + fromid
                                            await bot.send_photo(chat_id, photo=img_data, caption=msg,
                                                                 parse_mode='HTML')
                                elif str(trx_details['Transaction Type']) == 'Received NFT':
                                    Operation = str(trx_details['Transaction Type']).upper()
                                    Name = '<b>Name:</b> <a href="https://tonviewer.com/' + trx_details[
                                        'NFT Address'] + '">' + str(trx_details['NFT Name']) + '</a>'
                                    fromid = '<b>From:</b> <a href="https://tonviewer.com/' + trx_details[
                                        'Sender Address'] + '">' + format_wallets(
                                        trx_details['Sender Address']) + '</a>'
                                    img_data = await fetch_image(trx_details['Imagelink'])

                                    for chat_id in Wallets[str(response_data['params']["account_id"])]['chats']:
                                        notfy = Wallets[str(response_data['params']["account_id"])]['notifications'][
                                            chat_id]
                                        if str(notfy[1]) == 'True':
                                            header = Wallets[str(response_data['params']["account_id"])]['tag'][chat_id]
                                            msg = '<a href="https://tonviewer.com/' + str(response_data['params'][
                                                                                              "account_id"]) + '">' + header + '</a>\n' + Operation + '\n' + Name + '\n' + fromid
                                            await bot.send_photo(chat_id, photo=img_data, caption=msg,
                                                                 parse_mode='HTML')

                                        # --------------------
                                        # ----------Sent-------------
                                elif str(trx_details['Transaction Type']) == 'Sent Token':
                                    price = int(trx_details['Amount']) / 1000000000
                                    Operation = '<a href="https://tonviewer.com/transaction/' + trx_details[
                                        'TXid'] + '">SENT: </a>' + str(price) + ' <a href="https://tonviewer.com/' + \
                                                trx_details['Token Address'] + '">' + str(
                                        trx_details['Token Name']) + '</a>'

                                    # Name = '<b>Amount:</b> '
                                    tokenAdress = trx_details['Token Address']
                                    tokenchart = chart(str(tokenAdress), 1)
                                    fromid = 'To:' + ' <a href="https://tonviewer.com/' + trx_details[
                                        'Receiver Address'] + '">' + format_wallets(
                                        trx_details['Receiver Address']) + '</a>'

                                    for i, chat_id in enumerate(
                                            Wallets[str(response_data['params']["account_id"])]['chats']):
                                        notfy = Wallets[str(response_data['params']["account_id"])]['notifications'][
                                            chat_id]
                                        print(notfy)
                                        if str(notfy[2]) == 'True':
                                            usser = await readUserdata(
                                                Wallets[str(response_data['params']["account_id"])]['users'][i])
                                            dolarbal = None
                                            if str(usser[2]).lower() == 'true':
                                                tonPrice = dolarPricing(tokenAdress)
                                                dolarbal = round(
                                                    (float(tonPrice['rates'][tokenAdress]['prices']['USD']) * price), 2)
                                            if dolarbal:
                                                Operation += f' ({dolarbal} $)'
                                            header = Wallets[str(response_data['params']["account_id"])]['tag'][chat_id]
                                            msg = '👨‍💻' + '<a href="https://tonviewer.com/' + str(
                                                response_data['params'][
                                                    "account_id"]) + '">' + header + '</a> 💼' + '\n ➡️ ' + Operation + '\n' + fromid
                                            # await bot.send_message(chat_id, msg, parse_mode='HTML',disable_web_page_preview=True)
                                            await bot.send_photo(chat_id, photo=tokenchart, caption=msg,
                                                                 parse_mode='HTML')
                                elif str(trx_details['Transaction Type']) == 'Sent TON':
                                    price = int(trx_details['Amount']) / 1000000000
                                    Operation = '<a href="https://tonviewer.com/transaction/' + trx_details[
                                        'TXid'] + '">SENT: </a>' + str(price) + ' ' + str(trx_details['Token Name 2'])

                                    # Name = '<b>Amount:</b> '
                                    fromid = 'To:' + ' <a href="https://tonviewer.com/' + trx_details[
                                        'Receiver Address'] + '">' + format_wallets(
                                        trx_details['Receiver Address']) + '</a>'

                                    for i, chat_id in enumerate(
                                            Wallets[str(response_data['params']["account_id"])]['chats']):
                                        notfy = Wallets[str(response_data['params']["account_id"])]['notifications'][
                                            chat_id]
                                        print(notfy)
                                        if str(notfy[2]) == 'True':
                                            usser = await readUserdata(
                                                Wallets[str(response_data['params']["account_id"])]['users'][i])
                                            dolarbal = None
                                            if str(usser[2]).lower() == 'true':
                                                tonPrice = livetonprice()
                                                dolarbal = round((float(tonPrice) * price), 2)
                                            if dolarbal:
                                                Operation += f' ({dolarbal} $)'
                                            header = Wallets[str(response_data['params']["account_id"])]['tag'][chat_id]
                                            msg = '👨‍💻' + '<a href="https://tonviewer.com/' + str(
                                                response_data['params'][
                                                    "account_id"]) + '">' + header + '</a> 💼' + '\n ➡️ ' + Operation + '\n' + fromid
                                            await bot.send_message(chat_id, msg, parse_mode='HTML',
                                                                   disable_web_page_preview=True)
                                            # --------------------------
                                        # ----------Recieved-------------
                                elif str(trx_details['Transaction Type']) == 'Received Token':
                                    price = int(trx_details['Amount']) / 1000000000
                                    Operation = '<a href="https://tonviewer.com/transaction/' + trx_details[
                                        'TXid'] + '">RECEIVED: </a>' + str(price) + ' <a href="https://tonviewer.com/' + \
                                                trx_details['Token Address'] + '">' + str(
                                        trx_details['Token Name']) + '</a>'

                                    # Name = '<b>Amount:</b> '
                                    tokenAdress = trx_details['Token Address']
                                    tokenchart = chart(str(tokenAdress), 1)
                                    fromid = '<b>From: </b>' + ' <a href="https://tonviewer.com/' + trx_details[
                                        'Sender Address'] + '">' + format_wallets(
                                        trx_details['Sender Address']) + '</a>'

                                    for i, chat_id in enumerate(
                                            Wallets[str(response_data['params']["account_id"])]['chats']):
                                        notfy = Wallets[str(response_data['params']["account_id"])]['notifications'][
                                            chat_id]
                                        print(notfy)
                                        if str(notfy[3]) == 'True':
                                            usser = await readUserdata(
                                                Wallets[str(response_data['params']["account_id"])]['users'][i])
                                            dolarbal = None
                                            if str(usser[2]).lower() == 'true':
                                                tonPrice = dolarPricing(tokenAdress)
                                                dolarbal = round(
                                                    (float(tonPrice['rates'][tokenAdress]['prices']['USD']) * price), 2)
                                            if dolarbal:
                                                Operation += f' ({dolarbal} $)'
                                            header = Wallets[str(response_data['params']["account_id"])]['tag'][chat_id]
                                            msg = '👨‍💻' + '<a href="https://tonviewer.com/' + str(
                                                response_data['params'][
                                                    "account_id"]) + '">' + header + '</a> 💼' + '\n  ⬅️' + Operation + '\n' + fromid
                                            # await bot.send_message(chat_id, msg, parse_mode='HTML',disable_web_page_preview=True)
                                            await bot.send_photo(chat_id, photo=tokenchart, caption=msg,
                                                                 parse_mode='HTML')

                                elif str(trx_details['Transaction Type']) == 'Received TON':
                                    price = int(trx_details['Amount']) / 1000000000
                                    Operation = '<a href="https://tonviewer.com/transaction/' + trx_details[
                                        'TXid'] + '">Received:</a> ' + str(price) + ' ' + str(
                                        trx_details['Token Name 2'])

                                    fromid = '<b>From: </b>' + ' <a href="https://tonviewer.com/' + trx_details[
                                        'Sender Address'] + '">' + format_wallets(
                                        trx_details['Sender Address']) + '</a>'

                                    for i, chat_id in enumerate(
                                            Wallets[str(response_data['params']["account_id"])]['chats']):
                                        notfy = Wallets[str(response_data['params']["account_id"])]['notifications'][
                                            chat_id]
                                        print(notfy)
                                        if str(notfy[3]) == 'True':
                                            usser = await readUserdata(
                                                Wallets[str(response_data['params']["account_id"])]['users'][i])
                                            dolarbal = None
                                            if str(usser[2]).lower() == 'true':
                                                tonPrice = livetonprice()
                                                dolarbal = round((float(tonPrice) * price), 2)
                                            if dolarbal:
                                                Operation += f' ({dolarbal} $)'
                                            header = Wallets[str(response_data['params']["account_id"])]['tag'][chat_id]
                                            msg = '👤' + '<a href="https://tonviewer.com/' + str(response_data['params'][
                                                                                                    "account_id"]) + '">' + header + '</a> 💼' + '\n  ⬅️' + Operation + '\n' + fromid
                                            await bot.send_message(chat_id, msg, parse_mode='HTML',
                                                                   disable_web_page_preview=True)
                                        # --------------------------
                                        # ----------SWAP-------------
                                elif str(trx_details['Transaction Type']) == 'Sent Token Swap':
                                    Operation = '💫 <a href="https://tonviewer.com/transaction/' + trx_details[
                                        'TXid'] + '">SWAP </a>\U0000200E \n'
                                    Amountton = int(trx_details['Amount Ton']) / 1000000000
                                    Ammounttoken = round(float(trx_details['Amount token']) / 1000000000, 4)
                                    tokenName = trx_details['Token Name']
                                    tokenAdress = trx_details['Token Address']
                                    tokenchart = chart(str(tokenAdress), 1)
                                    pool = Getpools(tokenAdress)
                                    fromid = f"👉️ <b>Sent:</b> {Amountton} TON\n👈️ <b>Received:</b> {Ammounttoken} <a href=\"https://tonviewer.com/{trx_details['Token Address']}\"> {tokenName}</a>"
                                    geckoterminal = '\U0000200E \n🦎 <b>Check on:</b> <a href="https://www.geckoterminal.com/ton/pools/' + pool + '">GeckoTerminal </a>\n'

                                    for chat_id in Wallets[str(response_data['params']["account_id"])]['chats']:
                                        notfy = Wallets[str(response_data['params']["account_id"])]['notifications'][
                                            chat_id]
                                        if str(notfy[0]) == 'True':
                                            header = Wallets[str(response_data['params']["account_id"])]['tag'][chat_id]
                                            msg = '👨‍💻 <a href="https://tonviewer.com/' + str(response_data['params'][
                                                                                                  "account_id"]) + '">' + header + '</a>\n' + Operation + '\n' + fromid + '\n' + geckoterminal
                                            # await bot.send_message(chat_id, msg, parse_mode='HTML',disable_web_page_preview=True)
                                            await bot.send_photo(chat_id, photo=tokenchart, caption=msg,
                                                                 parse_mode='HTML')
                                elif str(trx_details['Transaction Type']) == 'Received Token Swap':
                                    Operation = '💫 <a href="https://tonviewer.com/transaction/' + trx_details[
                                        'TXid'] + '">SWAP </a>‎ \n'
                                    Amountton = int(trx_details['Amount Ton']) / 1000000000
                                    Ammounttoken = round(float(trx_details['Amount token']) / 1000000000, 4)
                                    tokenName = trx_details['Token Name']
                                    tokenAdress = trx_details['Token Address']
                                    tokenchart = chart(str(tokenAdress), 1)
                                    fromid = f'👉 <b>Sent:</b> {Ammounttoken} <a href="https://tonviewer.com/{tokenAdress}"> {tokenName}</a>\n👈 <b>Received:</b> {Amountton} TON '
                                    pool = Getpools(tokenAdress)
                                    geckoterminal = '\U0000200E \n🦎 <b>Check on:</b> <a href="https://www.geckoterminal.com/ton/pools/' + pool + '">GeckoTerminal </a>\n'

                                    for chat_id in Wallets[str(response_data['params']["account_id"])]['chats']:
                                        notfy = Wallets[str(response_data['params']["account_id"])]['notifications'][
                                            chat_id]
                                        if str(notfy[0]) == 'True':
                                            header = Wallets[str(response_data['params']["account_id"])]['tag'][chat_id]
                                            msg = '👨‍💻 <a href="https://tonviewer.com/' + str(response_data['params'][
                                                                                                  "account_id"]) + '">' + header + '</a>\n' + Operation + '\n' + fromid + '\n' + geckoterminal
                                            # await bot.send_message(chat_id, msg, parse_mode='HTML',disable_web_page_preview=True)
                                            await bot.send_photo(chat_id, photo=tokenchart, caption=msg,
                                                                 parse_mode='HTML')
                                elif str(trx_details['Transaction Type']) == 'Sent TON Swap':
                                    Operation = '💫 <a href="https://tonviewer.com/transaction/' + trx_details[
                                        'TXid'] + '">SWAP </a>‎ \n'
                                    Amountton = int(trx_details['Amount Ton']) / 1000000000
                                    Ammounttoken = round(float(trx_details['Amount token']) / 1000000000, 4)
                                    tokenName = trx_details['Token Name']
                                    tokenAdress = trx_details['Token Address']
                                    tokenchart = chart(str(tokenAdress), 1)
                                    fromid = f'👉 <b>Sent:</b>  {Amountton} TON \n👈 <b>Received:</b> {Ammounttoken} <a href="https://tonviewer.com/{tokenAdress}"> {tokenName}</a>'

                                    for chat_id in Wallets[str(response_data['params']["account_id"])]['chats']:
                                        notfy = Wallets[str(response_data['params']["account_id"])]['notifications'][
                                            chat_id]
                                        if str(notfy[0]) == 'True':
                                            header = Wallets[str(response_data['params']["account_id"])]['tag'][chat_id]
                                            msg = '👨‍💻 <a href="https://tonviewer.com/' + str(response_data['params'][
                                                                                                  "account_id"]) + '">' + header + '</a>\n' + Operation + '\n' + fromid
                                            # await bot.send_message(chat_id, msg, parse_mode='HTML',disable_web_page_preview=True)
                                            await bot.send_photo(chat_id, photo=tokenchart, caption=msg,
                                                                 parse_mode='HTML')
                                elif str(trx_details['Transaction Type']) == 'Received TON Swap':
                                    Operation = '💫 <a href="https://tonviewer.com/transaction/' + trx_details[
                                        'TXid'] + '">SWAP </a>‎ \n'
                                    Amountton = int(trx_details['Amount Ton']) / 1000000000
                                    Ammounttoken = round(float(trx_details['Amount token']) / 1000000000, 4)
                                    tokenName = trx_details['Token Name']
                                    tokenAdress = trx_details['Token Address']
                                    tokenchart = chart(str(tokenAdress), 1)
                                    fromid = f'👉 <b>Sent:</b> {Ammounttoken} <a href="https://tonviewer.com/{tokenAdress}"> {tokenName}\n👈 <b>Received:</b> {Amountton} TON</a>'

                                    for chat_id in Wallets[str(response_data['params']["account_id"])]['chats']:
                                        notfy = Wallets[str(response_data['params']["account_id"])]['notifications'][
                                            chat_id]
                                        if str(notfy[0]) == 'True':
                                            header = Wallets[str(response_data['params']["account_id"])]['tag'][chat_id]
                                            msg = '👨‍💻 <a href="https://tonviewer.com/' + str(response_data['params'][
                                                                                                  "account_id"]) + '">' + header + '</a>\n' + Operation + '\n' + fromid
                                            # await bot.send_message(chat_id, msg, parse_mode='HTML',disable_web_page_preview=True)
                                            await bot.send_photo(chat_id, photo=tokenchart, caption=msg,
                                                                 parse_mode='HTML')
                                            # ----------------------------------
                    except json.JSONDecodeError:
                        print("Received non-JSON response:", response)
        except Exception as e:
            print(f"Connection closed, attempting to reconnect caused by {e}")
            await asyncio.sleep(5)

async def main():
    while True:
        try:
            await asyncio.gather(
                bot.polling(),
                track_wallets_websocket(bot)
            )
        except KeyboardInterrupt:
            print("Program stopped by user.")
            break  # Exit the loop on Ctrl+C
        except Exception as e:
            print(f"An error occurred: {e}. Restarting...")
            # Here you might want to add a delay before restarting
            continue


if __name__ == "__main__":
    asyncio.run(main())
