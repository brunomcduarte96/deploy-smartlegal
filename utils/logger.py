import logging
import os
from datetime import datetime

def setup_logger():
    """Configura o sistema de logging"""
    # Criar diretório de logs se não existir
    log_dir = 'logs'
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    
    # Nome do arquivo de log com data
    log_file = f"logs/smartlegal_{datetime.now().strftime('%Y%m%d')}.log"
    
    # Configuração do logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()
        ]
    )
    
    return logging.getLogger('smartlegal') 