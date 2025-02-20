from typing import Dict, Any
import re

class FormValidator:
    @staticmethod
    def validate_email(email: str) -> bool:
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(pattern, email))
    
    @staticmethod
    def validate_cpf(cpf: str) -> bool:
        # Implementar validação real de CPF
        return len(cpf.replace('.','').replace('-','')) == 11
    
    @staticmethod
    def validate_phone(phone: str) -> bool:
        # Validar formato (XX) XXXXX-XXXX
        pattern = r'^\([0-9]{2}\) [0-9]{5}-[0-9]{4}$'
        return bool(re.match(pattern, phone))
    
    @staticmethod
    def validate_onboarding_form(data: Dict[str, Any]) -> Dict[str, str]:
        errors = {}
        
        if not data.get('nome_completo'):
            errors['nome_completo'] = 'Nome é obrigatório'
            
        if not FormValidator.validate_email(data.get('email', '')):
            errors['email'] = 'Email inválido'
            
        if not FormValidator.validate_cpf(data.get('cpf', '')):
            errors['cpf'] = 'CPF inválido'
            
        if not FormValidator.validate_phone(data.get('celular', '')):
            errors['celular'] = 'Celular inválido'
            
        return errors 