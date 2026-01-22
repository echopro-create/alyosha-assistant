"""
Alyosha Waveform Animation 2026
Premium Siri-style aurora волна с bloom-эффектами
"""
import math
import random
from PyQt6.QtWidgets import QWidget
from PyQt6.QtCore import QTimer, Qt, QPointF, QRectF
from PyQt6.QtGui import (
    QPainter, QPainterPath, QLinearGradient, QRadialGradient,
    QColor, QPen, QBrush
)


class WaveformWidget(QWidget):
    """Анимированная aurora-волна в стиле Siri 2026"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.setMinimumHeight(100)
        self.setMaximumHeight(120)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        # Animation state
        self.phase = 0.0
        self.phase2 = 0.0
        self.phase3 = 0.0
        self.target_amplitude = 0.3
        self.current_amplitude = 0.3
        self.audio_level = 0.0
        self.smoothed_audio = 0.0
        
        # Particle system
        self.particles = []
        self._init_particles()
        
        # Color animation
        self.color_phase = 0.0
        
        # States
        self.is_listening = False
        self.is_thinking = False
        self.is_speaking = False
        
        # Animation timer (60 FPS)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._animate)
        self.timer.start(16)  # ~60 FPS
    
    def _init_particles(self):
        """Инициализация частиц для эффекта"""
        self.particles = []
        for _ in range(20):
            self.particles.append({
                'x': random.random(),
                'y': random.random() * 0.5 + 0.25,
                'size': random.random() * 3 + 1,
                'speed': random.random() * 0.01 + 0.005,
                'alpha': random.random() * 0.5 + 0.2,
                'phase': random.random() * math.pi * 2
            })
    
    def set_state(self, listening: bool = False, thinking: bool = False, speaking: bool = False):
        """Установить состояние анимации"""
        self.is_listening = listening
        self.is_thinking = thinking
        self.is_speaking = speaking
        
        if listening:
            self.target_amplitude = 0.9
        elif thinking:
            self.target_amplitude = 0.6
        elif speaking:
            self.target_amplitude = 0.75
        else:
            self.target_amplitude = 0.35
    
    def set_audio_level(self, level: float):
        """Установить уровень громкости для реакции волны"""
        self.audio_level = min(1.0, max(0.0, level))
        
        if self.is_listening:
            self.target_amplitude = 0.5 + level * 0.5
    
    def _animate(self):
        """Обновление анимации"""
        # Smooth amplitude transition (spring-like)
        diff = self.target_amplitude - self.current_amplitude
        self.current_amplitude += diff * 0.12
        
        # Smooth audio level
        self.smoothed_audio += (self.audio_level - self.smoothed_audio) * 0.15
        
        # Update phases and amplitude based on state
        speed_multiplier = 1.0
        if self.is_thinking:
            speed_multiplier = 2.2
            # Pulsating amplitude for thinking
            self.target_amplitude = 0.55 + math.sin(self.phase * 0.8) * 0.2
        elif self.is_speaking:
            speed_multiplier = 1.5
        elif self.is_listening:
            speed_multiplier = 1.2 + self.smoothed_audio * 0.8
        else:
             self.target_amplitude = 0.35 + math.sin(self.phase * 0.3) * 0.05
        
        self.phase += 0.035 * speed_multiplier
        self.phase2 += 0.028 * speed_multiplier
        self.phase3 += 0.042 * speed_multiplier
        self.color_phase += 0.015
        
        # Update particles
        for p in self.particles:
            p['x'] += p['speed']
            if p['x'] > 1.2:
                p['x'] = -0.2
                p['y'] = random.random() * 0.5 + 0.25
        
        self.update()
    
    def paintEvent(self, event):
        """Отрисовка волны"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        width = self.width()
        height = self.height()
        center_y = height / 2
        
        # Draw background glow
        self._draw_background_glow(painter, width, height, center_y)
        
        # Draw particles when active
        if self.is_listening or self.is_speaking or self.is_thinking:
            self._draw_particles(painter, width, height, center_y)
        
        # Draw aurora waves
        self._draw_aurora_waves(painter, width, center_y)
        
        # Draw center orb glow
        if self.is_listening or self.is_speaking or self.is_thinking:
            self._draw_center_orb(painter, width, center_y)
    
    def _draw_background_glow(self, painter: QPainter, width: int, height: int, center_y: float):
        """Мягкое фоновое свечение"""
        if not (self.is_listening or self.is_speaking or self.is_thinking):
            return
        
        intensity = self.current_amplitude * 0.3
        
        gradient = QRadialGradient(width / 2, center_y, width * 0.4)
        
        # Aurora colors based on state
        if self.is_listening:
            core_color = QColor(139, 92, 246, int(35 * intensity))
        elif self.is_thinking:
            core_color = QColor(245, 158, 11, int(30 * intensity))
        else:  # speaking
            core_color = QColor(16, 185, 129, int(35 * intensity))
        
        gradient.setColorAt(0, core_color)
        gradient.setColorAt(1, QColor(0, 0, 0, 0))
        
        painter.fillRect(0, 0, width, height, gradient)
    
    def _draw_particles(self, painter: QPainter, width: int, height: int, center_y: float):
        """Отрисовка частиц"""
        for p in self.particles:
            x = p['x'] * width
            
            # Particles follow wave
            wave_offset = math.sin(p['x'] * math.pi * 3 + self.phase + p['phase']) * 15
            y = center_y + wave_offset
            
            # Color based on position
            hue_shift = math.sin(self.color_phase + p['x'] * math.pi) * 30
            
            if self.is_listening:
                color = QColor.fromHsv(int(270 + hue_shift) % 360, 200, 255, int(p['alpha'] * 180 * self.current_amplitude))
            elif self.is_thinking:
                color = QColor.fromHsv(int(35 + hue_shift) % 360, 220, 255, int(p['alpha'] * 160 * self.current_amplitude))
            else:
                color = QColor.fromHsv(int(160 + hue_shift) % 360, 200, 255, int(p['alpha'] * 180 * self.current_amplitude))
            
            size = p['size'] * (1 + self.smoothed_audio * 0.5)
            
            painter.setBrush(QBrush(color))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawEllipse(QPointF(x, y), size, size)
    
    def _draw_aurora_waves(self, painter: QPainter, width: int, center_y: float):
        """Отрисовка aurora-волн с многослойным эффектом"""
        amplitude = self.current_amplitude * 30
        
        # Layer 1: Main wave with aurora gradient
        self._draw_wave_layer(
            painter, width, center_y, amplitude,
            self.phase, [0, 0.3, 0.7, 1.0],
            [
                (139, 92, 246, 220),   # Purple
                (236, 72, 153, 240),   # Pink
                (59, 130, 246, 220),   # Blue
                (139, 92, 246, 220),   # Purple
            ],
            line_width=4.0,
            opacity=1.0
        )
        
        # Layer 2: Secondary wave (shifted)
        self._draw_wave_layer(
            painter, width, center_y, amplitude * 0.7,
            self.phase2 + 0.8, [0, 0.4, 0.8, 1.0],
            [
                (6, 182, 212, 180),    # Cyan
                (139, 92, 246, 200),   # Purple
                (236, 72, 153, 180),   # Pink
                (6, 182, 212, 180),    # Cyan
            ],
            line_width=3.0,
            opacity=0.6
        )
        
        # Layer 3: Subtle background wave
        self._draw_wave_layer(
            painter, width, center_y, amplitude * 0.5,
            self.phase3 + 1.5, [0, 0.5, 1.0],
            [
                (16, 185, 129, 120),   # Emerald
                (59, 130, 246, 140),   # Blue
                (16, 185, 129, 120),   # Emerald
            ],
            line_width=2.0,
            opacity=0.4
        )
    
    def _draw_wave_layer(self, painter: QPainter, width: int, center_y: float,
                         amplitude: float, phase: float, 
                         gradient_stops: list, colors: list,
                         line_width: float, opacity: float):
        """Отрисовка одного слоя волны"""
        # Create gradient
        gradient = QLinearGradient(0, 0, width, 0)
        
        # Animate gradient with color shift
        shift = (math.sin(self.color_phase) + 1) * 0.1
        
        for i, stop in enumerate(gradient_stops):
            r, g, b, a = colors[i]
            adjusted_stop = min(1.0, max(0.0, stop + shift))
            gradient.setColorAt(adjusted_stop, QColor(r, g, b, a))
        
        # Build wave path
        path = QPainterPath()
        path.moveTo(0, center_y)
        
        for x in range(width + 1):
            t = x / width
            
            # Multi-harmonic wave
            y1 = math.sin(t * math.pi * 3.5 + phase) * amplitude
            y2 = math.sin(t * math.pi * 5.5 + phase * 1.4) * amplitude * 0.25
            y3 = math.sin(t * math.pi * 2.2 + phase * 0.6) * amplitude * 0.4
            
            # Audio reactivity
            audio_boost = 1.0 + self.smoothed_audio * 0.3
            
            # Smooth edge fade (more pronounced at edges)
            edge_fade = math.pow(math.sin(t * math.pi), 0.7)
            
            y = center_y + (y1 + y2 + y3) * edge_fade * audio_boost
            path.lineTo(x, y)
        
        # Draw with gradient
        pen = QPen(gradient, line_width)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
        
        painter.setOpacity(opacity)
        painter.setPen(pen)
        painter.drawPath(path)
        painter.setOpacity(1.0)
    
    def _draw_center_orb(self, painter: QPainter, width: int, center_y: float):
        """Отрисовка центрального orb свечения"""
        orb_size = 60 + self.smoothed_audio * 40 + math.sin(self.phase * 2) * 10
        
        # Outer glow
        gradient = QRadialGradient(width / 2, center_y, orb_size)
        
        # Color based on state
        if self.is_listening:
            gradient.setColorAt(0, QColor(139, 92, 246, int(80 * self.current_amplitude)))
            gradient.setColorAt(0.5, QColor(139, 92, 246, int(30 * self.current_amplitude)))
        elif self.is_thinking:
            gradient.setColorAt(0, QColor(245, 158, 11, int(70 * self.current_amplitude)))
            gradient.setColorAt(0.5, QColor(245, 158, 11, int(25 * self.current_amplitude)))
        else:  # speaking
            gradient.setColorAt(0, QColor(16, 185, 129, int(80 * self.current_amplitude)))
            gradient.setColorAt(0.5, QColor(16, 185, 129, int(30 * self.current_amplitude)))
        
        gradient.setColorAt(1, QColor(0, 0, 0, 0))
        
        painter.setBrush(QBrush(gradient))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(
            QPointF(width / 2, center_y),
            orb_size, orb_size * 0.6
        )
