import socket
import psutil

wifi_ip = "127.0.0.1"

# Priority 1: Check Wi-Fi adapter specifically
for interface, addrs in psutil.net_if_addrs().items():
    for addr in addrs:
        if addr.family == socket.AF_INET:
            ip = addr.address
            if not ip.startswith('127.') and not ip.startswith('169.254.'):
                if 'wifi' in interface.lower() or 'wi-fi' in interface.lower():
                    wifi_ip = ip
                    break

# Priority 2: Fallback to non-loopback 192.168.x.x
if wifi_ip == "127.0.0.1":
    for interface, addrs in psutil.net_if_addrs().items():
        for addr in addrs:
            if addr.family == socket.AF_INET:
                ip = addr.address
                if ip.startswith('192.168.'):
                    wifi_ip = ip
                    break

print('========================================================')
print('  REAL WI-FI LOCAL URL FOR ANDROID:')
print(f'  --> http://{wifi_ip}:8000')
print('========================================================')
