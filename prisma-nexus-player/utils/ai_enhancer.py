import numpy as np
from scipy import signal
from scipy.io import wavfile
import librosa
import soundfile as sf
import warnings
warnings.filterwarnings('ignore')

class AIEnhancer:
    def __init__(self):
        self.sample_rate = 44100
        self.effects = {
            'clear': self.clear_enhancement,
            'bass_boost': self.bass_boost,
            'vocal_enhance': self.vocal_enhancement,
            '3d_audio': self.spatial_audio,
            'noise_reduction': self.noise_reduction
        }
    
    def apply_effect(self, audio_file, effect_name):
        """Apply AI audio enhancement effect"""
        if effect_name not in self.effects:
            return {'status': 'error', 'message': 'Effect not found'}
        
        try:
            # Load audio file
            audio, sr = librosa.load(audio_file, sr=self.sample_rate)
            
            # Apply effect
            enhanced_audio = self.effects[effect_name](audio)
            
            # Save enhanced audio
            output_path = audio_file.replace('.', f'_{effect_name}.')
            sf.write(output_path, enhanced_audio, sr)
            
            return {
                'status': 'success',
                'effect': effect_name,
                'output': output_path
            }
        except Exception as e:
            return {'status': 'error', 'message': str(e)}
    
    def clear_enhancement(self, audio):
        """Clear audio enhancement - improves clarity"""
        # Apply high-pass filter to remove rumble
        b, a = signal.butter(4, 80/(self.sample_rate/2), 'high')
        enhanced = signal.filtfilt(b, a, audio)
        
        # Compress dynamic range slightly
        enhanced = np.sign(enhanced) * np.log1p(np.abs(enhanced))
        
        return enhanced
    
    def bass_boost(self, audio):
        """Enhanced bass boost using multiband processing"""
        # Low frequency boost
        b, a = signal.butter(4, 250/(self.sample_rate/2), 'low')
        low_freq = signal.filtfilt(b, a, audio)
        
        # Mix original with boosted low frequencies
        enhanced = audio + (low_freq * 1.5)
        
        return enhanced / np.max(np.abs(enhanced))
    
    def vocal_enhancement(self, audio):
        """Vocal enhancement using spectral processing"""
        # Compute STFT
        D = librosa.stft(audio)
        
        # Focus on vocal frequency range (300Hz - 3400Hz)
        freqs = librosa.fft_frequencies(sr=self.sample_rate)
        vocal_mask = (freqs >= 300) & (freqs <= 3400)
        
        # Boost vocal frequencies
        D[vocal_mask] *= 1.5
        
        # Reconstruct audio
        enhanced = librosa.istft(D)
        
        return enhanced / np.max(np.abs(enhanced))
    
    def spatial_audio(self, audio):
        """Create 3D spatial audio effect"""
        # Create stereo effect if mono
        if len(audio.shape) == 1:
            # Create pseudo-stereo with slight delay
            delay = int(0.02 * self.sample_rate)  # 20ms delay
            left = audio
            right = np.pad(audio, (delay, 0))[:len(audio)]
            
            # Apply HRTF-like filtering
            b, a = signal.butter(2, [200/(self.sample_rate/2), 8000/(self.sample_rate/2)], 'band')
            right = signal.filtfilt(b, a, right)
            
            enhanced = np.vstack([left, right])
        else:
            enhanced = audio
        
        return enhanced
    
    def noise_reduction(self, audio):
        """AI-based noise reduction using spectral subtraction"""
        # Compute STFT
        D = librosa.stft(audio)
        magnitude = np.abs(D)
        phase = np.angle(D)
        
        # Estimate noise from quietest parts
        noise_estimate = np.mean(np.sort(magnitude, axis=1)[:, :10], axis=1)
        
        # Apply spectral subtraction
        magnitude = np.maximum(magnitude - noise_estimate[:, np.newaxis], 0)
        
        # Reconstruct
        D_clean = magnitude * np.exp(1j * phase)
        enhanced = librosa.istft(D_clean)
        
        return enhanced / np.max(np.abs(enhanced))