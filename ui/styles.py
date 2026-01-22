"""
Alyosha UI Styles 2026
AMOLED Black премиальный glassmorphism дизайн
"""

# Цветовая палитра 2026 — AMOLED Black Edition
COLORS = {
    "dark": {
        # Фоны (TRUE AMOLED BLACK for OLED power savings)
        "bg_primary": "rgba(0, 0, 0, 1.0)",        # Pure black
        "bg_secondary": "rgba(5, 5, 8, 0.98)",     # Near black
        "bg_tertiary": "rgba(10, 10, 15, 0.96)",   # Slight gray
        "bg_glass": "rgba(255, 255, 255, 0.02)",   # Very subtle glass
        "bg_glass_hover": "rgba(255, 255, 255, 0.05)",
        "bg_glass_active": "rgba(255, 255, 255, 0.08)",
        
        # Границы (subtle on black)
        "border": "rgba(255, 255, 255, 0.04)",
        "border_light": "rgba(255, 255, 255, 0.07)",
        "border_accent": "rgba(14, 165, 233, 0.35)",
        
        # Текст
        "text_primary": "#FFFFFF",
        "text_secondary": "rgba(255, 255, 255, 0.80)",
        "text_muted": "rgba(255, 255, 255, 0.50)",
        "text_dim": "rgba(255, 255, 255, 0.55)",
        
        # Акценты (2026 Soft Cyan/Teal - Apple-style)
        "accent": "#0EA5E9",           # Sky Blue
        "accent_light": "#38BDF8",     # Lighter Sky
        "accent_dark": "#0284C7",      # Deeper Sky
        "accent_glow": "rgba(14, 165, 233, 0.3)",
        
        # Title gradient (premium silver-white)
        "title_primary": "#FFFFFF",
        "title_secondary": "rgba(255, 255, 255, 0.9)",
        
        # Aurora градиент (subtle blues/cyans only)
        "aurora_1": "#0EA5E9",  # Sky Blue
        "aurora_2": "#06B6D4",  # Cyan
        "aurora_3": "#3B82F6",  # Blue
        "aurora_4": "#0284C7",  # Deep Sky
        "aurora_5": "#22D3EE",  # Light Cyan
        
        # Семантика
        "success": "#10B981",  # Emerald (actual green)
        "success_glow": "rgba(16, 185, 129, 0.3)",
        "warning": "#F59E0B",
        "warning_glow": "rgba(245, 158, 11, 0.3)",
        "error": "#EF4444",
        "error_glow": "rgba(239, 68, 68, 0.3)",
        
        # Bubbles (darker for AMOLED)
        "user_bubble": "rgba(14, 165, 233, 0.10)",
        "user_bubble_border": "rgba(14, 165, 233, 0.22)",
        "assistant_bubble": "rgba(255, 255, 255, 0.03)",
        "assistant_bubble_border": "rgba(255, 255, 255, 0.06)",
        "system_bubble": "rgba(16, 185, 129, 0.06)",
        "system_bubble_border": "rgba(16, 185, 129, 0.18)",
        
        # Shadows (neutral)
        "shadow_sm": "rgba(0, 0, 0, 0.12)",
        "shadow_md": "rgba(0, 0, 0, 0.20)",
        "shadow_lg": "rgba(0, 0, 0, 0.30)",
        "shadow_accent": "rgba(14, 165, 233, 0.20)",
    }
}

def get_main_window_style(theme: str = "dark") -> str:
    """Стиль главного окна с gradient mesh"""
    c = COLORS[theme]
    return f"""
        QMainWindow {{
            background: transparent;
        }}
        
        QWidget#centralWidget {{
            background: qlineargradient(
                spread:pad, x1:0, y1:0, x2:1, y2:1,
                stop:0 {c["bg_primary"]},
                stop:0.5 {c["bg_secondary"]},
                stop:1 {c["bg_tertiary"]}
            );
            border-radius: 20px;
            border: 1px solid {c["border_light"]};
        }}
    """

def get_header_style(theme: str = "dark") -> str:
    """Стиль заголовка с shimmer"""
    c = COLORS[theme]
    return f"""
        QWidget#headerWidget {{
            background: transparent;
            border-bottom: 1px solid {c["border"]};
            padding-bottom: 12px;
        }}
    """

def get_title_style(theme: str = "dark") -> str:
    """Стиль заголовка — чистый белый (iOS 2026 style)"""
    c = COLORS[theme]
    return f"""
        color: #FFFFFF;
        font-size: 24px;
        font-weight: 700;
        font-family: 'SF Pro Display', 'Montserrat', 'Outfit', 'Ubuntu', sans-serif;
        letter-spacing: -0.5px;
    """

