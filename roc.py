    
class StockPortfolioServer():
    # global varibale for the total stock value 
    total_stock_value, deposit,withdrawal, loan=0,0,0,0
    client_thread_started = False
    Bank_Limit= 6000
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
    async def start(self):
        #server_ip_kafka_string = os.getenv("KAFKA_IP", "0.0.0.0")
        server_ip_kafka_string = os.getenv("KAFKA_IP", "kafka")
        server_ip_kafka_string = server_ip_kafka_string.strip() if server_ip_kafka_string else ""
        server_kafka_bank = socket.gethostbyname(server_ip_kafka_string)
        print (f"ip of kafka is: {server_kafka_bank}")
        # chnaged tehe topics because of the bug try to fix it !
        bank_topic = 'prepare_topic'
        coordinator_topic = 'total_value_topic'
        vote_topic= 'vote_topic'
        bootstrap_servers = f"{server_kafka_bank}:9092"
        #consumer_group_id = 'bank_group'
        consumer_group_id= os.getenv("GROUPID","bank_germany")
        loop = asyncio.get_event_loop()
        monitor = aiomonitor.Monitor(loop=loop)




        self.producer = BankProducer(bootstrap_servers, bank_topic,coordinator_topic,vote_topic)
        self.consumer = BankConsumer(bootstrap_servers,coordinator_topic, bank_topic, consumer_group_id, vote_topic)
        self.coordinator_topic= coordinator_topic
        self.topic = bank_topic
        # So it is crashing on this line(108) when
        status =await self.producer.start()
        print(f" status is : {status }")
        time.sleep(60)
        await self.consumer.start()
        publish_task = asyncio.create_task(self.publish_bank_values())
        consume_task = asyncio.create_task(self.handle_decision_messages())

        #await asyncio.gather(publish_task, consume_task)
        await publish_task
        await consume_task

class BankConsumer:
    def __init__(self, bootstrap_servers, coordinator_topic, bank_topic, consumer_group_id,vote_topic):
        self.bootstrap_servers = bootstrap_servers
        self.coordinator_topic = coordinator_topic
        self.bank_topic = bank_topic
        self.consumer_group_id = consumer_group_id
        self.vote_topic= vote_topic
        self.producer= BankProducer(bootstrap_servers,coordinator_topic,bank_topic,vote_topic)

        
    async def start(self):
        try:
            #loop = asyncio.get_event_loop()
            self.consumer = AIOKafkaConsumer(
                bootstrap_servers=self.bootstrap_servers,
                group_id=self.consumer_group_id,
                enable_auto_commit=False,
                #loop=loop
            )
            
         #   await asyncio.sleep(120)
            await self.consumer.start()
            await self.consumer.subscribe([ self.bank_topic, self.coordinator_topic])
        except Exception as e:
            print(f"Error during consumer start: {e}")

    async def stop(self):
        await self.consumer.stop()  
        
        
         async def consume_bank_values(self):
        print("got in to onue bak value function")
        tst= StockPortfolioServer()
        print("after the tst class instatiated")
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
                print(f"Received values: bank name {bank_name} and total stock value {total_stock_value}")
                
                try:
                        if  tst.total_stock_value >=7000 :               # __class__.total_stock_value >= 6570:     # 6500 <= total_stock_value <= 6800          
                            print("Before commit vote")
                            sleep_for_commit= asyncio.create_task(self.producer.publish_vote('commit', bank_name))
                            await sleep_for_commit
                            breakpoint()
                            #await self.producer.publish_vote('commit', bank_name)
                            #self.producer.publish_vote('commit', bank_name)
                            print(f"Published commit vote for bank {bank_name}")
                            return "done"
                            #break
                except Exception as e:
                        #print("exeption vote")
                         logging.exception(f"Exception  vote occurred: {e}")
                
                else:
                    print("Before abort vote")
                    sleep_for_abort= asyncio.create_task(self.producer.publish_vote('abort', bank_name))
                    await sleep_for_abort
                    #await self.producer.publish_vote('abort', bank_name)
                     #self.producer.publish_vote('abort', bank_name)
                    print(f"Published abort vote for bank {bank_name}")
                   # break
                        
                        
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
               # print(f"Received values on coordinator topic : bank name {bank_name} and total stock value {total_stock_value}")
                
                pass

class BankProducer:
    def __init__(self, bootstrap_servers, coordinatortopic,bank_topic,vote_topic):
        #loop = asyncio.get_event_loop()
        self.producer = AIOKafkaProducer(bootstrap_servers=bootstrap_servers)
        self.bank_topic = bank_topic
        self.coordinator_topic= coordinatortopic
        self.vote_topic= vote_topic


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
        await self.producer.send_and_wait(self.bank_topic, json.dumps(message).encode('utf-8'))

    
    async def publish_bank_info_to_coordinator(self, bank_name, total_stock_value):
        message = {
            'bank_name': bank_name,
            'total_stock_value': total_stock_value
        }
        print(f"Publishing bankrupt bank  info to prepare topic : {message}")
        await self.producer.send_and_wait(self.coordinator_topic, json.dumps(message).encode('utf-8'))
    
    
    #async def publish_vote(self, decision_type, bankrupt_bank_name):
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
        await self.producer.send_and_wait(self.vote_topic, json.dumps(message).encode('utf-8'))
        print("after wait vote ")
    
    async def publish_decision(self, decision_type, bankrupt_bank_name):
        message = {
            'type': decision_type,
            'bankrupt_bank_name': bankrupt_bank_name
        }
        print(f"Producing decision message: {message}")
        await self.producer.send_and_wait(self.coordinator_topic, json.dumps(message).encode('utf-8'))



