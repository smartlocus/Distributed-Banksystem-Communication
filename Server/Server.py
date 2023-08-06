import json
import os
import threading
import time
#import aiomonitor
import sys
from concurrent import futures
from networking.udpSocket import udp_socket
from networking.tcpSocket import http_server
import asyncio
import thriftpy2
import socket
from aiokafka import AIOKafkaConsumer
from aiokafka import AIOKafkaProducer
from thriftpy2.rpc import make_aio_server
from thriftpy2.rpc import make_aio_client

import logging

try:
    stockportfolio_thrift = thriftpy2.load("/Server/Server/stockportfolio.thrift", module_name="stockportfolio_thrift")

except Exception as e:
    print(f"Failed to load Thrift file: {e}")
    exit(1)


class StockPortfolioServer():
    # global varibale for the total stock value
    total_stock_value, deposit, withdrawal, loan = 0, 0, 0, 0
    client_thread_started = False
    Bank_Limit = 6000

    # global varibale for the deposit

    # global variable for  auszahlung

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
        # update the total stock value
        self.update_total_stock_value()
        print(f"Total sum of stock prices is: {self.total_stock_value}")
        self.udp_server = udp_socket(self.server_ip, self.server_port)
        # self.http_server = http_server(self.handle_get)
        # runing the http Server as a Thread in the background since we the udp process
        # never finishes and does not allow the next http process to start

        # thread for starting the http Server
        self.http_thread = threading.Thread(target=self.create_http_server)
        self.http_thread.daemon = True  # run in the background
        self.http_thread.start()

    def create_http_server(self):
        self.server_ip = os.environ.get("SERVER_IP", "127.0.0.1")
        self.server_port = int(os.environ.get("SERVER_PORT", "6789"))
        self.http_server = http_server(self.server_ip, self.server_port, self.handle_get, self.post_handler)

    async def vote_consume(self):
     # await self.producer.start()

        # print(f"testis : {tst}")
        await self.consumer.start()
        consume_task = asyncio.create_task(self.vote_consume())
        await consume_task

    async def handle_decision_messages(self):
        await self.consumer.consume_bank_values()

    async def publish_bank_values(self):
        while True:
            await asyncio.sleep(40)
            bank_name = os.getenv("BANKNAME")
            await self.producer.publish_bank_value(bank_name, StockPortfolioServer.total_stock_value)

            # if self.total_stock_value <= 7000:
            #self.total_stock_value -= 3000
            #print(f"substatced on line 82 : {self.total_stock_value}")

            if self.total_stock_value <= 7000:
                print(f"Starting 2PC process...")
                # issues i have the next line publishes in to total value topic instead of coordinator topic
                await self.producer.publish_bank_info_to_coordinator(bank_name, self.total_stock_value)
            else:
                print("Total stock value is not less than 7000. Not publishing to coordinator topic")

    async def start(self):
        # server_ip_kafka_string = os.getenv("KAFKA_IP", "0.0.0.0")
        server_ip_kafka_string = os.getenv("KAFKA_IP", "kafka")
        server_ip_kafka_string = server_ip_kafka_string.strip() if server_ip_kafka_string else ""
        server_kafka_bank = socket.gethostbyname(server_ip_kafka_string)
        print(f"ip of kafka is: {server_kafka_bank}")
        # chnaged tehe topics because of the bug try to fix it !
        bank_topic = 'prepare_topic'
        coordinator_topic = 'total_value_topic'
        vote_topic = 'vote_topic'
        bootstrap_servers = f"{server_kafka_bank}:9092"
        # consumer_group_id = 'bank_group'
        consumer_group_id = os.getenv("GROUPID", "bank_germany")
        loop = asyncio.get_event_loop()
        print(f"current loop is {loop}")
        #monitor = aiomonitor.Monitor(loop=loop)

        self.producer = BankProducer(bootstrap_servers, bank_topic, coordinator_topic, vote_topic)
        self.consumer = BankConsumer(bootstrap_servers, coordinator_topic, bank_topic, consumer_group_id, vote_topic)
        self.coordinator_topic = coordinator_topic
        self.topic = bank_topic
        # So it is crashing on this line(108) when
        #status = await self.producer.start()
        #print(f" status is : {status}")
        #time.sleep(60)
        #await self.consumer.start()
        await self.producer.start()

        #print(f"testis : {tst}")
        await self.consumer.start()
       #await tst1
       # print(f"testis : {tst1}")

        publish_task = asyncio.create_task(self.publish_bank_values())
        consume_task = asyncio.create_task(self.handle_decision_messages())

        # await asyncio.gather(publish_task, consume_task)
        await publish_task
        await consume_task

    def run(self):

        def check_stock_value():
            while True:
                time.sleep(5)
                if self.total_stock_value <= self.Bank_Limit and not self.client_thread_started:
                    client_thread = threading.Thread(target=self.run_client_thread)
                    client_thread.daemon = True
                    client_thread.start()
                    self.client_thread_started = True

                # here is checked if the total value is less than than the bank limit
                # and sets the bool to false so that the clien thread gets triggered
                # everytime the total stock value is less than the bank limit
                # made changes here from > to <
                elif self.total_stock_value < self.Bank_Limit and self.client_thread_started:
                    self.client_thread_started = False

                time.sleep(3)

        # self.client_thread_started= False

        # This thread is runnign
        check_thread = threading.Thread(target=check_stock_value)
        check_thread.daemon = True
        check_thread.start()

        while True:
            data, client_address = self.udp_server.receive(self.server_ip, self.server_port,
                                                           "I am the server accepting connections...", 4096)
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

                portfolio_value = self.calculate_portfolio_value()
                self.__class__.total_stock_value = portfolio_value

                print("Total portfolio stock:", portfolio_value)

                response = {"status": "ok", "message": "Received data successfully"}
            except Exception as e:
                response = {"status": "error", "message": str(e)}

            response_json = json.dumps(response)
            print("Sending response:", response_json)

            self.udp_server.send(client_address[0], client_address[1], response_json, 4096)

        # thread for starting the client thrift
        # if total_stock_value <= server.Bank_Limit and not server.client_thread_started:

    #     client_thread= threading.Thread(target=server.run_client_thread)
    #     client_thread.daemon= True
    #      client_thread.start()

    def run_thrift_server(self):
        self.server_ip1 = os.environ.get("SERVER_IP_THRIFT", "0.0.0.0")
        self.server_port2 = int(os.environ.get("SERVER_PORT_THRIFT", "7001"))
        handler = StockPortfolioHandler()
        thrift_server = make_aio_server(
            stockportfolio_thrift.StockPortfolioService, handler, self.server_ip1, self.server_port2)
        print(f"Started the Thrift Server on: {self.server_ip1}:{self.server_port2} ")
        # thrift_server.serve()
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(thrift_server.serve())

    async def run_thrift_client(self):
        client = BankClient()
        await client.connect()
        loan_amount = int(os.getenv("LOAN_AMOUNT", "1000"))
        await client.request_loan(loan_amount)  # chnaged here
        # print("This is robis line")
        await client.approve_loan()

    def run_client_thread(self):
        # this line modified to start the clinet thrift asynchron
        # asyncio.run(self.run_thrift_client())
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(self.run_thrift_client())

    # asyncio.run(asyncio.to_thread(self.run_thrift_client()))

    def handle_get(self, request):
        # start_time=time.monotonic()
        # portfolio_value = self.calculate_portfolio_value()
        hhtp_body = f'Total portfolio value: {self.__class__.total_stock_value}'
        #   end_time=time.monotonic()
        # elapsed_time= end_time- start_time
        #  print(f"GET request took {elapsed_time:.3f} seconds.")
        return hhtp_body

    def post_handler(self, data_array):
        # start_time=time.monotonic()
        for data in data_array:
            if data.startswith('portfolio_value='):
                self.__class__.total_stock_value = int(data.split('=')[1])

            #  print (f"total stock value is: {self.total_stock_value}")

            elif data.startswith('deposit='):
                self.__class__.deposit = int(data.split('=')[1])
                self.__class__.total_stock_value += self.__class__.deposit

            elif data.startswith('withdrawal='):
                self.__class__.withdrawal = int(data.split('=')[1])
                self.__class__.total_stock_value -= self.__class__.withdrawal

        # end_time= time.monotonic()
        # elapsed_time= end_time -start_time
        # print(f"POST request took {elapsed_time:.3f} seconds.")
        return f'portfolio_value={self.__class__.total_stock_value}, deposit={self.__class__.deposit}, withdrawal={self.__class__.withdrawal}'

    def update_total_stock_value(self):
        self.__class__.total_stock_value = sum(stock['price'] for stock in self.stocks)

    # function for calculating the sum of the portfolio
    def calculate_portfolio_value(self):
        portfolio_value = 0
        for stock in self.stocks:
            portfolio_value += stock["price"]

        return portfolio_value


