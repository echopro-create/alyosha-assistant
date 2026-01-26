"""
Alyosha Icon System 2026
Centralized SVG icon factory for a premium, crisp UI without external asset dependencies.
Uses raw SVG XML strings to generate QIcons with dynamic coloring.
"""
from PyQt6.QtGui import QIcon, QPixmap, QPainter
from PyQt6.QtCore import Qt
from PyQt6.QtSvg import QSvgRenderer
from PyQt6.QtCore import QByteArray

from .styles import COLORS

class IconFactory:
    """Factory for creating colored QIcons from SVG paths"""
    
    # Phosphor Icons (Regular/Bold) - Hardcoded for self-containment
    _ICONS = {
        "send": """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 256 256"><path fill="{color}" d="M227.32,28.68a16,16,0,0,0-15.66-4.08l-152,47.49a16,16,0,0,0-10.22,19.23,16,16,0,0,0,14.73,11.39l49.51,6,35.79,93a16,16,0,0,0,15,10.26h0a16,16,0,0,0,15-10.26l47.5-152A16,16,0,0,0,227.32,28.68ZM161.41,178.65,133.05,105a8,8,0,0,0-4.78-4.76L54.43,71.62,194.7,27.79Z"/></svg>""",
        
        "mic": """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 256 256"><path fill="{color}" d="M128,176a48.05,48.05,0,0,0,48-48V64a48,48,0,0,0-96,0v64A48.05,48.05,0,0,0,128,176ZM96,64a32,32,0,0,1,64,0v64a32,32,0,0,1-64,0Zm96,64a8,8,0,0,1,16,0,80.09,80.09,0,0,1-72,79.6V232h16a8,8,0,0,1,0,16H104a8,8,0,0,1,0-16h16V207.6A80.09,80.09,0,0,1,48,128a8,8,0,0,1,16,0,64,64,0,0,0,128,0Z"/></svg>""",
        
        "mic_off": """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 256 256"><path fill="{color}" d="M213.38,221.92,168.69,179a80,80,0,0,1-120.69-51,8,8,0,0,1,16,0,64,64,0,0,0,94.1,47l-35-33.6A47.78,47.78,0,0,1,80,128V64a48,48,0,0,1,85.67-29l29-27.9A8,8,0,1,1,205.86,18.5l22.65,21.75a8,8,0,0,1,6.67,10.87L224.93,210.8A8,8,0,1,1,213.38,221.92ZM164.63,143.08,96,77.2V128a32,32,0,0,0,51.86,22.62,31.79,31.79,0,0,0,16.77-7.54ZM157.06,47.8A32,32,0,0,0,96.39,56.55L144,102.24V64A31.85,31.85,0,0,0,157.06,47.8Z"/></svg>""",
        
        "settings": """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 256 256"><path fill="{color}" d="M128,80a48,48,0,1,0,48,48A48.05,48.05,0,0,0,128,80Zm0,80a32,32,0,1,1,32-32A32,32,0,0,1,128,160Zm88-29.84q.06-2.16,0-4.32l14.92-18.64a8,8,0,0,0,1.48-7.06,107.21,107.21,0,0,0-10.88-26.25,8,8,0,0,0-6-3.93l-23.72-2.64q-1.48-1.56-3-3t-3.12-2.84l-2.64-23.72a8,8,0,0,0-3.93-6,107.21,107.21,0,0,0-26.25-10.88,8,8,0,0,0-7.06,1.48L127.16,47.16q-2.16-.06-4.32,0L104.2,32.25a8,8,0,0,0-7.06-1.48,107.21,107.21,0,0,0-26.25,10.88,8,8,0,0,0-3.93,6l-2.64,23.72q-1.58,1.42-3.12,2.84t-3,3l-23.72,2.64a8,8,0,0,0-6,3.93,107.21,107.21,0,0,0-10.88,26.25,8,8,0,0,0,1.48,7.06L37.16,136.16q-.06,2.16,0,4.32L22.24,159.12a8,8,0,0,0-1.48,7.06,107.21,107.21,0,0,0,10.88,26.25,8,8,0,0,0,6,3.93l23.72,2.64q1.49,1.58,3,3t3.12,2.84l2.64,23.72a8,8,0,0,0,3.93,6,107.21,107.21,0,0,0,26.25,10.88,8,8,0,0,0,7.06-1.48l18.64-14.92q2.16.06,4.32,0l18.64,14.92a8,8,0,0,0,7.06,1.48,107.21,107.21,0,0,0,26.25-10.88,8,8,0,0,0,3.93-6l2.64-23.72q1.56-1.4,3.12-2.84t3-3l23.72-2.64a8,8,0,0,0,6-3.93,107.21,107.21,0,0,0,10.88-26.25,8,8,0,0,0-1.48-7.06ZM203.52,156,180,174.8q-.78,3.94-2,7.78L174.67,212a91.3,91.3,0,0,1-16.71,6.93l-29-25.13q-4-.61-8-2-4,1.4-8,2L83.09,218.9a91.3,91.3,0,0,1-16.71-6.93l-3.35-29.47q-2.86-2.5-4.88-5.3L33.31,192.4a90.5,90.5,0,0,1-6.93-16.71l25.13-29q.61-4,2-8-1.4-4-2-8L26.38,101.6a91.3,91.3,0,0,1,6.93-16.71l29.47-3.35q2.51-2.86,5.3-4.87l-15.2-24.81a90.5,90.5,0,0,1,16.71-6.93l29,25.13q4,.61,8,2,4-1.4,8-2L138.1,37.1a91.3,91.3,0,0,1,16.71,6.93l3.35,29.47q2.86,2.5,4.88,5.3l24.81-15.2a90.5,90.5,0,0,1,6.93,16.71l-25.13,29q-.61,4-2,8,1.4,4,2,8l25.13,29.09A91.3,91.3,0,0,1,203.52,156Z"/></svg>""",
        
        "x": """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 256 256"><path fill="{color}" d="M205.66,194.34a8,8,0,0,1-11.32,11.32L128,139.31,61.66,205.66a8,8,0,0,1-11.32-11.32L116.69,128,50.34,61.66A8,8,0,0,1,61.66,50.34L128,116.69l66.34-66.35a8,8,0,0,1,11.32,11.32L139.31,128Z"/></svg>""",
        
        "minus": """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 256 256"><path fill="{color}" d="M224,128a8,8,0,0,1-8,8H40a8,8,0,0,1,0-16H216A8,8,0,0,1,224,128Z"/></svg>""",
        
        "copy": """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 256 256"><path fill="{color}" d="M216,32H88a8,8,0,0,0-8,8V80H40a8,8,0,0,0-8,8V216a8,8,0,0,0,8,8H168a8,8,0,0,0,8-8V176h40a8,8,0,0,0,8-8V40A8,8,0,0,0,216,32ZM160,208H48V96H160Zm48-48H176V88a8,8,0,0,0-8-8H96V48H208Z"/></svg>""",
        
        "check": """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 256 256"><path fill="{color}" d="M229.66,56.34a8,8,0,0,1,0,11.32l-136,136a8,8,0,0,1-11.32,0l-56-56a8,8,0,0,1,11.32-11.32L88,186.69,218.34,56.34A8,8,0,0,1,229.66,56.34Z"/></svg>""",

        "user": """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 256 256"><path fill="{color}" d="M231.9,212a120.7,120.7,0,0,0-67.19-36.2A64,64,0,1,0,91.29,175.8,120.7,120.7,0,0,0,24.1,212a8,8,0,1,0,13.8,8,104.1,104.1,0,0,1,180.2,0,8,8,0,1,0,13.8-8ZM72,96a56,56,0,1,1,56,56A56.06,56.06,0,0,1,72,96Z"/></svg>""",
        
        "cpu": """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 256 256"><path fill="{color}" d="M80,80v96H176V80Zm-16,88V88a8,8,0,0,1,8-8h92a8,8,0,0,1,8,8v80a8,8,0,0,1-8,8H72A8,8,0,0,1,64,168Z M248,88v80a16,16,0,0,1-16,16h-8v16a8,8,0,0,1-16,0V184H176v16a8,8,0,0,1-16,0V184H96v16a8,8,0,0,1-16,0V184H72v16a8,8,0,0,1-16,0V184H32a16,16,0,0,1-16-16V88A16,16,0,0,1,32,72H56V56a8,8,0,0,1,16,0V72H96V56a8,8,0,0,1,16,0V72h64V56a8,8,0,0,1,16,0V72h8v16a8,8,0,0,1,16,0V72h24A16,16,0,0,1,248,88Z"/></svg>""",
        
        "info": """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 256 256"><path fill="{color}" d="M128,24A104,104,0,1,0,232,128,104.11,104.11,0,0,0,128,24Zm0,192a88,88,0,1,1,88-88A88.1,88.1,0,0,1,128,216Zm16-40a8,8,0,0,1-8,8,16,16,0,0,1-16-16V128a8,8,0,0,1,0-16,16,16,0,0,1,16,16v40A8,8,0,0,1,144,176ZM128,84a12,12,0,1,1-12,12A12,12,0,0,1,128,84Z"/></svg>""",
        
        "menu": """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 256 256"><path fill="{color}" d="M224,128a8,8,0,0,1-8,8H40a8,8,0,0,1,0-16H216A8,8,0,0,1,224,128ZM40,72H216a8,8,0,0,0,0-16H40a8,8,0,0,0,0,16ZM216,184H40a8,8,0,0,0,0,16H216a8,8,0,0,0,0-16Z"/></svg>""",
        
        "terminal": """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 256 256"><path fill="{color}" d="M118.63,165.66a8,8,0,0,1-11.32,0L35.31,93.66a8,8,0,0,1,11.32-11.32L113,148.69l66.34-66.35a8,8,0,0,1,11.32,11.32Z" transform="rotate(-90 128 128)"/><rect x="120" y="160" width="88" height="16" rx="8" fill="{color}"/></svg>""",
        
        "plus": """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 256 256"><path fill="{color}" d="M224,128a8,8,0,0,1-8,8H136v80a8,8,0,0,1-16,0V136H40a8,8,0,0,1,0-16h80V40a8,8,0,0,1,16,0v80h80A8,8,0,0,1,224,128Z"/></svg>"""
    }

    @staticmethod
    def get_icon(name: str, color: str = None, size: int = 24) -> QIcon:
        """
        Get QIcon by name with specified color
        :param name: Icon name (e.g. 'send', 'mic')
        :param color: Hex color string (e.g. '#FFFFFF'). Defaults to theme text color.
        :param size: Target size for internal pixmap rendering
        """
        if name not in IconFactory._ICONS:
            return QIcon()
            
        if color is None:
            color = COLORS["dark"]["text_primary"]
            
        # 1. Prepare SVG content
        svg_content = IconFactory._ICONS[name].format(color=color)
        svg_bytes = QByteArray(svg_content.encode('utf-8'))
        
        # 2. Render to QPixmap
        renderer = QSvgRenderer(svg_bytes)
        pixmap = QPixmap(size, size)
        pixmap.fill(Qt.GlobalColor.transparent)
        
        painter = QPainter(pixmap)
        renderer.render(painter)
        painter.end()
        
        # 3. Return QIcon
        return QIcon(pixmap)
        
    @staticmethod
    def get_pixmap(name: str, color: str = None, size: int = 24) -> QPixmap:
        """Get QPixmap directly"""
        return IconFactory.get_icon(name, color, size).pixmap(size, size)

