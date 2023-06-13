import socket
import time
# This class sends a data with a post request to thr SERVERIP und SERVERPORT

class http_client:
  def __init__(self, SERVER_HOST, SERVER_PORT):
    self.SERVER_PORT = SERVER_PORT
    self.SERVER_HOST = SERVER_HOST

  def send_data(self, data, _callback_get=None, _callback_post=None):
    # Socket erstellen
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    # Mit Server verbinden
    client_socket.connect((self.SERVER_HOST, self.SERVER_PORT))

    print('TCP socket connected to HTTP server')

    # Nachricht senden
    header = 'POST / HTTP/1.1\r\n' \
             'Content-Type: text\r\n\r\n'
    message = header + data
    client_socket.send(message.encode())

    # Antwort erhalten und ausgeben
    server_response = client_socket.recv(1024).decode()

    # Socket schließen
    client_socket.close()


class http_server:
  def __init__(self,SERVER_HOST ,SERVER_PORT ,_callback_get=None, _callback_post=None): # , _callback_post=None
    #SERVER_HOST = '0.0.0.0'
    #SERVER_PORT = 8080
    self.SERVER_HOST= SERVER_HOST
    self.SERVER_PORT= SERVER_PORT

    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind((SERVER_HOST, SERVER_PORT))
    server_socket.listen(2)

    print(f"HTTP server up and listening on {self.SERVER_HOST}:{self.SERVER_PORT}")
    #print(f"Serving on {SERVER_HOST}:{SERVER_PORT}")


    while True:
      # Auf Client warten
      client_connection, client_address = server_socket.accept()
      client_connection.setblocking(False)

      # Client Request empfangen
      request = None
      while request is None:
        try:
          request = client_connection.recv(1024).decode()
        except:
          pass

      # Unterscheiden ob GET Anfrage oder POST Anfrage
      method = request.split(' ', 1)[0]
      headers = get_headers_from_http_request(request)
      data = get_data_from_http_request(request)

      # Antworte mit Daten aus Datenbank bei GET
      if method == 'GET':
        start_time=time.time()
        header = 'HTTP/1.0 200 OK\r\n' \
                 'Server: Custom Python\r\n' \
                 'Content-Type: text\r\n' \
                 '\r\n'

        # Daten an Caller geben (Datenbank)
        response = _callback_get(data)
        
        elapsed_time= (time.time() -start_time)*1000
      
        print(f"GET request successful for response: {response}, took {elapsed_time:.2f} ms")
      # Schreibe Daten aus der Anfrage in die Datenbank bei POST
      elif method == 'POST':
        start_time=time.time()
        header = 'HTTP/1.0 201 Created\r\n' \
                 'Server: custom python\r\n' \
                 '\r\n'

        # Daten an Caller geben (Datenbank)
        response = _callback_post(data)
      
        elapsed_time= (time.time()-start_time) *1000

        print(f"POST request successful for response: {response}, took {elapsed_time:.2f} ms")
      # Antworte mit Fehlercode bei sonstigen Methoden
      else:
        header = 'HTTP/1.0 400 Bad Request\r\n' \
                 'Server: custom python\r\n' \
                 '\r\n'
        response = ''

      # HTTP Response an client senden
      message = header + response

      client_connection.sendall(message.encode())

      # Client Verbindung abbauen
      client_connection.close()


def get_data_from_http_request(request: str):
  # Gesamte Anfrage zerstückeln
  request_array = request.split('\r\n')

  # Position von Daten finden anhand von Leerzeile
  counter = 0
  for request_line in request_array:
    if len(
        request_line) == 0: break  # Identifiziert Leerzeile (Ende des Headers / Start des bodies)
    counter = counter + 1

  # Gebe Data nach Leerzeile zurück oder gebe nichts zurück wenn es kein Body gibt
  return request_array[counter + 1:] if counter != len(request_array) else []


def get_headers_from_http_request(request: str):
  # Gesamte Anfrage zerstückeln
  request_array = request.split('\r\n')

  # Erste Zeile löschen, weil kein Header
  request_array.pop(0)

  # Request Array durchiterieren und Header extrahieren
  header_dictionary = dict()

  for request_line in request_array:
    if len(
        request_line) == 0: break  # Identifiziert Leerzeile (Ende des Headers)

    key, value = request_line.split(':', 1)
    header_dictionary[key] = value.strip()

  return header_dictionary