# This class is used by the thrift server  for the rpc procedure
class StockPortfolioHandler:
    async def ApproveLoan(self):
        if StockPortfolioServer.loan > 0:
            loan_amount = StockPortfolioServer.loan
            StockPortfolioServer.total_stock_value -= loan_amount
            StockPortfolioServer.loan = 0
            print("Loan approved.")
            print(f"substracted total value through rpc : {StockPortfolioServer.total_stock_value}")
            print(f"My total stock value now is : {StockPortfolioServer.total_stock_value}")
            return loan_amount

        else:
            print("No loan to approve")
            return (-1)

    async def RequestLoan(self, amount):
        if StockPortfolioServer.total_stock_value >= amount:
            StockPortfolioServer.loan = amount
            print(f"Incoming Loan request from Bank: {StockPortfolioServer.loan}")
            print(f"My total stock value now is : {StockPortfolioServer.total_stock_value}")
            return StockPortfolioServer.loan
        else:
            print("Bankruptcy! Cannot request loan.")
            return 0


# This class will be  used for instanciating the Bank Client Thrift in case a bank goes bankrupt

class BankClient:
    def __init__(self):
        self.client = None

    async def connect(self):
        try:

            server_ip_bank_string = os.getenv("SERVER_IP_BANK")
            # server_ip_bank_string= server_ip_bank_string.strip()
            print(f"Value of SERVER_IP_BANK: {server_ip_bank_string}")
            server_ip_bank_string = server_ip_bank_string.strip() if server_ip_bank_string else ""
            print(f"Value of server_ip_bank_string: {server_ip_bank_string}")

            # print("type is : " ,type(server_ip_bank_string))
            print(f"ip bank is : {server_ip_bank_string}")
            #  server_ip_bank_string = "'" + f"{server_ip_bank_string}" + "'"
            #  server_ip_bank_string = server_ip_bank_string.strip()

            # print(f"name is : {server_ip_bank_string}")
            server_ip_bank = socket.gethostbyname(server_ip_bank_string)

            # time.sleep(4)
            print(f"ip bank 2 is : {server_ip_bank}")
            type(server_ip_bank_string)
            server_port_bank = int(os.environ.get("SERVER_PORT_BANK", "7001"))

            self.client = await make_aio_client(stockportfolio_thrift.StockPortfolioService, server_ip_bank,
                                                server_port_bank)
            print(f"Connected to Bank: {server_ip_bank}, {server_port_bank}")
            
            
        except Exception as e:
            print(f"Failed to connect to the Thrift server: {e}")
            print(f" failed Connected to Bank: {server_ip_bank}, {server_port_bank}")

    async def request_loan(self, amount):
        try:
            if self.client is None:
                print("Thrift client is not connected")
                return
            start_time = time.time()
            response = await self.client.RequestLoan(amount)
            
            end_time = time.time()
            elapsed_time = end_time - start_time
            
            print(f"Loan requested: {amount}")
            print("Response from the Thrift server:", response)
            print(f"Elapsed time for loan request: {elapsed_time} seconds")
        except Exception as e:
            print(f"Failed to request a loan: {e}")

    async def approve_loan(self):
        try:
            if self.client is None:
                print("Thrift client is not connected")
                return

            start_time = time.time()
            response = await self.client.ApproveLoan()
            
            end_time = time.time()
            elapsed_time = end_time - start_time
            
            print("Response from the Thrift server:", response)
            print(f"Elapsed time on approve loan : {elapsed_time} seconds")

            # updating the total stock value of the Bank after  recieving it from the thrift server
            #  if response >0:
            # The reason why the total value stock became 7570 again is because first you had 8750 -1000 = 750 and here you are adding 1000 to it that is why it is 8750 again
            StockPortfolioServer.total_stock_value += response
            print(
                f"updated total stock value after receiving it from the Thrift server: {StockPortfolioServer.total_stock_value}")
        except Exception as e:
            print(f"Failed to approve a loan: {e}")


