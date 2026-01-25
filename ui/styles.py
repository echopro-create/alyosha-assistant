# Цветовая палитра 2026 — Calm Deep Edition
COLORS = {
    "dark": {
        # Фоны (Deep Charcoal/Navy base instead of pure black)
        "bg_primary": "#0B0E14",        # Deepest Charcoal
        "bg_secondary": "#151921",      # Lighter Charcoal
        "bg_tertiary": "#1E232E",       # UI Surface
        "bg_glass": "rgba(255, 255, 255, 0.03)",   # Subtle glass
        "bg_glass_hover": "rgba(255, 255, 255, 0.06)",
        "bg_glass_active": "rgba(255, 255, 255, 0.09)",
        
        # Границы (Softened)
        "border": "rgba(255, 255, 255, 0.06)",
        "border_light": "rgba(255, 255, 255, 0.10)",
        "border_accent": "rgba(56, 189, 248, 0.3)",
        
        # Текст (Reduced contrast)
        "text_primary": "#F2F4F7",      # ~95% White
        "text_secondary": "#94A3B8",    # Slate 400
        "text_muted": "#64748B",        # Slate 500
        "text_dim": "#475569",          # Slate 600
        
        # Акценты (Soft Sky Blue)
        "accent": "#38BDF8",            # Sky 400
        "accent_light": "#7DD3FC",      # Sky 300
        "accent_dark": "#0284C7",       # Sky 600
        "accent_glow": "rgba(56, 189, 248, 0.25)",
        
        # Title gradient (Soft Silver)
        "title_primary": "#F8FAFC",
        "title_secondary": "#cbd5e1",
        
        # Aurora градиент (Calm Ocean)
        "aurora_1": "#0C4A6E",  # Sky 900
        "aurora_2": "#075985",  # Sky 800
        "aurora_3": "#0369A1",  # Sky 700
        "aurora_4": "#0284C7",  # Sky 600
        "aurora_5": "#38BDF8",  # Sky 400
        
        # Семантика (Pastel/Soft)
        "success": "#34D399",  # Emerald 400
        "success_glow": "rgba(52, 211, 153, 0.2)",
        "warning": "#FBBF24",  # Amber 400
        "warning_glow": "rgba(251, 191, 36, 0.2)",
        "error": "#F87171",    # Red 400
        "error_glow": "rgba(248, 113, 113, 0.2)",
        
        # Bubbles
        "user_bubble": "rgba(56, 189, 248, 0.10)",
        "user_bubble_border": "rgba(56, 189, 248, 0.2)",
        "assistant_bubble": "rgba(255, 255, 255, 0.04)",
        "assistant_bubble_border": "rgba(255, 255, 255, 0.08)",
        "system_bubble": "rgba(52, 211, 153, 0.08)",
        "system_bubble_border": "rgba(52, 211, 153, 0.2)",
        
        # Shadows (Organic)
        "shadow_sm": "rgba(0, 0, 0, 0.15)",
        "shadow_md": "rgba(0, 0, 0, 0.25)",
        "shadow_lg": "rgba(0, 0, 0, 0.35)",
        "shadow_accent": "rgba(56, 189, 248, 0.15)",
    }
}

def get_font_family() -> str:
    """Единый стек шрифтов 2026"""
    return "'Inter', 'Outfit', 'Segoe UI', system-ui, sans-serif"

def get_main_window_style(theme: str = "dark") -> str:
    """Стиль главного окна с gradient mesh"""
    c = COLORS[theme]
    return f"""
        QMainWindow {{
            background: transparent;
        }}
        
        QWidget#centralWidget {{
            background: {c["bg_primary"]};
            border-radius: 24px;
            border: 1px solid {c["border"]};
        }}
    """

def get_header_style(theme: str = "dark") -> str:
    """Стиль заголовка"""
    c = COLORS[theme]
    return f"""
        QWidget#headerWidget {{
            background: transparent;
            border-bottom: 1px solid {c["border"]};
            padding-bottom: 16px;
        }}
    """

def get_title_style(theme: str = "dark") -> str:
    """Стиль заголовка — Soft Silver"""
    c = COLORS[theme]
    return f"""
        color: {c["title_primary"]};
        font-size: 20px;
        font-weight: 600;
        font-family: {get_font_family()};
        letter-spacing: -0.02em;
    """

