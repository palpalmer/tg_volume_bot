import requests
import schedule
import time
from datetime import datetime
from telegram import Bot
from telegram.ext import Updater, CommandHandler
import os
import sys

# Токен Telegram
TELEGRAM_TOKEN = '7688373338:AAEmKtl2feOzGGr5t108yOm8KZkHpaCnnOE'
CHAT_ID = None
bot = Bot(token=TELEGRAM_TOKEN)

# ======== CHAT ID =========
def load_chat_id():
    global CHAT_ID
    try:
        with open("chat_id.txt", "r") as f:
            CHAT_ID = f.read().strip()
    except FileNotFoundError:
        CHAT_ID = None

def save_chat_id(chat_id):
    with open("chat_id.txt", "w") as f:
        f.write(str(chat_id))

# ======== DATA FUNCTION =========
def get_top_movers():
    all_coins = []

    for page in range(2, 9):  # Сторінки 2–8 (позиції 251–2000)
        url = "https://api.coingecko.com/api/v3/coins/markets"
        params = {
            'vs_currency': 'usd',
            'order': 'market_cap_desc',
            'per_page': 250,
            'page': page,
        }
        try:
            response = requests.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            all_coins.extend(data)
        except Exception as e:
            return [f"Error fetching data: {e}"]

    coins_300_2000 = all_coins[49:]  # Від 300 до 2000

    movers = []
    for coin in coins_300_2000:
        name = coin['name']
        symbol = coin['symbol'].upper()
        market_cap = coin['market_cap']
        volume = coin['total_volume']

        if market_cap and volume and volume > market_cap:
            ratio = volume / market_cap
            movers.append({
                'name': name,
                'symbol': symbol,
                'volume': volume,
                'market_cap': market_cap,
                'ratio': ratio
            })

    top_20 = sorted(movers, key=lambda x: x['ratio'], reverse=True)[:20]

    formatted = [
        f"{idx+1}. {m['name']} ({m['symbol']})\n"
        f"   Volume: ${m['volume']:,}\n"
        f"   Market Cap: ${m['market_cap']:,}\n"
        f"   Volume/Cap Ratio: {m['ratio']:.2f}\n"
        for idx, m in enumerate(top_20)
    ]

    return formatted

# ======== SENDER =========
def send_daily_report():
    load_chat_id()
    movers = get_top_movers()
    now = datetime.now().strftime("%Y-%m-%d %H:%M")

    if not movers:
        message = f"[{now}] No coins with volume > market cap today."
    else:
        message = f"[{now}] Top 20 coins (rank 300–2000) with Volume > Market Cap:\n\n" + "\n".join(movers)

    if CHAT_ID:
        try:
            bot.send_message(chat_id=CHAT_ID, text=message)
        except Exception as e:
            print(f"Error sending message: {e}")
    else:
        print("CHAT_ID not set. Send /start to bot in Telegram.")

# ======== COMMAND: /start =========
def start(update, context):
    global CHAT_ID
    CHAT_ID = update.effective_chat.id
    save_chat_id(CHAT_ID)

    welcome_message = (
        "Привіт! Я бот, який щодня відстежує монети, "
        "в яких обсяг торгів перевищує ринкову капіталізацію (з позицій 300–2000).\n\n"
        "Ти будеш отримувати звіт щодня о 16:00.\n\n"
        "Щоб отримати звіт вручну — напиши /report."
    )

    context.bot.send_message(chat_id=CHAT_ID, text=welcome_message)

# ======== COMMAND: /report =========
def report(update, context):
    movers = get_top_movers()
    now = datetime.now().strftime("%Y-%m-%d %H:%M")

    if not movers:
        message = f"[{now}] No coins with volume > market cap today."
    else:
        message = f"[{now}] Top 20 coins (rank 300–2000) with Volume > Market Cap:\n\n" + "\n".join(movers)

    context.bot.send_message(chat_id=update.effective_chat.id, text=message)

# ======== MAIN =========
def main():
    load_chat_id()
    updater = Updater(TELEGRAM_TOKEN, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("report", report))

    updater.start_polling()
    print("Bot is running... Waiting for /start.")

    schedule.every().day.at("16:00").do(send_daily_report)


while True:
        schedule.run_pending()
        time.sleep(10)

# ======== ENTRY POINT =========
if __name__ == "__main__":
    if "--send_report" in sys.argv:
        send_daily_report()
    else:
        main()