class BankConsumer:
    def __init__(self, bootstrap_servers, coordinator_topic, bank_topic, consumer_group_id, vote_topic):
        self.bootstrap_servers = bootstrap_servers
        self.coordinator_topic = coordinator_topic
        self.bank_topic = bank_topic
        self.consumer_group_id = consumer_group_id
        self.vote_topic = vote_topic
        self.producer = BankProducer(bootstrap_servers, coordinator_topic, bank_topic, vote_topic)

    async def start(self):
        try:
            # loop = asyncio.get_event_loop()
            self.consumer = AIOKafkaConsumer(
                bootstrap_servers=self.bootstrap_servers,
                group_id=self.consumer_group_id,
                enable_auto_commit=False,
                # loop=loop
            )

            #   await asyncio.sleep(120)
            await self.consumer.start()
            await self.consumer.subscribe([self.bank_topic, self.coordinator_topic,self.vote_topic])
        except Exception as e:
            print(f"Error during consumer start: {e}")

    async def stop(self):
        await self.consumer.stop()









    async def consume_bank_values(self):
        print("got in to onue bak value function")
        tst = StockPortfolioServer()
        print("after the tst class instatiated")
        vote_decisions = []
        async for message in self.consumer:
            topic = message.topic
            message_data = json.loads(message.value.decode('utf-8'))
            if topic == self.bank_topic:
                
                # Handle bank values
                bank_name = message_data['bank_name']
                total_stock_value = message_data['total_stock_value']
                print(
                    "Consumed: Topic={}, Partition={}, Offset={}, Key={}, Value={}, Timestamp={}".format(
                        message.topic,
                        message.partition,
                        message.offset,
                        message.key,
                        message.value,
                        message.timestamp,
                    )
                    
                )
                producertimestamp=message.timestamp
                consumer_timestamp= time.time()
                time_taken= consumer_timestamp-(producertimestamp/1000)
                print("Time taken  from publish to consume on coordinator topic is: ", time_taken*1000,"milliseconds")
                print(f"Received values: bank name {bank_name} and total stock value {total_stock_value}")
                #await self.producer.stop()

                try:
                    
                    if StockPortfolioServer.total_stock_value >= 7000:  # __class__.total_stock_value >= 6570:     # 6500 <= total_stock_value <= 6800
                        print(f"line value after the if condition is: {total_stock_value}")
                        print("Before commit vote")
                        loop = asyncio.get_event_loop()
                        print(f"current event loop is: {loop}")
                       # sleep_for_commit = asyncio.create_task(self.producer.publish_vote('commit', bank_name))
                        #await sleep_for_commit
                        await self.commit_vote(bank_name)
                        print(f"Published commit vote for bank {bank_name}")

                        #breakpoint()
                        # await self.producer.publish_vote('commit', bank_name)
                        # self.producer.publish_vote('commit', bank_name)
                        print(f"Published commit vote for bank {bank_name}")
                        print("This is the recursive line  after they vote ")
                        #await self.consume_vote()
                        print("This is the line of the consume vote in the if statemenet after the vote ")
                        #return "done"
                        # break


                    else:
                        print(f"total stock value on the else statemnet is: {StockPortfolioServer.total_stock_value}")
                        print("Before abort vote")
                        await self.abort_vote(bank_name)
                        print(f"Published abort vote for bank {bank_name}")
                        #sleep_for_abort = asyncio.create_task(self.producer.publish_vote('abort', bank_name))
                        #await sleep_for_abort
                        # await self.producer.publish_vote('abort', bank_name)
                        # self.producer.publish_vote('abort', bank_name)

                        print(f"Published abort vote for bank {bank_name}")
                        #await self.consume_vote()
                        print("This is the line of the consume vote in the else statement ")
                # break

                except Exception as e:
                    # print("exeption vote")
                    logging.exception(f"Exception  vote occurred: {e}")
                    
                    
            elif topic == self.coordinator_topic:
                

                bank_name = message_data['bank_name']
                total_stock_value = message_data['total_stock_value']
                print(
                    "Consumed: Topic={}, Partition={}, Offset={}, Key={}, Value={}, Timestamp={}".format(
                        message.topic,
                        message.partition,
                        message.offset,
                        message.key,
                        message.value,
                        message.timestamp,
                    )
                )
                
                producertimestamp=message.timestamp
                consumer_timestamp= time.time()
                time_taken= consumer_timestamp-(producertimestamp/1000)
                print("Time takne from publish to consume on total stock Value Topic  is: ", time_taken*1000,"milliseconds")
                
                
                
                
                print(f"Received values on total value  topic : bank name {bank_name} and total stock value {total_stock_value}")

            elif topic == self.vote_topic:
                # Handle vote values
                #vote_decisions = []
                
                vote_type = message_data['type'].split(',')
                bank_name = message_data['bankrupt_bank_name']
                
                
                print(
                        "Consumed: Topic={}, Partition={}, Offset={}, Key={}, Value={}, Timestamp={}".format(
                            message.topic,
                            message.partition,
                            message.offset,
                            message.key,
                            message.value,
                            message.timestamp,
                        )
                    )
                
                producertimestamp=message.timestamp
                consumer_timestamp= time.time()
                time_taken= consumer_timestamp-(producertimestamp/1000)
                print("Time takne from publish to consume on vote topic is: ", time_taken*1000,"milliseconds")
                
                
                vote_decisions.append(vote_type)
                print(f"Received values: vote type {vote_type} and bank name {bank_name}")
                print("hey there")
               
                print(f"Vote decisions: {vote_decisions}")
                print("Vote decisions length:",len(vote_decisions))
                print(f"This lin eis after the appand to the array list")
            
            if len(vote_decisions) >=2:
                        first_two_decisions = vote_decisions[:2] # first two decisions
                        if all(decision == "commit" for decision in first_two_decisions):
                        # Save the bankrupt bank name
                         print(f"{bank_name} can be saved!")
                         #break
                        else:
                            print(f" Money Transaction will not be executed.One Bank does not have enough Money.")
                           # break
                            
            #print("I have finished reading all the votes of the Banks ")
                


            pass
   # def run_vote_thread(self,bankname):
       #  bank_name=bankname

        # sleep_for_commit=  asyncio.create_task(self.producer.publish_vote('commit', bank_name))
        # await sleep_for_commit

   # def run_abort_thread(self,bankname):
       # bank_name = bankname

       # sleep_for_commit = asyncio.create_task(self.producer.publish_vote('abort', bank_name))
       # await sleep_for_commit

    async def commit_vote(self, bank_name):
        # Perform publishing of the commit vote
        # ...
        print("went in to commit vote function ")
        await self.producer.publish_vote('commit', bank_name)

    async def abort_vote(self, bank_name):
        # Perform publishing of the abort vote
        # ...
        print("went in to abort vote function ")
        await self.producer.start()
        await self.producer.publish_vote('abort', bank_name)


    async def  consume_vote(self):
        tst = StockPortfolioServer()
        print("Starting consuming from the vote topic")

        #await self.consumer.start()
        #await self.consumer.stop()
        #await self.consumer.start()
        name="bank1"
        containername= os.environ.get("bank1")
        if name==containername:
            vote_decisions = []
            async for message in self.consumer:
                topic = message.topic
                message_data = json.loads(message.value.decode('utf-8'))
                if topic == self.vote_topic:
                    # Handle vote values
                    vote_type = message_data['type']
                    bank_name = message_data['bankrupt_bank_name']
                    print(
                        "Consumed: Topic={}, Partition={}, Offset={}, Key={}, Value={}, Timestamp={}".format(
                            message.topic,
                            message.partition,
                            message.offset,
                            message.key,
                            message.value,
                            message.timestamp,
                        )
                    )
                    print(f"Received values: vote type {vote_type} and bank name {bank_name}")
                   
                    vote_decisions.append(vote_type)
                    if len(vote_decisions) >=2:
                        first_two_decisions = vote_decisions[:2] # first two decisions
                        if all(decision == "commit" for decision in first_two_decisions):
                        # Save the bankrupt bank name
                         print(f"{bank_name} can be saved!")
                        else:
                            print(f" Money Transaction will not be executed.One Bank does not have enough Money.")
                            
                    print("I have finished reading all the votes of the Banks ")
                    #pass
                    break

        else:
            pass