def get_control_button_style(theme: str = "dark") -> str:
    """Стиль кнопок управления (minimize, close)"""
    c = COLORS[theme]
    return f"""
        QPushButton {{
            background: transparent;
            border: none;
            border-radius: 8px;
            padding: 4px;
            font-size: 16px;
            font-weight: 400;
            color: {c["text_muted"]};
        }}
        
        QPushButton:hover {{
            background: {c["bg_glass_hover"]};
            color: {c["text_primary"]};
        }}
        
        QPushButton:pressed {{
            background: {c["bg_glass_active"]};
        }}
        
        QPushButton#closeButton:hover {{
            background: rgba(248, 113, 113, 0.15);
            color: {c["error"]};
        }}
    """

def get_chat_widget_style(theme: str = "dark") -> str:
    """Стиль чат-виджета"""
    c = COLORS[theme]
    return f"""
        QScrollArea {{
            background: transparent;
            border: none;
        }}
        
        QScrollArea > QWidget > QWidget {{
            background: transparent;
        }}
        
        QScrollBar:vertical {{
            background: transparent;
            width: 6px;
            margin: 0;
        }}
        
        QScrollBar::handle:vertical {{
            background: {c["bg_glass_hover"]};
            border-radius: 3px;
            min-height: 40px;
        }}
        
        QScrollBar::handle:vertical:hover {{
            background: {c["text_muted"]};
        }}
        
        QScrollBar::add-line:vertical,
        QScrollBar::sub-line:vertical {{
            height: 0;
        }}
        
        QScrollBar::add-page:vertical,
        QScrollBar::sub-page:vertical {{
            background: transparent;
        }}
    """

def get_input_style(theme: str = "dark") -> str:
    """Стиль поля ввода — Flat & Calm"""
    c = COLORS[theme]
    return f"""
        QLineEdit {{
            background: {c["bg_tertiary"]};
            border: 1px solid transparent;
            border-radius: 20px;
            padding: 12px 16px;
            font-size: 15px;
            color: {c["text_primary"]};
            font-family: {get_font_family()};
            selection-background-color: {c["accent"]};
        }}
        
        QLineEdit:hover {{
            background: {c["bg_secondary"]};
        }}
        
        QLineEdit:focus {{
            background: {c["bg_secondary"]};
            border: 1px solid {c["border_accent"]};
        }}
        
        QLineEdit::placeholder {{
            color: {c["text_muted"]};
        }}
    """

def get_button_style(theme: str = "dark") -> str:
    """Стиль кнопок — 2026 Soft"""
    c = COLORS[theme]
    return f"""
        QPushButton {{
            background: {c["bg_glass"]};
            border: 1px solid {c["border"]};
            border-radius: 12px;
            padding: 8px 16px;
            font-size: 14px;
            font-weight: 500;
            color: {c["text_primary"]};
            font-family: {get_font_family()};
        }}
        
        QPushButton:hover {{
            background: {c["bg_glass_hover"]};
            border-color: {c["border_light"]};
        }}
        
        QPushButton:pressed {{
            background: {c["bg_glass_active"]};
        }}
        
        QPushButton#primaryButton {{
            background: {c["accent_dark"]};
            border: none;
            color: white;
        }}
        
        QPushButton#primaryButton:hover {{
            background: {c["accent"]};
        }}
        
        QPushButton#sendButton {{
            background: transparent;
            border: none;
            border-radius: 20px;
            color: {c["text_muted"]};
            font-size: 18px;
        }}
        
        QPushButton#sendButton:hover {{
            color: {c["accent"]};
            background: {c["bg_glass_hover"]};
        }}

        QPushButton#voiceButton {{
            background: transparent;
            border: none;
            border-radius: 20px;
            color: {c["text_muted"]};
            font-size: 18px;
        }}
        
        QPushButton#voiceButton:hover {{
            color: {c["accent"]};
            background: {c["bg_glass_hover"]};
        }}
        
        QPushButton#dangerButton {{
            background: rgba(248, 113, 113, 0.1);
            border: 1px solid rgba(248, 113, 113, 0.3);
            color: {c["error"]};
        }}
        
        QPushButton#dangerButton:hover {{
            background: rgba(248, 113, 113, 0.2);
        }}
    """

