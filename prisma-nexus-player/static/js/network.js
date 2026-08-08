// Network Connectivity Module
class NetworkManager {
    constructor() {
        this.connectedDevices = [];
        this.isConnected = false;
        
        this.initialize();
    }
    
    initialize() {
        this.btnDiscover = document.getElementById('btnDiscover');
        this.deviceList = document.getElementById('deviceList');
        
        this.btnDiscover.addEventListener('click', () => this.discoverDevices());
        
        // Check network status periodically
        setInterval(() => this.checkNetworkStatus(), 5000);
    }
    
    async discoverDevices() {
        this.btnDiscover.innerHTML = '🔄 Discovering...';
        this.btnDiscover.disabled = true;
        
        try {
            const response = await fetch('/api/network/discover');
            const devices = await response.json();
            
            this.updateDeviceList(devices);
        } catch (error) {
            console.error('Error discovering devices:', error);
        } finally {
            this.btnDiscover.innerHTML = '🔍 Discover Devices';
            this.btnDiscover.disabled = false;
        }
    }
    
    updateDeviceList(devices) {
        this.deviceList.innerHTML = devices.map(device => `
            <div class="device-item">
                <div class="device-info">
                    <span class="device-icon">📱</span>
                    <div>
                        <div class="device-name">${device.name}</div>
                        <div class="device-ip">${device.ip}</div>
                    </div>
                </div>
                <button class="btn-connect" onclick="networkManager.connectToDevice('${device.ip}')">
                    Connect
                </button>
            </div>
        `).join('');
        
        if (devices.length === 0) {
            this.deviceList.innerHTML = '<p class="empty-state">No devices found</p>';
        }
    }
    
    async connectToDevice(ip) {
        try {
            const response = await fetch('/api/network/connect', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ ip: ip })
            });
            
            const result = await response.json();
            
            if (result.status === 'success') {
                this.connectedDevices.push({ ip: ip, name: result.message });
                this.isConnected = true;
                this.showConnectedIndicator();
            }
        } catch (error) {
            console.error('Error connecting to device:', error);
        }
    }
    
    async checkNetworkStatus() {
        try {
            const response = await fetch('/api/network/status');
            const status = await response.json();
            
            this.updateNetworkStatus(status);
        } catch (error) {
            console.error('Error checking network status:', error);
        }
    }
    
    updateNetworkStatus(status) {
        const networkTab = document.querySelector('[data-tab="network"]');
        if (status.connected_devices > 0) {
            networkTab.innerHTML = `🌐 Network (${status.connected_devices})`;
        }
    }
    
    showConnectedIndicator() {
        const indicator = document.createElement('div');
        indicator.className = 'network-indicator';
        indicator.innerHTML = `
            <span class="indicator-dot"></span>
            <span>${this.connectedDevices.length} device(s) connected</span>
        `;
        
        // Remove existing indicator
        const existing = document.querySelector('.network-indicator');
        if (existing) existing.remove();
        
        document.querySelector('.header').appendChild(indicator);
    }
    
    async syncPlayback(position) {
        if (!this.isConnected) return;
        
        for (const device of this.connectedDevices) {
            socket.emit('sync_playback', {
                device_ip: device.ip,
                position: position
            });
        }
    }
}

const networkManager = new NetworkManager();

// Add styles for network components
const style = document.createElement('style');
style.textContent = `
    .device-item {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 10px;
        background: rgba(255, 255, 255, 0.05);
        border-radius: 8px;
        margin-bottom: 10px;
    }
    
    .device-info {
        display: flex;
        align-items: center;
        gap: 10px;
    }
    
    .device-icon {
        font-size: 24px;
    }
    
    .device-name {
        font-weight: bold;
    }
    
    .device-ip {
        font-size: 12px;
        color: var(--text-secondary);
    }
    
    .btn-connect {
        padding: 5px 15px;
        background: var(--accent2);
        border: none;
        border-radius: 5px;
        color: white;
        cursor: pointer;
    }
    
    .network-indicator {
        display: flex;
        align-items: center;
        gap: 8px;
        padding: 5px 15px;
        background: rgba(78, 205, 196, 0.2);
        border-radius: 20px;
        font-size: 12px;
    }
    
    .indicator-dot {
        width: 8px;
        height: 8px;
        background: var(--accent2);
        border-radius: 50%;
        animation: pulse 2s infinite;
    }
    
    .modal {
        position: fixed;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        background: rgba(0, 0, 0, 0.8);
        display: flex;
        align-items: center;
        justify-content: center;
        z-index: 1000;
    }
    
    .modal-content {
        background: var(--primary-gradient);
        padding: 30px;
        border-radius: 15px;
        max-width: 600px;
        width: 90%;
    }
    
    .eq-controls {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(80px, 1fr));
        gap: 15px;
        margin: 20px 0;
    }
    
    .eq-band {
        text-align: center;
    }
    
    .eq-slider {
        width: 80px;
        -webkit-appearance: slider-vertical;
        height: 150px;
    }
    
    .eq-presets {
        display: flex;
        gap: 10px;
        flex-wrap: wrap;
        margin: 20px 0;
    }
    
    .preset-btn {
        padding: 8px 15px;
        background: rgba(255, 255, 255, 0.1);
        border: 1px solid var(--glass-border);
        border-radius: 5px;
        color: white;
        cursor: pointer;
    }
    
    .playlist-item {
        display: flex;
        align-items: center;
        gap: 10px;
        padding: 10px;
        background: rgba(255, 255, 255, 0.05);
        border-radius: 8px;
        margin-bottom: 5px;
        cursor: pointer;
        transition: all 0.3s;
    }
    
    .playlist-item:hover {
        background: rgba(255, 255, 255, 0.1);
    }
    
    .playlist-item.active {
        background: rgba(78, 205, 196, 0.2);
        border: 1px solid var(--accent2);
    }
    
    .visualizer-bar {
        animation: equalizer 0.5s ease infinite alternate;
    }
    
    @keyframes equalizer {
        0% { height: 10%; }
        100% { height: 90%; }
    }
    
    @keyframes slideIn {
        from { transform: translateX(100%); opacity: 0; }
        to { transform: translateX(0); opacity: 1; }
    }
    
    @keyframes slideOut {
        from { transform: translateX(0); opacity: 1; }
        to { transform: translateX(100%); opacity: 0; }
    }
`;
document.head.appendChild(style);