class BankProducer:
    def __init__(self, bootstrap_servers, coordinatortopic, bank_topic, vote_topic):
        # loop = asyncio.get_event_loop()
        self.producer = AIOKafkaProducer(bootstrap_servers=bootstrap_servers)
        self.bank_topic = bank_topic
        self.coordinator_topic = coordinatortopic
        self.vote_topic = vote_topic
       # self.stock_portfolio_server= StockPortfolioServer()
        #consumer = BankConsumer(bootstrap_servers, coordinatortopic, bank_topic, None,vote_topic)


    async def start(self):
        await self.producer.start()

    async def stop(self):
        await self.producer.stop()

    async def publish_bank_value(self, bank_name, total_stock_value):
        message = {
            'bank_name': bank_name,
            'total_stock_value': total_stock_value
        }
        
        print(f"Producing message: {message}")
        timestamp_ms = int(time.time() * 1000)
        message['timestamp'] = timestamp_ms
        message_str = json.dumps(message).encode('utf-8')
        
        #tst= await self.producer.send_and_wait(self.bank_topic, json.dumps(message).encode('utf-8'))
        tst= await self.producer.send_and_wait(self.bank_topic, value=message_str,timestamp_ms=timestamp_ms)
        print(f"printing tst on publish ban k value function: {tst}")
        print(f"Published message with timestamp: {message}")

    async def publish_bank_info_to_coordinator(self, bank_name, total_stock_value):
        message = {
            'bank_name': bank_name,
            'total_stock_value': total_stock_value
        }
        
        #timestamp_ms = int(time.time() * 1000)
        #message['timestamp'] = timestamp_ms
        #message_str = json.dumps(message).encode('utf-8')
        
        print(f"Publishing bankrupt bank  info to prepare topic : {message}")
        tst=  await self.producer.send_and_wait(self.coordinator_topic, json.dumps(message).encode('utf-8'))
        #tst=  await self.producer.send_and_wait(self.coordinator_topic, value=message_str,timestamp_ms=timestamp_ms)
        print(f"printing tst: {tst}")


    # async def publish_vote(self, decision_type, bankrupt_bank_name):
    #   message = {
    #      'type': decision_type,
    #     'bankrupt_bank_name': bankrupt_bank_name
    #  }
    # print(f"Producing vote message: {message}")
    # await self.producer.send_and_wait(self.vote_topic, json.dumps(message).encode('utf-8'))

    async def publish_vote(self, decision_type, bankrupt_bank_name):
        message = {
            'type': decision_type,
            'bankrupt_bank_name': bankrupt_bank_name
        }
        print(f"Producing vote message: {message}")
        #try:
        await self.producer.start()
        tst = await self.producer.send_and_wait(self.vote_topic, json.dumps(message).encode('utf-8'))
        print(f"printing tst publish vote function: {tst}")
        #await self.producer.stop()
        #asyncio.create_task()
       # await self.stock_portfolio_server.vote_consume(self.consumer)
        print("line starting consume vote")



           # print(f"printing tst: {tst}")
        print("after wait vote ")
        print("after 1")
       # except Exception as teff:
           # print(f"exception publish vote: {teff}")

    async def publish_decision(self, decision_type, bankrupt_bank_name):
        message = {
            'type': decision_type,
            'bankrupt_bank_name': bankrupt_bank_name
        }
        print(f"Producing decision message: {message}")
        await self.producer.send_and_wait(self.coordinator_topic, json.dumps(message).encode('utf-8'))



