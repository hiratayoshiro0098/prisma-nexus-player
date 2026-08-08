import socket
import json
import threading
from zeroconf import ServiceBrowser, Zeroconf, ServiceInfo
import requests

class NetworkManager:
    def __init__(self):
        self.device_name = socket.gethostname()
        self.local_ip = self.get_local_ip()
        self.connected_devices = []
        self.discovered_devices = []
        self.server_thread = None
        self.is_running = False
        
    def get_local_ip(self):
        """Get local IP address"""
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except:
            return "127.0.0.1"
    
    def get_status(self):
        """Get network status"""
        return {
            'device_name': self.device_name,
            'local_ip': self.local_ip,
            'connected_devices': len(self.connected_devices),
            'discovered_devices': len(self.discovered_devices),
            'is_running': self.is_running
        }
    
    def discover_devices(self):
        """Discover PNP devices on local network"""
        # Scan local network for other PNP instances
        devices = []
        base_ip = '.'.join(self.local_ip.split('.')[:3])
        
        def scan_ip(ip):
            try:
                response = requests.get(f'http://{ip}:5000/api/ping', timeout=0.5)
                if response.status_code == 200:
                    devices.append({
                        'ip': ip,
                        'name': response.json().get('device_name', 'Unknown'),
                        'port': 5000
                    })
            except:
                pass
        
        threads = []
        for i in range(1, 255):
            ip = f"{base_ip}.{i}"
            t = threading.Thread(target=scan_ip, args=(ip,))
            t.start()
            threads.append(t)
        
        for t in threads:
            t.join()
        
        self.discovered_devices = devices
        return devices
    
    def connect_to_device(self, device_ip):
        """Connect to another PNP device"""
        try:
            # Establish connection
            response = requests.post(
                f'http://{device_ip}:5000/api/network/connect',
                json={
                    'ip': self.local_ip,
                    'name': self.device_name
                }
            )
            
            if response.status_code == 200:
                self.connected_devices.append({
                    'ip': device_ip,
                    'name': response.json().get('name', 'Unknown')
                })
                return {'status': 'success', 'message': f'Connected to {device_ip}'}
            
        except Exception as e:
            return {'status': 'error', 'message': str(e)}
    
    def sync_playback(self, data):
        """Sync playback with connected devices"""
        for device in self.connected_devices:
            try:
                requests.post(
                    f'http://{device["ip"]}:5000/api/sync',
                    json=data,
                    timeout=2
                )
            except:
                pass
    
    def start_server(self):
        """Start network discovery server"""
        self.is_running = True
        # Start mDNS service
        zeroconf = Zeroconf()
        info = ServiceInfo(
            "_pnp._tcp.local.",
            f"{self.device_name}._pnp._tcp.local.",
            addresses=[socket.inet_aton(self.local_ip)],
            port=5000,
            properties={'device': 'PNP'}
        )
        zeroconf.register_service(info)
    
    def stop_server(self):
        """Stop network services"""
        self.is_running = False