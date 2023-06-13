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

from thriftpy2.rpc import make_aio_client


try:
     stockportfolio_thrift= thriftpy2.load("/home/robi/uni/RobiVS/stockportfolio.thrift", module_name="stockportfolio_thrift")

except Exception as e:
         print(f"Failed to load Thrift file: {e}")
         exit(1)

class BankClient:
    def __init__(self):
        self.client = None

    async def connect(self):
        try:
            self.client = await make_aio_client(stockportfolio_thrift.StockPortfolioService, '127.0.0.1', 7001)
            print("Connected to the Thrift server")
        except Exception as e:
            print(f"Failed to connect to the Thrift server: {e}")

    async def request_loan(self, amount):
        try:
            if self.client is None:
                print("Thrift client is not connected")
                return

            response = await self.client.RequestLoan(amount)
            print(f"Loan requested: {amount}")
            print("Response from the Thrift server:", response)
        except Exception as e:
            print(f"Failed to request a loan: {e}")

    async def approve_loan(self):
        try:
            if self.client is None:
                print("Thrift client is not connected")
                return

            response = await self.client.ApproveLoan()
            print("Response from the Thrift server:", response)
        except Exception as e:
            print(f"Failed to approve a loan: {e}")

async def main():
    client = BankClient()
    await client.connect()

    # Example usage: Request a loan of 5000
    await client.request_loan(1000)

    # Example usage: Approve a loan
    await client.approve_loan()

asyncio.run(main())