async def delayed_start():
    await asyncio.sleep(60)
    server = StockPortfolioServer()
    await server.start()


def run_async_code():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(delayed_start())


def main():
    try:
        # thread for starting the Server thrift
        server = StockPortfolioServer()
        thrift_thread = threading.Thread(target=server.run_thrift_server)
        thrift_thread.daemon = True
        thrift_thread.start()

        time.sleep(10)

        # loop= asyncio.get_event_loop()
        # loop.run_until_complete(delayed_start())
        # asyncio.run(delayed_start())

        async_thread = threading.Thread(target=run_async_code)
        async_thread.daemon = True
        async_thread.start()
        # asyncio.run(delayed_start())
        # kafka_thread = threading.Thread(target=asyncio.run(delayed_start()))
        # kafka_thread= True
        # kafka_thread.start()

        # thread for starting the client thrift
        # if server.total_stock_value <= server.Bank_Limit and not server.client_thread_started:
        #    client_thread= threading.Thread(target=server.run_client_thread)
        #   client_thread.daemon= True
        #  client_thread.start()

        #  print("total stock value is :" ,server.total_stock_value)

        server.run()



    except Exception as e:
        print(f"failed to run server: {e}")
        logging.exception(f"Failed to run server: {e}")


if __name__ == '__main__':
    main()


