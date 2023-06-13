import json
import os
import threading
import time
import sys
from concurrent import futures
from networking.udpSocket import udp_socket
from networking.tcpSocket import http_server
import asyncio
import thriftpy2

from thriftpy2.rpc import make_aio_server


try:
      stockportfolio_thrift= thriftpy2.load("/Server/Server/stockportfolio.thrift", module_name="stockportfolio_thrift")

except Exception as e:
         print(f"Failed to load Thrift file: {e}")
         exit(1)




class StockPortfolioServer():
    # global varibale for the total stock value 
    total_stock_value, deposit,withdrawal, loan=0,0,0,0
    # global varibale for the deposit
  
    #global variable for  auszahlung

    

    def __init__(self):
        self.server_ip = os.environ.get("SERVER_IP", "127.0.0.1")
        self.server_port = int(os.environ.get("SERVER_PORT", "6789"))
        self.stocks = [
            {"symbol": "VW", "price": 170.0},
            {"symbol": "KIA", "price": 3000.0},
            {"symbol": "AUDI", "price": 400.0},
            {"symbol": "BMW", "price": 5000.0},
        ] 
       # total_stock_value =  sum(stock['price'] for stock in self.stocks) 
        #update the total stock value 
        self.update_total_stock_value()
        print(f"Total sum of stock prices is: {self.total_stock_value}")
        self.udp_server = udp_socket(self.server_ip, self.server_port)
       # self.http_server = http_server(self.handle_get)
       # runing the http Server as a Thread in the background since we the udp process 
       # never finishes and does not allow the next http process to start 
       
        self.http_thread = threading.Thread(target=self.create_http_server)
        self.http_thread.daemon = True # run in the background
        self.http_thread.start()

        
    

    def create_http_server(self):
        self.server_ip = os.environ.get("SERVER_IP", "127.0.0.1")
        self.server_port = int(os.environ.get("SERVER_PORT", "6789"))
        self.http_server = http_server(self.server_ip,self.server_port,self.handle_get,self.post_handler)

    def run(self):
        

        while True:
            data, client_address = self.udp_server.receive(self.server_ip, self.server_port, "I am the server accepting connections...", 4096)
            print("Received message from Bank:", data)
            data = json.loads(data)
            print("Message received from Bank  %s: " % (client_address,))

            try:
                # Update the securities prices based on the received data
                for received_stocks in data:
                    for stock in self.stocks:
                        if stock["symbol"] == received_stocks["symbol"]:
                            stock["price"] = received_stocks["price"]
                            print(f"Updated price of {stock['symbol']}: {stock['price']}")
        
                # calculate the portfolio value and print it out 

                portfolio_value= self.calculate_portfolio_value()
                self.__class__.total_stock_value=portfolio_value
                
                print("Total portfolio stock:", portfolio_value)

                response = {"status": "ok", "message": "Received data successfully"}
            except Exception as e:
                response = {"status": "error", "message": str(e)}

            response_json = json.dumps(response)
            print("Sending response:", response_json)
      
      
            self.udp_server.send(client_address[0], client_address[1], response_json, 4096)
        



    def run_thrift_server(self):
        self.server_ip1 = os.environ.get("SERVER_IP1", "127.0.0.1")
        self.server_port2 = int(os.environ.get("SERVER_PORT2", "7001"))
        handler = StockPortfolioHandler()
        thrift_server =  make_aio_server(
                         stockportfolio_thrift.StockPortfolioService, handler, self.server_ip1, self.server_port2)
        print(f"Started the Thrift Server on: {self.server_ip1}:{self.server_port2} ")
        #thrift_server.serve()
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(thrift_server.serve())


    def handle_get(self, request):
       # start_time=time.monotonic()
       # portfolio_value = self.calculate_portfolio_value()
        hhtp_body= f'Total portfolio value: {self.__class__.total_stock_value}'  
     #   end_time=time.monotonic()
       # elapsed_time= end_time- start_time
      #  print(f"GET request took {elapsed_time:.3f} seconds.")
        return hhtp_body
    

    def post_handler(self,data_array):
       # start_time=time.monotonic()
        for data in data_array:
            if data.startswith('portfolio_value='):
                self.__class__.total_stock_value= int(data.split('=')[1])
             
              #  print (f"total stock value is: {self.total_stock_value}")

            elif data.startswith('deposit='):
                 self.__class__.deposit= int(data.split('=')[1])
                 self.__class__.total_stock_value+= self.__class__.deposit
            
            elif data.startswith('withdrawal='):
                 self.__class__.withdrawal= int(data.split('=')[1])
                 self.__class__.total_stock_value-=self.__class__.withdrawal

       # end_time= time.monotonic()       
       # elapsed_time= end_time -start_time
       # print(f"POST request took {elapsed_time:.3f} seconds.")
        return f'portfolio_value={self.__class__.total_stock_value}, deposit={self.__class__.deposit}, withdrawal={self.__class__.withdrawal}'

    def update_total_stock_value(self):
        self.__class__.total_stock_value= sum(stock['price'] for stock in self.stocks)

    # function for calculating the sum of the portfolio
    def calculate_portfolio_value(self):
        portfolio_value=0
        for stock in self.stocks:
            portfolio_value+= stock ["price"]

        return portfolio_value
    


class StockPortfolioHandler:
    async  def ApproveLoan(self):
                if StockPortfolioServer.loan > 0:
                    loan_amount = StockPortfolioServer.loan
                    StockPortfolioServer.total_stock_value -= loan_amount
                    StockPortfolioServer.loan = 0
                    print("Loan approved.")
                    print (f"substracted total value through rpc : {StockPortfolioServer.total_stock_value}")
                    return loan_amount
                
                else:
                    print("No loan to approve")
                    return(-1)
                


    async def RequestLoan(self, amount):
                if StockPortfolioServer.total_stock_value >= amount:
                    StockPortfolioServer.loan=amount
                    print(f"Loan requested robi: {StockPortfolioServer.loan}")
                    return StockPortfolioServer.loan
                else:
                    print("Bankruptcy! Cannot request loan.")
                    return 0
                    

    
def main():
     try:  
        server=StockPortfolioServer()
        thrift_thread = threading.Thread(target=server.run_thrift_server)
        thrift_thread.daemon = True
        thrift_thread.start()
           
        
        server.run()

     except Exception as e:
            print(f"failed to run server: {e}" )

if __name__=='__main__':
   main()