def get_control_button_style(theme: str = "dark") -> str:
    """Стиль кнопок управления (minimize, close)"""
    c = COLORS[theme]
    return f"""
        QPushButton {{
            background: {c["bg_glass"]};
            border: 1px solid {c["border"]};
            border-radius: 16px;
            padding: 0;
            font-size: 14px;
            font-weight: 400;
            color: {c["text_muted"]};
        }}
        
        QPushButton:hover {{
            background: {c["bg_glass_hover"]};
            border-color: {c["border_light"]};
            color: {c["text_primary"]};
        }}
        
        QPushButton:pressed {{
            background: {c["bg_glass_active"]};
        }}
        
        QPushButton#closeButton:hover {{
            background: rgba(239, 68, 68, 0.25);
            border-color: rgba(239, 68, 68, 0.5);
            color: #EF4444;
        }}
    """

def get_chat_widget_style(theme: str = "dark") -> str:
    """Стиль чат-виджета"""
    c = COLORS[theme]
    return f"""
        QScrollArea {{
            background: transparent;
            border: none;
            border-radius: 16px;
        }}
        
        QScrollArea > QWidget > QWidget {{
            background: transparent;
        }}
        
        QScrollBar:vertical {{
            background: rgba(255, 255, 255, 0.02);
            width: 8px;
            margin: 12px 3px;
            border-radius: 4px;
        }}
        
        QScrollBar::handle:vertical {{
            background: rgba(255, 255, 255, 0.12);
            border-radius: 4px;
            min-height: 50px;
        }}
        
        QScrollBar::handle:vertical:hover {{
            background: rgba(255, 255, 255, 0.2);
        }}
        
        QScrollBar::handle:vertical:pressed {{
            background: {c["accent"]};
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
    """Стиль поля ввода — premium floating"""
    c = COLORS[theme]
    return f"""
        QLineEdit {{
            background: rgba(255, 255, 255, 0.08);
            border: 1px solid rgba(255, 255, 255, 0.2);
            border-radius: 20px;
            padding: 10px 18px;
            font-size: 15px;
            color: #FFFFFF;
            font-family: 'Ubuntu', 'Inter', 'Outfit', 'Noto Sans', sans-serif;
            selection-background-color: {c["accent"]};
        }}
        
        QLineEdit:hover {{
            border-color: rgba(255, 255, 255, 0.3);
            background: rgba(255, 255, 255, 0.12);
        }}
        
        QLineEdit:focus {{
            border-color: {c["accent"]};
            background: rgba(255, 255, 255, 0.15);
        }}
        
        QLineEdit::placeholder {{
            color: rgba(255, 255, 255, 0.5);
        }}
    """

def get_button_style(theme: str = "dark") -> str:
    """Стиль кнопок — glassmorphism 2026"""
    c = COLORS[theme]
    return f"""
        QPushButton {{
            background: {c["bg_glass"]};
            border: 1px solid {c["border"]};
            border-radius: 14px;
            padding: 10px 20px;
            font-size: 14px;
            font-weight: 600;
            color: {c["text_primary"]};
            font-family: 'Montserrat', 'Outfit', 'Ubuntu Medium', 'Inter', sans-serif;
            letter-spacing: 0.2px;
        }}
        
        QPushButton:hover {{
            background: {c["bg_glass_hover"]};
            border-color: {c["border_accent"]};
        }}
        
        QPushButton:pressed {{
            background: {c["bg_glass_active"]};
        }}
        
        QPushButton#primaryButton {{
            background: qlineargradient(
                spread:pad, x1:0, y1:0, x2:1, y2:1,
                stop:0 {c["accent"]},
                stop:1 {c["aurora_2"]}
            );
            border: none;
            border-radius: 24px;
            color: white;
            font-weight: 700;
        }}
        
        QPushButton#primaryButton:hover {{
            background: qlineargradient(
                spread:pad, x1:0, y1:0, x2:1, y2:1,
                stop:0 {c["accent_light"]},
                stop:1 #F472B6
            );
        }}
        
        QPushButton#sendButton {{
            background: rgba(255, 255, 255, 0.12);
            border: none;
            border-radius: 23px;
            color: white;
            font-size: 16px;
        }}
        
        QPushButton#sendButton:hover {{
            background: rgba(255, 255, 255, 0.18);
        }}
        
        QPushButton#dangerButton {{
            background: rgba(239, 68, 68, 0.15);
            border: 1px solid rgba(239, 68, 68, 0.4);
            color: #FCA5A5;
        }}
        
        QPushButton#dangerButton:hover {{
            background: rgba(239, 68, 68, 0.3);
            border-color: rgba(239, 68, 68, 0.6);
            color: #FECACA;
        }}
    """

def get_message_bubble_style(role: str, theme: str = "dark") -> str:
    """Стиль пузырька сообщения — 3D glassmorphism"""
    c = COLORS[theme]
    
    if role == "user":
        bg = c["user_bubble"]
        border = c["user_bubble_border"]
        border_radius = "20px 20px 6px 20px"
        shadow = f"0 4px 16px {c['shadow_accent']}"
    elif role == "assistant":
        bg = c["assistant_bubble"]
        border = c["assistant_bubble_border"]
        border_radius = "20px 20px 20px 6px"
        shadow = f"0 4px 12px {c['shadow_sm']}"
    else:  # system
        bg = c["system_bubble"]
        border = c["system_bubble_border"]
        border_radius = "14px"
        shadow = "none"
    
    return f"""
        background: {bg};
        border: 1px solid {border};
        border-radius: {border_radius};
        padding: 8px 14px;
        color: {c["text_primary"]};
        font-size: 14px;
        font-family: 'Ubuntu', 'Inter', 'Outfit', 'Noto Sans', sans-serif;
        line-height: 1.4;
    """

def get_role_label_style(role: str, theme: str = "dark") -> str:
    """Стиль лейбла роли в сообщении"""
    c = COLORS[theme]
    
    colors = {
        "assistant": c["accent"],
        "user": c["text_secondary"],
        "system": c["accent_light"],
    }
    
    return f"""
        color: {colors.get(role, c["text_secondary"])};
        font-size: 11px;
        font-weight: 700;
        letter-spacing: 1.2px;
        text-transform: uppercase;
        padding: 0;
        margin: 0 0 4px 0;
        background: transparent;
        border: none;
        font-family: 'Montserrat', 'Outfit', 'Ubuntu Bold', 'Noto Sans', sans-serif;
    """

def get_status_label_style(state: str, theme: str = "dark") -> str:
    """Стиль лейбла статуса — с glow эффектом"""
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
        font-size: 14px;
        font-weight: 700;
        font-family: 'Montserrat', 'Outfit', 'Ubuntu Bold', 'Inter', sans-serif;
        letter-spacing: 0.8px;
        text-transform: uppercase;
    """

