import logging
import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import six

from datetime import date, timedelta, datetime
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, InputMediaPhoto, Update, ParseMode
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler, CallbackContext

import binance_respository

token = os.environ.get('telegram_bot_token')
last_run_bot_date = datetime.today().date()

#df_last_kline = binance_respository.get_last_kline_candle("BTCUSDT", "1d", "BNM")
#last_update_data_date = df_last_kline["OpenTime"][-1:]


df_daily = binance_respository.get_all_df("1d")
df_weekly = binance_respository.get_all_df("1w")

#print(df_daily.tail(1))
last_update_data_date = df_daily["OpenTime"][-1:].iloc[0]

#print(token)
#print(last_update_data_date)


# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)

logger = logging.getLogger(__name__)

def fixed_width(str, width):
    length = len(str)
    if (length > width):
        return str
    else:
        n = width - length
        i = 0
        while i< n:
            str = str + " "
        return str

def get_send_text(df, title):
    head = "<pre><b>" + "{:<10}".format("AssetName") + "|" +  "{:<20}".format("%VOLUME_CHANGE_1D") + "|" +  "{:<20}".format("%PRICE_CHANGE_1D") + "|" + "{:<25}".format("%NUMBER_TRADES_CHANGE_1D") + "|" + "{:<10}".format("DATE")  + "</b>\n"

    msg = title + head
    #msg.append(head)
    for i, row in df.iterrows():
        ticker = "{:<10}".format(row["AssetName"])

        vol_change_1_f= "{:.2f}".format(row["%VOLUME_CHANGE_1D"])
        vol_change_1d = "{:<20}".format(vol_change_1_f)

        price_change_f= "{:.2f}".format(row["%PRICE_CHANGE_1D"])
        price_change_1d = "{:<20}".format(price_change_f)

        numbertrades_change_f= "{:.2f}".format(row["%NUMBER_TRADES_CHANGE_1D"])
        numbertrades_change_1d = "{:<25}".format(numbertrades_change_f)

        from_date = "{:<10}".format(datetime.strftime(row["OpenTime"], "%d-%m-%Y"))

        #price_change_1d = fixed_width(str(row["%PRICE_CHANGE_1D"]), 20)
        #numbertrades_change_1d = fixed_width(str(row["%NUMBER_TRADES_CHANGE_1D"]), 30)
        #from_date = fixed_width(datetime.strftime(row["OpenTime"], "%d-%m-%Y"), 20)

        msg  = msg + ticker + "|" + vol_change_1d + "|" + price_change_1d + "|" +  numbertrades_change_1d + "|"  + from_date + "\n"
    msg = msg + "</pre>"\

    return msg

def render_mpl_table(data, col_width=3.0, row_height=0.625, font_size=14,
                     header_color='#40466e', row_colors=['#f1f1f2', 'w'], edge_color='w',
                     bbox=[0, 0, 1, 1], header_columns=0,
                     ax=None, **kwargs):
    if ax is None:
        size = (np.array(data.shape[::-1]) + np.array([0, 1])) * np.array([col_width, row_height])
        fig, ax = plt.subplots(figsize=size)
        ax.axis('off')

    mpl_table = ax.table(cellText=data.values, bbox=bbox, colLabels=data.columns, **kwargs)

    mpl_table.auto_set_font_size(False)
    mpl_table.set_fontsize(font_size)

    for k, cell in  six.iteritems(mpl_table._cells):
        cell.set_edgecolor(edge_color)
        if k[0] == 0 or k[1] < header_columns:
            cell.set_text_props(weight='bold', color='w')
            cell.set_facecolor(header_color)
        else:
            cell.set_facecolor(row_colors[k[0]%len(row_colors) ])
    return ax

def sync_data() -> None:
    global last_update_data_date, df_daily, df_weekly

    last_run_bot_date = datetime.today().date()
    #last_update_data_date = df_daily["OpenTime"][-1:].iloc[0]
    if(last_run_bot_date > last_update_data_date.date()):
        binance_respository.update_coins_listing()
        binance_respository.sync_data("1d")
        binance_respository.sync_data("1w")

        df_daily = binance_respository.get_all_df("1d")
        df_weekly = binance_respository.get_all_df("1w")

        #print(df_daily.tail(1))
        last_update_data_date = df_daily["OpenTime"][-1:].iloc[0]

def start(update: Update, context: CallbackContext) -> None:
    """Sends a message with three inline buttons attached."""
    
    cur_date = datetime.strftime(date.today(), "%d-%m-%Y")
    prev_date = datetime.strftime(date.today() - timedelta(1),  "%d-%m-%Y")
    
    keyboard = [
        [
            InlineKeyboardButton("Loại cây nến BTC hôm qua - " + prev_date, callback_data='1'),
            InlineKeyboardButton("Loại cây nến BTC hôm nay - " + cur_date, callback_data='2'),
        ],
        [InlineKeyboardButton("Các coins có chỉ số buy theo MFI, RSI", callback_data='3')],
        [InlineKeyboardButton("Các coins có chỉ số sell theo MFI, RSI", callback_data='4')],      
        [
            InlineKeyboardButton("Các coins có volume tăng đột biến", callback_data='5'),
            InlineKeyboardButton("Các coins có giá tăng đột biến", callback_data='6'),
        ]
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)

    update.message.reply_text('Please choose:', reply_markup=reply_markup)


