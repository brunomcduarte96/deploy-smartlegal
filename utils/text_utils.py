def format_title_case(text: str) -> str:
    """Formata texto com primeiras letras maiúsculas"""
    if not text:
        return text
    return ' '.join(word.capitalize() for word in text.strip().split()) 