def get_typing_indicator_style(theme: str = "dark") -> str:
    """Стиль индикатора печати"""
    c = COLORS[theme]
    return f"""
        background: {c["bg_glass"]};
        border: 1px solid {c["border"]};
        border-radius: 16px;
        padding: 12px 16px;
    """

def get_avatar_style(theme: str = "dark") -> str:
    """Стиль аватара ассистента"""
    c = COLORS[theme]
    return f"""
        background: qlineargradient(
            spread:pad, x1:0, y1:0, x2:1, y2:1,
            stop:0 {c["aurora_1"]},
            stop:0.5 {c["aurora_2"]},
            stop:1 {c["aurora_3"]}
        );
        border: none;
        border-radius: 18px;
    """

def get_confirmation_style(theme: str = "dark") -> str:
    """Стиль диалога подтверждения"""
    c = COLORS[theme]
    return f"""
        QFrame#confirmationDialog {{
            background: rgba(239, 68, 68, 0.08);
            border: 1.5px solid rgba(239, 68, 68, 0.35);
            border-radius: 20px;
            padding: 20px;
        }}
    """

def get_model_badge_style(mode: str = "Auto", theme: str = "dark") -> str:
    """Стиль бейджа модели Gemini — Premium Borderless Glass Capsule"""
    c = COLORS[theme]
    # 2026 minimal style - no bright colors, just subtle glass
    
    return f"""
        QLabel {{
            background: rgba(255, 255, 255, 0.04);
            color: rgba(255, 255, 255, 0.85);
            border: 1px solid rgba(255, 255, 255, 0.08);
            border-radius: 10px;
            padding: 4px 12px;
            font-size: 11px;
            font-family: 'SF Pro Text', 'Montserrat', 'Outfit', sans-serif;
            font-weight: 600;
            letter-spacing: 0.3px;
        }}
        QLabel:hover {{
            background: rgba(255, 255, 255, 0.08);
            border-color: rgba(255, 255, 255, 0.12);
        }}
    """
