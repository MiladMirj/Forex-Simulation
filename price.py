import random
from datetime import datetime


def price_generator(last_bid_price, last_ask_price, first_run=False):
    """
    Generates a new bid and ask price based on the last prices and a random offset.

    Args:
        last_bid_price (float): The last recorded bid price.
        last_ask_price (float): The last recorded ask price.
        first_run (bool): If True, generates initial random prices within a range; 
                          if False, generates new prices based on the last bid and ask prices.

    Returns:
        tuple: A tuple containing the new bid price, new ask price, and the current timestamp.
    """
    if first_run:
        new_bid_price = random.uniform(.9, 1.2)
        new_ask_price = new_bid_price + random.uniform(0.0001, 0.01)
    else:
        ten_percent_bid = last_bid_price * 0.1
        ten_percent_ask = last_ask_price * 0.1
        ten_percent = (ten_percent_bid + ten_percent_ask) / 2
        random_offset = random.uniform(-ten_percent, ten_percent)
        new_bid_price = round(last_bid_price + random_offset, 4)
        new_ask_price = round(last_ask_price + random_offset, 4)
        
    new_bid_price = max(new_bid_price, 0.0001)
    new_ask_price = max(new_ask_price, 0.0001)
    
    current_time = datetime.now()
    return new_bid_price, new_ask_price, current_time

def price_generator_thread(queue, stop_event, interval=5, first_run=False):
    """
    Continuously generates and updates bid/ask prices in a separate thread.

    Args:
        queue (Queue): A queue object to store the generated prices.
        stop_event (Event): An event used to stop the thread when needed.
        interval (int): Time interval (in seconds) between price updates.
        first_run (bool): If True, generates the first set of prices; otherwise, it updates prices.
    """
    last_bid_price = 0
    last_ask_price = 0
    while not stop_event.is_set():
        new_bid_price, new_ask_price, current_time = price_generator(last_bid_price, last_ask_price, first_run)
        if not first_run:
            queue.put((new_bid_price, new_ask_price, current_time))
        last_bid_price = new_bid_price
        last_ask_price = new_ask_price
        first_run = False
        stop_event.wait(interval)


def process_price(prices):
    """
    Processes a list of price dictionaries to extract key statistics.

    Args:
        prices (list): A list of price dictionaries, each containing 'ask', 'bid', and 'time' keys.

    Returns:
        tuple: A tuple containing the maximum ask price, minimum ask price, 
               opening ask price, closing ask price, and the time of the last price.
    """
    ask_prices = [price['ask'] for price in prices]
    bid_prices = [price['bid'] for price in prices]
    max_ask_price = max(ask_prices)
    min_ask_price = min(ask_prices)
    max_bid_price = max(bid_prices)
    min_bid_price = min(bid_prices)
    open_ask_price = ask_prices[0]
    open_bid_price = bid_prices[0]
    close_ask_price = ask_prices[-1]
    close_bid_price = bid_prices[-1]
    end_time = prices[-1]['time']
    return (max_ask_price, min_ask_price, open_ask_price, close_ask_price, end_time)       