def button(update: Update, context: CallbackContext) -> None:
    """Parses the CallbackQuery and updates the message text."""
    query = update.callback_query

    # CallbackQueries need to be answered, even if no notification to the user is needed
    # Some clients may have trouble otherwise. See https://core.telegram.org/bots/api#callbackquery
    query.answer()

    if (query.data == "1"):
        prev_date = datetime.strftime(date.today()-timedelta(1), "%Y-%m-%d")
        candle_type = binance_respository.get_candle_type(symbol="BTCUSDT", date=prev_date, all_df=df_daily)
        query.edit_message_text(text=f"<b>Mẫu nến của BTCUSDT vào ngày {prev_date} là: </b><u>"+ candle_type + "</u>", parse_mode=ParseMode.HTML)
    elif (query.data == "2"):
        prev_date = datetime.strftime(date.today(), "%Y-%m-%d")
        candle_type = binance_respository.get_candle_type(symbol="BTCUSDT", date=prev_date, all_df=df_daily)
        query.edit_message_text(text=f"<b>Mẫu nến của BTCUSDT vào ngày {prev_date} là: </b><u>"+ candle_type + "</u>", parse_mode=ParseMode.HTML)
    elif (query.data == "3"):
        prev_date = datetime.strftime(date.today()-timedelta(1), "%Y-%m-%d")
        df = binance_respository.get_buy_signal_mfi(prev_date, df_daily)

        if (df.empty):
            query.edit_message_text("<b>Không có coins nào thỏa mãn điều kiện!</b>", parse_mode=ParseMode.HTML)
        else:
            msg = get_send_text(df, "<b><u>Danh sách coins thỏa mãn điều kiện buy theo MFI14 (25) và RSI14 (30)</u></b>\n")
            query.edit_message_text(text=msg, parse_mode=ParseMode.HTML)
    elif (query.data == "4"):
        prev_date = datetime.strftime(date.today()-timedelta(1), "%Y-%m-%d")
        df = binance_respository.get_sell_signal_mfi(prev_date, df_daily)

        if (df.empty):
            query.edit_message_text("<b>Không có coins nào thỏa mãn điều kiện!</b>", parse_mode=ParseMode.HTML)
        else:
            msg = get_send_text(df, "<b><u>Danh sách coins thỏa mãn điều kiện sell theo MFI14 (80) và RSI14 (70)</u></b>\n")
            query.edit_message_text(text=msg, parse_mode=ParseMode.HTML)
    elif (query.data == "5"):
        prev_date = datetime.strftime(date.today()-timedelta(1), "%Y-%m-%d")
        df = binance_respository.get_recent_top_vol_change(prev_date, df_daily)

        if (df.empty):
            query.edit_message_text("<b>Không có coins nào thay đổi lớn về volume theo ngày!</b>", parse_mode=ParseMode.HTML)
        else:
            msg = get_send_text(df, "<b><u>Danh sách coins có thay đổi lớn về volume theo ngày</u></b>\n")
            query.edit_message_text(text=msg, parse_mode=ParseMode.HTML)

            # Generate formatted table
            render_mpl_table(df, header_columns=0, col_width=4.0)

            # Save result to image:
            plt.savefig('mytable.png')

            media_1 = InputMediaPhoto(media=open('mytable.png', 'rb'))
            #update.edited_message.re
            update.edited_message.bot.reply_photo(photo=media_1)

            #query.edit_message_media(media=media_1)

    elif (query.data == "6"):
        prev_date = datetime.strftime(date.today()-timedelta(1), "%Y-%m-%d")
        df = binance_respository.get_recent_top_price_change(prev_date, df_daily)

        if (df.empty):
            query.edit_message_text("<b>Không có coins nào thay đổi lớn về giá theo ngày!</b>", parse_mode=ParseMode.HTML)
        else:
            msg = get_send_text(df, "<b><u>Danh sách coins có thay đổi lớn về giá theo ngày</u></b>\n")
            query.edit_message_text(text=msg, parse_mode=ParseMode.HTML)

def candle_type_command(update: Update, context: CallbackContext) -> None:
    """Displays Candle Partern with Ticker and date."""

    symbol = context.args[0]
    from_date = context.args[1]

    #print(symbol)
    #print(from_date)
    candle_type = binance_respository.get_candle_type(symbol, from_date, df_daily)
    #print(candle_type)
    update.message.reply_text(text=f"<b>Mẫu nến của {symbol} vào ngày {from_date} là: </b><u>"+ candle_type + "</u>", parse_mode=ParseMode.HTML)


def help_command(update: Update, context: CallbackContext) -> None:
    """Displays info on how to use the bot."""
    update.message.reply_text("Use /start to test this bot.")


def main() -> None:
    """Start the bot."""

    # Get dataframe of daily, weekly data
    print(last_update_data_date)
    sync_data()

    # Create the Updater and pass it your bot's token.
    updater = Updater(token)

    # Get the dispatcher to register handlers
    dispatcher = updater.dispatcher

    # on different commands - answer in Telegram
    updater.dispatcher.add_handler(CommandHandler('start', start))
    updater.dispatcher.add_handler(CallbackQueryHandler(button))
    updater.dispatcher.add_handler(CommandHandler('help', help_command))
    updater.dispatcher.add_handler(CommandHandler('candle', candle_type_command))

    # Start the Bot
    updater.start_polling()

    # Run the bot until you press Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT. This should be used most of the time, since
    # start_polling() is non-blocking and will stop the bot gracefully.
    updater.idle()



if __name__ == '__main__':
    main()