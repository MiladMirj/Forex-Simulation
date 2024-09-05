# #                                                        Code Surge !
# #                                                        Code Surge !
# #                                                        Code Surge !
# #                                                        Code Surge !
#                                                   https://github.com/MiladMirj
#                                           https://www.linkedin.com/in/milad-mirjalili-15147421a/
#                                               https://www.youtube.com/watch?v=7O3hJp5mhF8
#
"""
This application simulates real-time trading for the EUR/USD currency pair.
It allows users to initiate, monitor, and close trades, while providing real-time updates on equity, margin, and other trading metrics.
The app is designed with a graphical user interface (GUI) built using PyQt5 and provides visual updates on price changes via candlestick charts using Plotly.
In order to run this script it's required to install the following libraries:
1- pandas: For managing and processing trade history and data.
2- PyQt5: For building the GUI components of the application.
3- plotly: For generating candlestick and line charts for price visualization.

"""

import sys
import threading
import time
from queue import Queue, Empty
import pandas as pd
import plotly.graph_objects as go
from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QTableWidgetItem, QButtonGroup, QRadioButton 
from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtCore import QTimer
from ui_main_window import Ui_MainWindow  
from price import price_generator_thread, process_price
from utility import update_candlestick_chart, is_float, format_currency




class MainWindow(QMainWindow, Ui_MainWindow):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.make_center()
        
        # Processing UI 
        self.radio_buy = self.findChild(QRadioButton, 'radio_buy')
        self.radio_sell = self.findChild(QRadioButton, 'radio_sell')
        self.radio_candle = self.findChild(QRadioButton, 'radio_candle')
        self.radio_line = self.findChild(QRadioButton, 'radio_line')
        self.button_group = QButtonGroup(self)
        self.button_group.addButton(self.radio_buy)
        self.button_group.addButton(self.radio_sell)
        self.button_group2 = QButtonGroup(self)
        self.button_group2.addButton(self.radio_candle)
        self.button_group2.addButton(self.radio_line)
        self.radio_candle.setChecked(True)
        self.radio_buy.setChecked(True)
        self.web_view = QWebEngineView(self.plotly_graph)
        layout = QVBoxLayout(self.plotly_graph)
        layout.addWidget(self.web_view)
        self.btn_open.clicked.connect(self.initiate_trade)
        self.btn_deposit.clicked.connect(self.deposit)
        self.btn_close.clicked.connect(self.close_trade)

        # Initializing plotly figures
        self.fig = go.Figure()
        self.fig2 = go.Figure()
        self.fig.add_trace(go.Candlestick(x=[], open=[], high=[], low=[], close=[]))
        self.fig2.add_trace(go.Scatter(x=[], y=[], mode='lines', name='Close Price'))
        self.fig.update_xaxes(type='date', title_text='Time')
        self.fig2.update_xaxes(type='date', title_text='Time')
        self.fig.update_yaxes(title_text='Price')
        self.fig2.update_yaxes(title_text='Close Price')
        self.fig.update_layout(title='Candlestick Chart', xaxis_rangeslider_visible=False)

        # Initializing variables
        self.trade_in_progress = False
        self.last_ask_price = None
        self.last_bid_price = None
        self.balance = float(self.text_balance.toPlainText().replace("$", ''))
        self.lable_balance.setText("Balance: " + format_currency(self.balance))
        self.trade_history = []
        self.candlesticks = []
        self.prices = []
        self.temp_price = []

        # Using Thread
        self.price_queue = Queue()
        self.stop_event = threading.Event()
        self.thread = threading.Thread(target=price_generator_thread,
                                       args=(self.price_queue, self.stop_event, 5, True))
        self.thread.start()
        self.start_time = time.time()
        self.temp_time = self.start_time

        # Using QTimer
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_data)
        self.timer.start(1000)  # Update every second
        self.temp_time = time.time()
        self.begin_time = time.time()

    
    def deposit(self):
        """
        Handles the deposit of funds into the account balance.
        """
        if self.trade_in_progress:
            self.update_message("Trading in progress ...")
            return

        input_balance = self.text_balance.toPlainText().replace("$", '')
        if not is_float(input_balance) :
            self.update_message("Wrong Number !")
            return
        if float(self.text_balance.toPlainText()) < 0:
            self.update_message("Wrong Number !")
            return
        self.balance = float(self.text_balance.toPlainText())
        self.lable_balance.setText("Balance: " + format_currency(self.balance))
        self.update_message(f"Depositing {format_currency(self.balance)}")
        
 
    def initiate_trade(self):
        """
        Initiates a new trade based on user input.
        """
        if self.trade_in_progress: 
            self.update_message("Trade in progress")
            return
        if self.last_ask_price is None: 
            self.update_message("Waiting for new Price ...")
            return   
        
        self.base_curr = 'euro'
        self.quote_curr = 'usd'
        units_to_trade_string = self.text_trade.toPlainText()
        
        if not is_float(units_to_trade_string):
            self.update_message("Wrong Number !")
            return
        self.units_to_trade = float(self.text_trade.toPlainText())
        if self.units_to_trade <=0 :
            self.update_message("Wrong Number !")
            return

        self.mode = 'long' if self.radio_buy.isChecked() else 'short'
            
        self.margin, _ = self.margin_cal(self.mode, self.base_curr, self.quote_curr, 
                                    self.last_bid_price, self.last_ask_price, self.units_to_trade)
        if self.balance < self.margin:
            self.update_message("Not enough Funds !\n, Increase balance to at least " + format_currency(self.margin))
            return

        self.trade_in_progress = True
        self.enter_position_bid_price = self.last_bid_price
        self.enter_position_ask_price = self.last_ask_price
        if self.mode == 'long':
            trade_msg = 'Buying'
            trade_msg2 = 'ASK price of'
            price = format_currency(self.enter_position_ask_price)
        else:
            trade_msg = 'Selling'
            trade_msg2 = 'BID price of'
            price = format_currency(self.enter_position_bid_price)

        msg = f"New Trade opens: \n {trade_msg} {format_currency(self.units_to_trade, '€')} with\n {trade_msg2} : {price} \n "
        self.update_message(msg, True)

    def trade(self, mode, base_curr, quote_curr, units_to_trade):
        """
        Executes and evaluates a trade based on the current market conditions.
        Args:
        mode (str): The trade mode, either 'long' (buy) or 'short' (sell).
        base_curr (str): The base currency in the trade pair.
        quote_curr (str): The quote currency in the trade pair.
        units_to_trade (float): The number of units involved in the trade.
        """
        profit = -1
        if mode == 'long': 
            bid_ask_price_diff = self.last_bid_price - self.enter_position_ask_price
            if bid_ask_price_diff > 0:
                profit = 1
        else:
            bid_ask_price_diff = self.last_ask_price - self.enter_position_bid_price
            if bid_ask_price_diff < 0 :
                profit = 1

        # Calculate price difference in pips        
        bid_ask_price_diff_pips = round(bid_ask_price_diff * 10000, 4)
        pip = 0.0001
        back_to_usd = 1   
        self.float_pl = profit * abs(bid_ask_price_diff_pips) * pip * units_to_trade * back_to_usd
        self.equity = self.balance + self.float_pl
        self.used_margin, position_value = self.margin_cal(mode, base_curr, quote_curr, self.last_bid_price, self.last_ask_price, units_to_trade)
        self.margin_level = abs(round(self.equity / self.used_margin * 100, 2))
        self.free_margin = self.equity - self.used_margin
        self.realize_PL = 0
        status = [format_currency(self.balance), format_currency(self.equity),
                     format_currency(self.float_pl), format_currency(self.used_margin),
                      format_currency(self.free_margin), str(self.margin_level) + '%', format_currency(self.realize_PL)]
        temp_list = self.trade_history.copy()
        temp_list.append(status)
        df = pd.DataFrame(temp_list, columns=['Balance', 'Equity', 'Float_PL', 'Used_Margin', 'Free_Margin', 'Margin_Level', 'Realized_PL'])
        self.load_dataframe(df, self.table_status)
        if self.margin_level < 100:
            self.update_message("WARNING !! \nMargin Call !!\n Margin LEVEL below 100%")
        if self.margin_level < 50:
            self.update_message("STOP OUT LEVEL REACHED !!\n MARGIN LEVEL BELOW 50 %\n LIQUIDATION")
            self.close_trade()

    
    def close_trade(self):
        """
        Closes the currently active trade and updates the account balances.
        """
        if not self.trade_in_progress:
            self.update_message("No Trade in progress", True)
            return

        self.balance = self.equity
        self.free_margin = self.equity
        self.realize_PL = self.float_pl
        self.used_margin = 0
        self.float_pl = 0
        self.margin_level = 0
        status = [format_currency(self.balance), format_currency(self.equity),
                     format_currency(self.float_pl), format_currency(self.used_margin),
                      format_currency(self.free_margin), str(self.margin_level) + '%', self.realize_PL]

        self.trade_history.append(status)
        df = pd.DataFrame(self.trade_history, columns=['Balance', 'Equity', 'Float_PL', 'Used_Margin', 'Free_Margin', 'Margin_Level','Realized_Pl'])

        self.load_dataframe(df, self.table_status)
        self.trade_in_progress = False
        self.text_balance.setText(str(self.balance))
        if self.mode == 'long':
            msg = 'with BID price of ' + format_currency(self.last_bid_price)
        else:
            msg = 'with ASK price of ' + format_currency(self.last_ask_price)
        self.update_message(f"Closing the Trade! \n {msg}")
        self.lable_balance.setText("Balance: " + format_currency(self.balance))
    
    def update_data(self):
        """
        Continuously fetches and updates the latest bid and ask prices from a price queue.
        """
        try:
            
            while True:
                try:
                    new_bid_price, new_ask_price, price_time = self.price_queue.get_nowait()
                    self.last_ask_price = new_ask_price
                    self.last_bid_price = new_bid_price
                    print(f"New Bid Price: {new_bid_price}, New Ask Price: {new_ask_price}, Time: {price_time}")
                    self.ask_price.setText("New ask price: " + str(new_ask_price))
                    self.bid_price.setText("New bid price: " + str(new_bid_price))
                    price_entry = {"ask": new_ask_price, "bid": new_bid_price, "time": price_time}
                    self.temp_price.append(price_entry)
                    if self.trade_in_progress:
                        self.trade(self.mode, self.base_curr, self.quote_curr, self.units_to_trade)
                    current_time = time.time()
                    # Drawing plots
                    if current_time - self.temp_time >= 30:
                        self.prices.append(self.temp_price)
                        max_ask_price, min_ask_price, open_ask_price, close_ask_price, candle_time = process_price(self.temp_price)
                        
                        self.candlesticks.append((candle_time, open_ask_price, close_ask_price, max_ask_price, min_ask_price))
                        self.temp_price = []
                        self.temp_time = current_time
                        if self.radio_candle.isChecked():
                            html, df = update_candlestick_chart(self.candlesticks, self.fig, 'candle')
                        else:
                            html, df = update_candlestick_chart(self.candlesticks, self.fig2, 'line')
                        self.web_view.setHtml(html)

                except Empty:
                    break

                if time.time() - self.begin_time > 500:
                    self.update_message("Market Closed ! \n Closing active trades ... ")
                    self.close_trade()
                    self.stop_timer()
                    self.stop_event.set()
                    self.thread.join()
        
        except Exception as e:
            print(f"Exception in data update: {e}")
    
    def margin_cal(self, mode, base_curr, quote_curr, bid_price, ask_price, units_to_trade):
        """
        Calculates the required margin and position value for a given trade.

        Args:
            mode (str): The type of trade ('long' or 'short').
            base_curr (str): The base currency of the trade.
            quote_curr (str): The quote currency of the trade.
            bid_price (float): The current bid price of the currency pair.
            ask_price (float): The current ask price of the currency pair.
            units_to_trade (float): The number of units to trade.

        Returns:
            tuple: The calculated margin and the total position value.
        """
        marin_rate = 0.2
        if mode=='long':
            exchange_rate = ask_price
        elif mode == 'short':
            exchange_rate = bid_price

        if base_curr.lower() != 'usd':
            position_value = exchange_rate * units_to_trade
        else:
            position_value = units_to_trade
        print('Position Value : ', format_currency(position_value))
        margin = marin_rate * position_value
        print("Used Margin : ", format_currency(margin) + " for " + str(marin_rate * 100) + " % of position size")
        return margin, position_value
    
    def load_dataframe(self, df, table):
        """
        Loads a pandas DataFrame into a QTableWidget for display.

        Args:
            df (DataFrame): The DataFrame containing data to load into the table.
            table (QTableWidget): The table widget where the data will be displayed.
        """
        table.clear()
        table.setRowCount(len(df))
        table.setColumnCount(len(df.columns))
        table.setHorizontalHeaderLabels(df.columns)
        for row in range(len(df)):
            for col in range(len(df.columns)):
                item = QTableWidgetItem(str(df.iat[row, col]))
                table.setItem(row, col, item)
    
    
    def make_center(self):
        screen = QApplication.desktop().screenNumber(QApplication.desktop().cursor().pos())
        centerPoint = QApplication.desktop().screenGeometry(screen).center()
        screen_height = QApplication.desktop().screenGeometry(screen).height()
        screen_width = QApplication.desktop().screenGeometry(screen).width()
        self.resize(int(screen_width * .9), int(screen_height * .9))
        frameGm = self.frameGeometry()
        frameGm.moveCenter(centerPoint)
        self.move(frameGm.topLeft()) 
    
    def update_message(self, msg, clear_flag=False):
        """
        Updates the status label with a new message.

        Args:
        msg (str): The message to display.
        clear_flag (bool): If True, clears the previous messages before updating.
        """
        if clear_flag:
            self.label_status.clear()
        previous_text = self.label_status.text()
        new_message = previous_text + '\n' + msg
        self.label_status.setText(new_message)

    def stop_app(self):
        """
        Stops the background thread and quits the application.
        """
        self.stop_event.set()
        self.thread.join()
        QApplication.quit()

    def start_timer(self):
        """
        Starts the timer with a 1-second interval.
        """
        self.timer.start(1000)  # Restart the timer with the same interval

    def stop_timer(self):
        self.timer.stop()  # Stop the timer

    def closeEvent(self, event):
        self.stop_event.set()
        self.thread.join()
        event.accept()
        
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())