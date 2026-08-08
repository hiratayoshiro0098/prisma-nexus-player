// AI Audio Enhancement Module
class AIEnhancer {
    constructor() {
        this.isActive = false;
        this.currentEffect = 'none';
        this.effects = {
            clear: { name: 'Clear Audio', icon: '🔊' },
            bass_boost: { name: 'Bass Boost', icon: '💪' },
            vocal_enhance: { name: 'Vocal Enhance', icon: '🎤' },
            '3d_audio': { name: '3D Spatial Audio', icon: '🌍' },
            noise_reduction: { name: 'Noise Reduction', icon: '🔇' }
        };
        
        this.initialize();
    }
    
    initialize() {
        this.btnAIEnhance = document.getElementById('btnAIEnhance');
        this.btnEqualizer = document.getElementById('btnEqualizer');
        this.btn3DAudio = document.getElementById('btn3DAudio');
        this.aiPreset = document.getElementById('aiPreset');
        
        this.btnAIEnhance.addEventListener('click', () => this.toggleAI());
        this.btnEqualizer.addEventListener('click', () => this.showEqualizer());
        this.btn3DAudio.addEventListener('click', () => this.toggle3DAudio());
        this.aiPreset.addEventListener('change', (e) => this.applyPreset(e.target.value));
    }
    
    toggleAI() {
        this.isActive = !this.isActive;
        this.btnAIEnhance.classList.toggle('active', this.isActive);
        
        if (this.isActive) {
            this.applyEffect('clear');
        } else {
            this.removeEffect();
        }
    }
    
    toggle3DAudio() {
        this.btn3DAudio.classList.toggle('active');
        if (this.btn3DAudio.classList.contains('active')) {
            this.applyEffect('3d_audio');
        } else {
            this.removeEffect();
        }
    }
    
    applyPreset(preset) {
        if (preset === 'none') {
            this.removeEffect();
            return;
        }
        
        this.applyEffect(preset);
    }
    
    async applyEffect(effect) {
        this.currentEffect = effect;
        
        try {
            const response = await fetch('/api/ai/enhance', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ effect: effect })
            });
            
            const result = await response.json();
            
            if (result.status === 'success') {
                this.showNotification(`Applied: ${this.effects[effect].name}`);
            }
        } catch (error) {
            console.error('Error applying AI effect:', error);
        }
    }
    
    async removeEffect() {
        this.currentEffect = 'none';
        this.isActive = false;
        this.btnAIEnhance.classList.remove('active');
        this.btn3DAudio.classList.remove('active');
        
        await this.applyEffect('none');
    }
    
    showEqualizer() {
        // Create equalizer modal
        const modal = document.createElement('div');
        modal.className = 'modal';
        modal.innerHTML = `
            <div class="modal-content">
                <h2>Equalizer</h2>
                <div class="eq-controls">
                    ${this.createEQBands()}
                </div>
                <div class="eq-presets">
                    <button class="preset-btn">Flat</button>
                    <button class="preset-btn">Rock</button>
                    <button class="preset-btn">Pop</button>
                    <button class="preset-btn">Jazz</button>
                    <button class="preset-btn">Classical</button>
                </div>
                <button class="btn-close-modal">Close</button>
            </div>
        `;
        
        document.body.appendChild(modal);
        modal.addEventListener('click', (e) => {
            if (e.target === modal) {
                modal.remove();
            }
        });
    }
    
    createEQBands() {
        const bands = [
            { freq: '32', label: 'Sub Bass' },
            { freq: '64', label: 'Bass' },
            { freq: '125', label: 'Low Mid' },
            { freq: '250', label: 'Mid' },
            { freq: '500', label: 'Mid' },
            { freq: '1k', label: 'High Mid' },
            { freq: '2k', label: 'Presence' },
            { freq: '4k', label: 'Treble' },
            { freq: '8k', label: 'High Treble' },
            { freq: '16k', label: 'Air' }
        ];
        
        return bands.map(band => `
            <div class="eq-band">
                <label>${band.freq}Hz</label>
                <input type="range" min="-12" max="12" value="0" class="eq-slider">
                <span>${band.label}</span>
            </div>
        `).join('');
    }
    
    showNotification(message) {
        const notification = document.createElement('div');
        notification.className = 'notification';
        notification.textContent = message;
        notification.style.cssText = `
            position: fixed;
            bottom: 20px;
            right: 20px;
            background: rgba(78, 205, 196, 0.9);
            color: white;
            padding: 15px 25px;
            border-radius: 10px;
            animation: slideIn 0.5s ease;
            z-index: 1000;
        `;
        
        document.body.appendChild(notification);
        
        setTimeout(() => {
            notification.style.animation = 'slideOut 0.5s ease';
            setTimeout(() => notification.remove(), 500);
        }, 3000);
    }
}

const aiEnhancer = new AIEnhancer();