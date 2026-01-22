"""
Alyosha Voice Activity Detection
Robust speech detection using WebRTC VAD
"""
import webrtcvad
import numpy as np
import logging

logger = logging.getLogger(__name__)

class VoiceActivityDetector:
    """
    Detects human speech in audio stream using WebRTC VAD.
    Unlike simple energy threshold, this detects voice characteristics.
    """
    
    def __init__(self, sample_rate=16000, aggressiveness=1):
        """
        Initialize VAD.
        
        Args:
            sample_rate: Audio sample rate (must be 8000, 16000, 32000, or 48000)
            aggressiveness: 0 (least aggressive) to 3 (most aggressive filtering of non-speech)
        """
        self.vad = webrtcvad.Vad(aggressiveness)
        self.sample_rate = sample_rate
        self.frame_duration_ms = 30
        self.samples_per_frame = int(sample_rate * self.frame_duration_ms / 1000)
        
        # Buffer for incomplete frames
        self.buffer = b""
        
    def is_speech(self, audio_chunk: np.ndarray) -> bool:
        """
        Check if audio chunk contains speech.
        
        Args:
            audio_chunk: Numpy array of int16 samples
        
        Returns:
            True if speech detected
        """
        try:
            # Ensure correct type
            if audio_chunk.dtype != np.int16:
                audio_chunk = (audio_chunk * 32768).astype(np.int16)
                
            audio_bytes = audio_chunk.tobytes()
            self.buffer += audio_bytes
            
            # Process complete frames
            frame_size_bytes = self.samples_per_frame * 2  # 16-bit = 2 bytes per sample
            is_speech_frame = False
            
            while len(self.buffer) >= frame_size_bytes:
                frame = self.buffer[:frame_size_bytes]
                self.buffer = self.buffer[frame_size_bytes:]
                
                if self.vad.is_speech(frame, self.sample_rate):
                    is_speech_frame = True
                    # Optimization: detecting one frame of speech in chunk is usually enough
                    # but we continue to flush buffer
            
            if is_speech_frame:
                # logger.debug("VAD: Speech detected") # Very spammy
                pass
                
            return is_speech_frame
            
        except Exception as e:
            logger.error(f"VAD Error: {e}")
            return False

    def reset(self):
        self.buffer = b""