def get_message_bubble_style(role: str, theme: str = "dark") -> str:
    """Стиль пузырька сообщения — Calm & Readable"""
    c = COLORS[theme]
    
    if role == "user":
        bg = c["user_bubble"]
        border = c["user_bubble_border"]
        border_radius = "18px 18px 4px 18px"
    elif role == "assistant":
        bg = c["assistant_bubble"]
        border = c["assistant_bubble_border"]
        border_radius = "18px 18px 18px 4px"
    else:  # system
        bg = c["system_bubble"]
        border = c["system_bubble_border"]
        border_radius = "12px"
    
    return f"""
        background: {bg};
        border: 1px solid {border};
        border-radius: {border_radius};
        padding: 12px 16px;
        color: {c["text_primary"]};
        font-size: 15px;
        font-family: {get_font_family()};
        line-height: 1.5;
    """

def get_role_label_style(role: str, theme: str = "dark") -> str:
    """Стиль лейбла роли в сообщении"""
    c = COLORS[theme]
    
    colors = {
        "assistant": c["accent"],
        "user": c["text_muted"],
        "system": c["accent_light"],
    }
    
    return f"""
        color: {colors.get(role, c["text_secondary"])};
        font-size: 11px;
        font-weight: 600;
        letter-spacing: 0.1em;
        text-transform: uppercase;
        padding: 0;
        margin: 0 0 4px 0;
        background: transparent;
        border: none;
        font-family: {get_font_family()};
    """

def get_status_label_style(state: str, theme: str = "dark") -> str:
    """Стиль лейбла статуса — Calm"""
    c = COLORS[theme]
    
    state_config = {
        "idle": {
            "color": c["text_muted"],
            "glow": "none"
        },
        "listening": {
            "color": c["accent"],
            "glow": c["accent_glow"]
        },
        "thinking": {
            "color": c["warning"],
            "glow": c["warning_glow"]
        },
        "speaking": {
            "color": c["success"],
            "glow": c["success_glow"]
        },
        "error": {
            "color": c["error"],
            "glow": c["error_glow"]
        },
    }
    
    cfg = state_config.get(state, state_config["idle"])
    
    return f"""
        color: {cfg["color"]};
        font-size: 13px;
        font-weight: 600;
        font-family: {get_font_family()};
        letter-spacing: 0.05em;
        text-transform: uppercase;
    """

def get_typing_indicator_style(theme: str = "dark") -> str:
    """Стиль индикатора печати"""
    c = COLORS[theme]
    return f"""
        background: {c["bg_tertiary"]};
        border: 1px solid {c["border"]};
        border-radius: 12px;
        padding: 8px 12px;
    """

def get_avatar_style(theme: str = "dark") -> str:
    """Стиль аватара ассистента"""
    c = COLORS[theme]
    return f"""
        background: qlineargradient(
            spread:pad, x1:0, y1:0, x2:1, y2:1,
            stop:0 {c["aurora_1"]},
            stop:0.5 {c["aurora_3"]},
            stop:1 {c["aurora_5"]}
        );
        border: none;
        border-radius: 16px;
    """

def get_confirmation_style(theme: str = "dark") -> str:
    """Стиль диалога подтверждения"""
    c = COLORS[theme]
    return f"""
        QFrame#confirmationDialog {{
            background: rgba(248, 113, 113, 0.05);
            border: 1px solid {c["text_muted"]};
            border-radius: 16px;
            padding: 20px;
        }}
    """

def get_model_badge_style(mode: str = "Auto", theme: str = "dark") -> str:
    """Стиль бейджа модели Gemini — Calm Pill"""
    c = COLORS[theme]
    
    return f"""
        QLabel {{
            background: {c["bg_glass"]};
            color: {c["text_secondary"]};
            border: 1px solid {c["border"]};
            border-radius: 8px;
            padding: 4px 10px;
            font-size: 11px;
            font-family: {get_font_family()};
            font-weight: 500;
        }}
        QLabel:hover {{
            background: {c["bg_glass_hover"]};
            color: {c["text_primary"]};
        }}
    """
