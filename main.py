import psutil
import time
import socket
import requests
import os
import json
import sys

def ensure_systemd_service_exists(service_name, exec_start, user='root'):
    service_path = f'/etc/systemd/system/{service_name}.service'
    if not os.path.exists(service_path):
        with open(service_path, 'w') as service_file:
            service_file.write(f"""[Unit]
Description=Custom Network Monitor Service

[Service]
ExecStart={exec_start}
User={user}
Restart=no

[Install]
WantedBy=multi-user.target
""")
        print(f"Service file {service_name}.service created.")
        # Reload systemd to recognize the new service file
        os.system('sudo systemctl daemon-reload')
        os.system(f'sudo systemctl enable {service_name}.service')
    else:
        print(f"Service file {service_name}.service already exists.")

def send_pushover_notification(message, user_key, api_token):
    url = 'https://api.pushover.net/1/messages.json'
    data = {
        'token': api_token,
        'user': user_key,
        'message': message
    }
    response = requests.post(url, data=data)
    if response.status_code == 200:
        print("Notification sent successfully.")
    else:
        print("Failed to send notification.")
        print(response.text)


def is_connected_to_internet(ip_address):
    try:
        # Attempt to connect to a well-known DNS server.
        sock = socket.create_connection((ip_address, 53), timeout=2)
        sock.close()
        return True
    except OSError:
        return False

def check_interfaces():
    addrs = psutil.net_if_addrs()
    status = psutil.net_if_stats()
    for intf, addr_list in addrs.items():
        if intf in status:  # Check if interface is known
            intf_status = status[intf]
            if intf_status.isup:  # Check if interface is up
                for addr in addr_list:
                    if addr.family == socket.AF_INET and addr.address != '127.0.0.1':  # Check for IPv4 addresses
                        if is_connected_to_internet('8.8.8.8'):
                            send_pushover_notification(f"Interface {intf} with IP {addr.address} is connected to the Internet.", user_key, api_token)
                            sys.exit() # Exit the script

if __name__ == "__main__":

    with open(sys.argv[1], 'r') as config_file:
        config = json.load(config_file)
        user_key = config['PUSHOVER_USER_KEY']
        api_token = config['PUSHOVER_API_TOKEN']

    service_name = "ipnotifier"
    exec_start = f"/usr/bin/python3 {os.path.abspath(__file__)} {os.path.abspath(os.getcwd())}/.config"

    # Check and create systemd service file if necessary
    ensure_systemd_service_exists(service_name, exec_start)

    while True:
        check_interfaces()
        time.sleep(10)  
