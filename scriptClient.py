import requests
import socket
import sys

# The url of the example web site
url = ""

if len(sys.argv) >= 2:
    url = sys.argv[1]
    print(f"Url passed to the script: {url}")
else:
    print("Not enough arguments provided. 'python3 scriptToAccessWebServer.py url-server'")
    exit(-1)    #if there is no argument passed to the script

# Get the domain name from the URL
domain_name = url.split('//')[-1].split('/')[0]

# Perform a DNS lookup to get the IP address
ip_address = socket.gethostbyname(domain_name)

print(f"Host is trying to get the web page of the web server, with IP address: {ip_address}")

# Send an HTTP GET request
response = requests.get(url)

# Print the response status code and content
print(f"Response Status Code: {response.status_code}")
print("Response Content:")
print(response.text)