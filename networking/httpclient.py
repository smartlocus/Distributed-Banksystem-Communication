import http.client

# Create a large sample HTTP request with a size larger than 1024 bytes
large_request = "GET /example HTTP/1.1\r\n" + ("X" * 1500)  # Total size exceeds 1024 bytes

# Set up the HTTP connection to your server
conn = http.client.HTTPConnection("localhost", 6789)  # Replace with your server's host and port

# Send the large request to the server
conn.request("GET", "/", large_request)
response = conn.getresponse()

# Read and print the response from the server
print(response.read().decode())

# Close the connection
conn.close()
