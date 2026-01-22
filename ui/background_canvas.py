"""
Alyosha Static Background Canvas 2026
Premium "iOS 26.3 Black Glass" style — static, zero CPU overhead
"""
import random
from PyQt6.QtWidgets import QWidget
from PyQt6.QtCore import Qt, QRectF
from PyQt6.QtGui import (
    QPainter, QPainterPath, QLinearGradient, QRadialGradient,
    QColor, QPixmap, QImage
)


class BackgroundCanvas(QWidget):
    """Static 'Black Glass' premium background — no animation, no CPU usage"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setMinimumSize(100, 100)
        
        # Cached pixmap to avoid re-rendering
        self._cached_pixmap: QPixmap | None = None
        self._cached_size = None
        
        # Pre-generate noise pattern (once)
        self._noise_image = self._generate_noise_texture(256, 256)
    
    def _generate_noise_texture(self, width: int, height: int) -> QImage:
        """Generate subtle grain/noise texture for premium glass look"""
        image = QImage(width, height, QImage.Format.Format_ARGB32)
        image.fill(Qt.GlobalColor.transparent)
        
        # Create subtle noise pixels
        for y in range(height):
            for x in range(width):
                # Very sparse, subtle noise
                if random.random() < 0.03:  # 3% pixel density
                    alpha = random.randint(3, 12)  # Very faint
                    gray = random.randint(200, 255)  # Light specks
                    image.setPixelColor(x, y, QColor(gray, gray, gray, alpha))
        
        return image
    
    def paintEvent(self, event):
        """Paint static background — cached for performance"""
        size = self.size()
        
        # Re-render only if size changed
        if self._cached_pixmap is None or self._cached_size != size:
            self._render_static_background()
        
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.drawPixmap(0, 0, self._cached_pixmap)
    
    def _render_static_background(self):
        """Render the static premium background once"""
        width = self.width()
        height = self.height()
        corner_radius = 20
        
        # Create pixmap cache
        self._cached_pixmap = QPixmap(self.size())
        self._cached_pixmap.fill(Qt.GlobalColor.transparent)
        self._cached_size = self.size()
        
        painter = QPainter(self._cached_pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        
        # Clip to rounded rectangle
        clip_path = QPainterPath()
        clip_path.addRoundedRect(QRectF(0, 0, width, height), corner_radius, corner_radius)
        painter.setClipPath(clip_path)
        
        # === Layer 1: Deep ocean gradient base ===
        gradient = QLinearGradient(0, 0, width * 0.3, height)
        gradient.setColorAt(0.0, QColor(5, 15, 25))      # Deep ocean black
        gradient.setColorAt(0.4, QColor(8, 20, 35))      # Blue-black
        gradient.setColorAt(0.7, QColor(5, 12, 22))      # Near black
        gradient.setColorAt(1.0, QColor(3, 8, 15))       # True deep
        painter.fillRect(0, 0, width, height, gradient)
        
        # === Layer 2: Subtle cyan radial glow (top-center) ===
        radial_top = QRadialGradient(width * 0.5, height * 0.15, width * 0.7)
        radial_top.setColorAt(0.0, QColor(14, 165, 233, 25))   # Cyan center
        radial_top.setColorAt(0.4, QColor(6, 95, 140, 12))     # Fade
        radial_top.setColorAt(1.0, QColor(0, 0, 0, 0))         # Transparent
        painter.fillRect(0, 0, width, height, radial_top)
        
        # === Layer 3: Bottom edge glow (subtle blue) ===
        radial_bottom = QRadialGradient(width * 0.5, height * 1.2, width * 0.8)
        radial_bottom.setColorAt(0.0, QColor(59, 130, 246, 15))  # Blue
        radial_bottom.setColorAt(0.5, QColor(30, 64, 120, 8))
        radial_bottom.setColorAt(1.0, QColor(0, 0, 0, 0))
        painter.fillRect(0, 0, width, height, radial_bottom)
        
        # === Layer 4: Glass reflection band (top) ===
        reflection = QLinearGradient(0, 0, 0, height * 0.25)
        reflection.setColorAt(0.0, QColor(255, 255, 255, 8))
        reflection.setColorAt(0.3, QColor(255, 255, 255, 4))
        reflection.setColorAt(1.0, QColor(255, 255, 255, 0))
        painter.fillRect(0, 0, width, int(height * 0.25), reflection)
        
        # === Layer 5: Subtle noise/grain texture ===
        # Tile the noise texture across the background
        if self._noise_image:
            noise_w = self._noise_image.width()
            noise_h = self._noise_image.height()
            for y in range(0, height, noise_h):
                for x in range(0, width, noise_w):
                    painter.drawImage(x, y, self._noise_image)
        
        # === Layer 6: Inner shadow for depth ===
        inner_shadow = QLinearGradient(0, 0, 0, 30)
        inner_shadow.setColorAt(0.0, QColor(0, 0, 0, 30))
        inner_shadow.setColorAt(1.0, QColor(0, 0, 0, 0))
        painter.fillRect(0, 0, width, 30, inner_shadow)
        
        painter.end()
    
    def resizeEvent(self, event):
        """Invalidate cache on resize"""
        self._cached_pixmap = None
        super().resizeEvent(event)
    
    def stop(self):
        """No-op for compatibility — no animation to stop"""
        pass
