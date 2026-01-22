"""
Alyosha Animated Background Canvas 2026
Premium "Black Glass" style subtle background animation
Replaces the removed waveform with non-intrusive ambient effects
"""
import math
import random
from PyQt6.QtWidgets import QWidget
from PyQt6.QtCore import QTimer, Qt, QPointF, QRectF
from PyQt6.QtGui import (
    QPainter, QPainterPath, QLinearGradient, QRadialGradient,
    QColor, QPen, QBrush
)


class BackgroundCanvas(QWidget):
    """Subtle animated background with black glass effects (30 FPS for battery)"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setMinimumSize(100, 100)
        
        # Animation phases
        self.gradient_phase = 0.0
        self.particle_phase = 0.0
        self.reflection_phase = 0.0
        
        # Sparse particle system (20 particles, slow)
        self.particles = []
        self._init_particles()
        
        # Animation timer (30 FPS - battery optimized)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._animate)
        self.timer.start(33)  # ~30 FPS
    
    def _init_particles(self):
        """Initialize sparse particle system"""
        self.particles = []
        for _ in range(15):  # Fewer particles for subtlety
            self.particles.append({
                'x': random.random(),
                'y': random.random(),
                'size': random.random() * 2 + 0.5,
                'speed': random.random() * 0.0015 + 0.0005,  # Very slow
                'alpha': random.random() * 0.04 + 0.01,  # Very faint
                'phase': random.random() * math.pi * 2,
                'drift': random.random() * 0.001 - 0.0005  # Subtle drift
            })
    
    def _animate(self):
        """Update animation (30 FPS)"""
        # Slow gradient phase rotation (10s full cycle)
        self.gradient_phase += 0.003
        
        # Particle phase
        self.particle_phase += 0.01
        
        # Reflection sweep
        self.reflection_phase += 0.008
        
        # Update particles
        for p in self.particles:
            p['x'] += p['speed']
            p['y'] += p['drift'] + math.sin(self.particle_phase + p['phase']) * 0.0002
            
            # Wrap around
            if p['x'] > 1.1:
                p['x'] = -0.1
                p['y'] = random.random()
            if p['y'] < -0.1 or p['y'] > 1.1:
                p['y'] = random.random()
        
        self.update()
    
    def paintEvent(self, event):
        """Paint the animated background with smooth rounded corners"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        width = self.width()
        height = self.height()
        
        # Clip to rounded rectangle for smooth corners
        clip_path = QPainterPath()
        corner_radius = 20
        clip_path.addRoundedRect(QRectF(0, 0, width, height), corner_radius, corner_radius)
        painter.setClipPath(clip_path)
        
        # 1. Animated gradient background
        self._draw_gradient_mesh(painter, width, height)
        
        # 2. Subtle particles
        self._draw_particles(painter, width, height)
        
        # 3. Glass reflection bands
        self._draw_reflections(painter, width, height)
    
    def _draw_gradient_mesh(self, painter: QPainter, width: int, height: int):
        """Draw slowly shifting gradient mesh - Cyan/Blue theme"""
        # Primary gradient with animated hue shift
        hue_shift = math.sin(self.gradient_phase) * 10  # ±10 degrees
        
        gradient = QLinearGradient(0, 0, width, height)
        
        # Cyan/Blue gradient (hue 195-210 range)
        base_hue = 200 + hue_shift  # Cyan base
        
        # Deep ocean blues
        gradient.setColorAt(0.0, QColor.fromHsv(int(base_hue) % 360, 70, 20, 255))
        gradient.setColorAt(0.3, QColor.fromHsv(int(base_hue + 15) % 360, 60, 25, 255))
        gradient.setColorAt(0.7, QColor.fromHsv(int(base_hue - 10) % 360, 65, 18, 255))
        gradient.setColorAt(1.0, QColor.fromHsv(int(base_hue + 20) % 360, 55, 22, 255))
        
        painter.fillRect(0, 0, width, height, gradient)
        
        # Secondary radial glow (center) - Soft Cyan
        glow_intensity = (math.sin(self.gradient_phase * 1.5) + 1) * 0.5  # 0-1
        
        radial = QRadialGradient(width * 0.5, height * 0.4, width * 0.6)
        # Cyan glow: rgb(14, 165, 233) = #0EA5E9
        radial.setColorAt(0.0, QColor(14, 165, 233, int(20 + glow_intensity * 15)))
        radial.setColorAt(0.5, QColor(14, 165, 233, int(8 + glow_intensity * 6)))
        radial.setColorAt(1.0, QColor(0, 0, 0, 0))
        
        painter.fillRect(0, 0, width, height, radial)
    
    def _draw_particles(self, painter: QPainter, width: int, height: int):
        """Draw sparse floating particles - Cyan theme"""
        for p in self.particles:
            x = p['x'] * width
            y = p['y'] * height
            
            # Pulsing alpha
            alpha_mod = (math.sin(self.particle_phase * 2 + p['phase']) + 1) * 0.5
            alpha = int((0.12 + alpha_mod * 0.08) * 255)
            
            # Cyan/Blue particles (hue 190-210)
            hue = 195 + math.sin(p['phase']) * 15
            color = QColor.fromHsv(int(hue) % 360, 120, 255, alpha)
            
            painter.setBrush(QBrush(color))
            painter.setPen(Qt.PenStyle.NoPen)
            
            size = (p['size'] + 1.5) * (1 + math.sin(self.particle_phase + p['phase']) * 0.2)  # Larger particles
            painter.drawEllipse(QPointF(x, y), size, size)
    
    def _draw_reflections(self, painter: QPainter, width: int, height: int):
        """Draw glass reflection bands"""
        # Single slow-moving reflection band
        band_pos = (math.sin(self.reflection_phase) + 1) * 0.5  # 0-1
        band_y = band_pos * height * 0.6  # Upper 60% only
        band_width = height * 0.15
        
        gradient = QLinearGradient(0, band_y, 0, band_y + band_width)
        gradient.setColorAt(0.0, QColor(255, 255, 255, 0))
        gradient.setColorAt(0.4, QColor(255, 255, 255, 20))  # More visible
        gradient.setColorAt(0.6, QColor(255, 255, 255, 15))
        gradient.setColorAt(1.0, QColor(255, 255, 255, 0))
        
        painter.fillRect(0, int(band_y), width, int(band_width), gradient)
        
        # Second band (offset, even more subtle)
        band2_pos = (math.sin(self.reflection_phase + 2) + 1) * 0.5
        band2_y = band2_pos * height * 0.8
        band2_width = height * 0.1
        
        gradient2 = QLinearGradient(0, band2_y, 0, band2_y + band2_width)
        gradient2.setColorAt(0.0, QColor(255, 255, 255, 0))
        gradient2.setColorAt(0.5, QColor(255, 255, 255, 4))
        gradient2.setColorAt(1.0, QColor(255, 255, 255, 0))
        
        painter.fillRect(0, int(band2_y), width, int(band2_width), gradient2)
    
    def stop(self):
        """Stop animation"""
        self.timer.stop()
