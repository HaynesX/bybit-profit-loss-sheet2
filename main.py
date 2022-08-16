import time
import traceback
from pybit import inverse_perpetual
from time import sleep
from datetime import datetime
import gspread
import json
from oauth2client.service_account import ServiceAccountCredentials
import pytz
import telebot
import os

TELEGRAM_SECRET_KEY = os.getenv('TELEGRAM_SECRET_KEY')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

BYBIT_SECRET_KEY = os.getenv('BYBIT_SECRET_KEY')
BYBIT_SECRET = os.getenv('BYBIT_SECRET')



PNL_DATA_JSON_PATH = "pnlData/haynes-bybit-b58869a98ed4.json"


bot = telebot.TeleBot(TELEGRAM_SECRET_KEY)

scope = ["https://spreadsheets.google.com/feeds","https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive.file", "https://www.googleapis.com/auth/drive"]

creds = ServiceAccountCredentials.from_json_keyfile_name(PNL_DATA_JSON_PATH, scope)

googleClient = gspread.authorize(creds)

sheet = googleClient.open("Trades - Bybit").worksheet("Multi EMA/MA 17 min Bybit")

session = inverse_perpetual.HTTP(
    endpoint='https://api.bybit.com', 
    api_key=BYBIT_SECRET_KEY,
    api_secret=BYBIT_SECRET
)



def poll_bybit():
    while True:
        time.sleep(7)
        print("Starting up bot.")
        bot.send_message("-670589159", "Starting up bot.", parse_mode="HTML", disable_web_page_preview=True)
        try:
            while True:
                with open('pnlData/data.json') as json_file:
                    calculatedProfitAndLoss = json.load(json_file)
                    listOfKeys = list(calculatedProfitAndLoss.keys())

                    if len(listOfKeys) == 0:
                        filterDate = datetime.strptime('Aug 11 2022  1:00AM', '%b %d %Y %I:%M%p')
                        filterDateTimestamp = datetime.timestamp(filterDate)
                    else:
                        filterDateTimestamp = calculatedProfitAndLoss[listOfKeys[0]]["Close_Time"]
                    
                    filterDateTimestampEnd = round(datetime.timestamp(datetime.now()))
                    

                time.sleep(3)

                allResults = []
                oldResults = []
                combinedResults = []

                for eachKey in calculatedProfitAndLoss:
                    oldResult = {
                        "order_id": calculatedProfitAndLoss[eachKey]["orderID"],
                        "side": calculatedProfitAndLoss[eachKey]["side"],
                        "avg_entry_price": calculatedProfitAndLoss[eachKey]["avgEntryPrice"],
                        "avg_exit_price": calculatedProfitAndLoss[eachKey]["avgClosePrice"],
                        "created_at": calculatedProfitAndLoss[eachKey]["Close_Time"],
                        "closed_pnl": calculatedProfitAndLoss[eachKey]["P&L (BTC)"],
                    }
                    oldResults.append(oldResult)

                profitAndLossData = ""
                pageIncrement = 0
                while profitAndLossData != None:
                    pageIncrement += 1

                    profitAndLossData = session.closed_profit_and_loss(symbol="BTCUSD", limit=50, page=pageIncrement, start_time=filterDateTimestamp, end_time=filterDateTimestampEnd)["result"]["data"]

                    if profitAndLossData == None:
                        continue

                    for eachResult in profitAndLossData:
                        if eachResult["order_id"] not in calculatedProfitAndLoss:
                            allResults.append(eachResult)
                            
                    
                    time.sleep(3)
                
                allResults.reverse()

                for eachResult in oldResults:
                    combinedResults.append(eachResult)

                for eachResult in allResults:
                    combinedResults.append(eachResult)

                startingBalance = 1.04456380

                allRows = []

                cumulativeBalance = startingBalance
                cumulativeProfitAndLoss = 0
                for eachResult in combinedResults:
                    orderID = eachResult["order_id"]
                    side = eachResult["side"]
                    avgEntryPrice = eachResult["avg_entry_price"]
                    avgClosePrice = eachResult["avg_exit_price"]
                    closedProfitAndLoss = eachResult["closed_pnl"]
                    closedProfitAndLossPercentage = (closedProfitAndLoss / cumulativeBalance) * 100 #Needs to multiply by 100 in spreadsheet
                    oldBalance = cumulativeBalance
                    cumulativeBalance += closedProfitAndLoss
                    cumulativeProfitAndLoss += closedProfitAndLoss
                    cumulativeProfitAndLossPercentage = (cumulativeProfitAndLoss / startingBalance) * 100 #Needs to multiply by 100 in spreadsheet
                    created_at = datetime.fromtimestamp(eachResult["created_at"])
                    created_at_string = created_at.strftime("%d/%m/%Y, %H:%M:%S")
                    winOrLoss = ""

                    if side == "Buy":
                        side = "Short"
                    else:
                        side = "Long"
                        
                    if closedProfitAndLoss < 0:
                        winOrLoss = "Loss"
                    else:
                        winOrLoss = "Win"
                        
                        
                    if orderID not in calculatedProfitAndLoss:
                        calculatedProfitAndLoss[orderID] = {"orderID": orderID, "Close_Time": eachResult['created_at'], "side": side, "avgEntryPrice": avgEntryPrice, "avgClosePrice": avgClosePrice, "P&L (BTC)": closedProfitAndLoss, "P&L %": closedProfitAndLossPercentage, "Cumulative P&L (BTC)": cumulativeProfitAndLoss, "Cumulative P&L %": cumulativeProfitAndLossPercentage, "Previous Balance": oldBalance, "New Balance": cumulativeBalance, "Created at": created_at_string, "WinOrLoss": winOrLoss}

                        allRows.append([orderID, created_at_string, side, avgEntryPrice, avgClosePrice, closedProfitAndLoss, closedProfitAndLossPercentage, cumulativeProfitAndLoss, cumulativeProfitAndLossPercentage, oldBalance, cumulativeBalance, winOrLoss, "", avgEntryPrice, "", "", "", closedProfitAndLossPercentage, "=(Q4-R4)/ABS(R4)"])
                
                

                if len(allRows) > 0:
                    print("New P&L Found. Adding to Google Sheet.")
                    allRows.reverse()
                    sheet.insert_rows(allRows, row=4, value_input_option='USER_ENTERED')

                    allRows.reverse()

                    for eachRow in allRows:
                        
                        

                        telegramMessage = f"""
    <b>Trade added to P&L Sheet</b>
                        
    Side: <b>{eachRow[2]}</b>
    Entry: <b>{eachRow[3]}</b>
    Exit: <b>{eachRow[4]}</b>
    P&L: <b>{round(eachRow[6], 2)}%</b>

    <b>{eachRow[1]}</b>
    <b><a href="https://docs.google.com/spreadsheets/d/1gNFpHEs0YXCYgrdGnk-5b8DuOLrwBKtDkfxxRK0GgVc">Google Sheet</a></b>
    """

                        bot.send_message(TELEGRAM_CHAT_ID, telegramMessage, parse_mode="HTML", disable_web_page_preview=True)

                        time.sleep(3)

                    with open("pnlData/data.json", "w") as outfile:
                        json.dump(calculatedProfitAndLoss, outfile)

        except Exception as e:
            print("ERROR!")
            print(e)
            print(traceback.format_exc())
            bot.send_message("-670589159", e, disable_web_page_preview=True)




def main():
    poll_bybit()
    



if __name__ == "__main__":
    main()