# Distributed Banking System Communication

This project demonstrates a distributed banking system that communicates using Docker containers and utilizes Apache Kafka for message passing. The system consists of multiple services, including banks, a stock market, Zookeeper, and Kafka.
This Project uses four communication types and these are UDP, TCP(also a running http server on top of TCP), RPC, MOM(message oriented middleware).

### UDP
![udp](https://github.com/smartlocus/Distributed-Banksystem-Communication/assets/114703928/f6436999-0f1c-4c5c-9c9e-c2846f1f9f41)

### TCP with an HTTP SERVER above it
![Screenshot from 2023-05-13 21-21-09](https://github.com/smartlocus/Distributed-Banksystem-Communication/assets/114703928/99952da4-c003-4cd2-93e7-13121dd119b7)
![Screenshot from 2023-05-13 20-36-27](https://github.com/smartlocus/Distributed-Banksystem-Communication/assets/114703928/ddea11b0-6a9d-4ee9-b75a-3db10b2873dc)

### Remote Procedure Call(RPC)
![Screenshot from 2023-07-11 01-29-16](https://github.com/smartlocus/Distributed-Banksystem-Communication/assets/114703928/d3ea10c1-95c4-42d3-8e24-89e12147b25c)

### Messsage Oriented Middleware(MOM) 
In implementing the publish subscribe communication , Kafka is used as a solution.Also note
that the two phase commit algorithm was used within the publish subscribe communication in order to ensure Atomicity, Data Consistency, Isolation and Durablility.

![Screenshot from 2023-07-10 23-44-50](https://github.com/smartlocus/Distributed-Banksystem-Communication/assets/114703928/7db2e7b7-1262-4639-aaec-a5dcef703016)
![Screenshot from 2023-07-10 23-48-00](https://github.com/smartlocus/Distributed-Banksystem-Communication/assets/114703928/cb3eb1c3-3953-446e-861f-d30b50b20e05)

![Screenshot from 2023-07-10 23-49-06](https://github.com/smartlocus/Distributed-Banksystem-Communication/assets/114703928/5030fa86-f947-4b9f-af26-8afed8df3cd7)




## Requirements

- Docker: Make sure you have Docker installed on your system. You can download it from [Docker's official website](https://www.docker.com/).

## How to Run

1. Clone the repository to your local machine:

git clone https://github.com/smartlocus/Distributed-Banksystem-Communication.git


2. Navigate to the project directory:

   
 cd Distributed-Banksystem-Communication

 
3. Build the Docker images for the services:

   ## docker-compose build

4. Run the services:

   ## docker-compose up




This command will start the banks, stock market, Zookeeper, and Kafka containers. The system will now be up and running, and you can access it through the specified ports.

## Services and Ports

The project consists of the following services:

- **bank**: Represents a bank service. It listens on port 6789.
- **bank2**: Another instance of the bank service. It listens on port 6789 as well.
- **stockmarket**: Represents a stock market service. It depends on the banks and listens on ports 6790 to 7000.
- **zookeeper**: Zookeeper is used for managing the Kafka cluster and coordination among brokers. It listens on port 2181.
- **kafka**: Apache Kafka is a message broker used for communication between services. It listens on port 9092.

## Environment Variables

The following environment variables are available to configure the services:

- **SERVER_IP**: The IP address of the bank service. Default: bank
- **SERVER_PORT**: The port number the bank service listens on. Default: 6789
- **SERVER_IP_THRIFT**: (Commented out) The IP address of the bank service for Thrift communication.
- **SERVER_PORT_THRIFT**: (Commented out) The port number the bank service listens on for Thrift communication.
- **SERVER_IP_BANK**: The IP address of bank2 for inter-bank communication. Default: bank2
- **SERVER_PORT_BANK**: The port number bank2 listens on for inter-bank communication. Default: 7001
- **LOAN_AMOUNT**: The amount of money to lend from another bank. Default: 1000
- **KAFKA_IP**: The IP address of the Kafka service. Default: kafka

## Network

The services are connected to a custom Docker bridge network named "test_net_1". This network allows the containers to communicate with each other.

## Note

- Make sure that the required ports (e.g., 6789, 7001, 2181, 9092) are not already in use on your system.



Feel free to modify and extend this project as needed. Happy coding!

   


