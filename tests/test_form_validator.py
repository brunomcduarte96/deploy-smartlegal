import pytest
from utils.form_validator import FormValidator

def test_email_validation():
    assert FormValidator.validate_email("test@example.com") == True
    assert FormValidator.validate_email("invalid.email") == False

def test_cpf_validation():
    assert FormValidator.validate_cpf("123.456.789-00") == True
    assert FormValidator.validate_cpf("123") == False

def test_phone_validation():
    assert FormValidator.validate_phone("(11) 98765-4321") == True
    assert FormValidator.validate_phone("1234-5678") == False 