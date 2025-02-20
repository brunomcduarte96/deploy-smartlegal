from datetime import datetime
import locale

def data_por_extenso(data: datetime) -> str:
    """Converte data para formato por extenso"""
    locale.setlocale(locale.LC_TIME, 'pt_BR.UTF-8')
    return data.strftime("%d de %B de %Y").lower() 