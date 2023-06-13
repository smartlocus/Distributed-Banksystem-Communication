import random
import json
import os
import sys
import time
from networking.udpSocket import udp_socket


# Define a list of stocks with their ticker symbols and initial prices
stocks = [
    {"symbol": "VW", "price": 170.0},
    {"symbol": "KIA", "price": 3000.0},
    {"symbol": "AUDI", "price": 400.0},
    {"symbol": "BMW", "price": 5000.0},
]


SERVER_HOSTNAME = os.environ.get("SERVER_HOSTNAME", "127.0.0.1")
SERVER_PORT = int(os.environ.get("SERVER_PORT", "6789"))




while True:
    # Simulate the prices of the stocks
    for stock in stocks:
        # Generate a random percentage change between -1% and +1%
        percent_change = random.uniform(-0.01, 0.01)
        # Calculate the new price based on the percent change
        new_price = stock["price"] * (1 + percent_change)
        # Update the stocks's price
        stock["price"] = new_price

    # Print the updated prices of the stocks
    print("Updated prices of stocks:")
    for stock in stocks:
        print(f"{stock['symbol']}: {stock['price']}")

    message = json.dumps(stocks)

    try:
        udp_client = udp_socket(SERVER_HOSTNAME, SERVER_PORT)
        start_time= time.time()
        response_server = udp_client.send(SERVER_HOSTNAME, SERVER_PORT, message, 4096)
        end_time= time.time()
        roundtriptime= end_time - start_time
        print("Response from the server => %s" % response_server)
        print("Round-trip time => %.2f ms" % (roundtriptime * 1000))
    except Exception as e:          # catch execption for catching the error
        print(f"Error occurred while sending/receiving data: {e}")
        sys.exit(1)

    #user_input = input("Do you want to quit? (y/n)")
    #if user_input == "y":
         #break
         # 
    time.sleep(200) 