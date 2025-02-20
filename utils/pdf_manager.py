import os
from typing import Union, List
from PyPDF2 import PdfReader, PdfWriter
from pdf2image import convert_from_bytes
import io
from docx import Document
from PIL import Image
import logging

logger = logging.getLogger(__name__)

class PDFManager:
    @staticmethod
    def check_pdf(file_content: bytes) -> bool:
        """Verifica se o arquivo é um PDF válido"""
        try:
            PdfReader(io.BytesIO(file_content))
            return True
        except:
            return False

    @staticmethod
    def convert_to_pdf(file_content: bytes, file_type: str) -> bytes:
        """Converte diferentes tipos de arquivo para PDF"""
        try:
            if file_type.lower() in ['jpg', 'jpeg', 'png']:
                return PDFManager._convert_image_to_pdf(file_content)
            elif file_type == 'docx':
                return PDFManager._convert_docx_to_pdf(file_content)
            else:
                raise ValueError(f"Formato não suportado: {file_type}")
        except Exception as e:
            raise Exception(f"Erro na conversão para PDF: {str(e)}")

    @staticmethod
    def _convert_docx_to_pdf(docx_content: bytes) -> bytes:
        """Converte arquivo DOCX para PDF"""
        try:
            # Salva o conteúdo do DOCX em um arquivo temporário
            doc = Document(io.BytesIO(docx_content))
            temp_docx = io.BytesIO()
            doc.save(temp_docx)
            temp_docx.seek(0)
            
            # TODO: Implementar conversão DOCX para PDF
            # Nota: Esta é uma implementação simplificada
            # Para uma solução completa, considere usar libraries como docx2pdf
            # ou uma API de conversão
            
            raise NotImplementedError("Conversão DOCX para PDF ainda não implementada")
        except Exception as e:
            raise Exception(f"Erro na conversão DOCX para PDF: {str(e)}")

    @staticmethod
    def _convert_image_to_pdf(image_content: bytes) -> bytes:
        """Converte imagem para PDF usando PIL"""
        try:
            # Abrir imagem usando PIL
            image = Image.open(io.BytesIO(image_content))
            
            # Converter para RGB se necessário
            if image.mode != 'RGB':
                image = image.convert('RGB')
            
            # Criar buffer para PDF
            pdf_buffer = io.BytesIO()
            
            # Salvar como PDF
            image.save(pdf_buffer, format='PDF', resolution=100.0)
            
            # Retornar conteúdo do PDF
            pdf_buffer.seek(0)
            return pdf_buffer.getvalue()
            
        except Exception as e:
            logger.error(f"Erro ao converter imagem para PDF: {str(e)}")
            raise Exception(f"Erro ao converter imagem para PDF: {str(e)}")

    @staticmethod
    def merge_pdfs(pdf_contents: List[bytes]) -> bytes:
        """Combina múltiplos PDFs em um único arquivo"""
        try:
            output = io.BytesIO()
            pdf_writer = PdfWriter()
            
            for pdf_content in pdf_contents:
                pdf_reader = PdfReader(io.BytesIO(pdf_content))
                for page in pdf_reader.pages:
                    pdf_writer.add_page(page)
            
            pdf_writer.write(output)
            return output.getvalue()
        except Exception as e:
            raise Exception(f"Erro ao combinar PDFs: {str(e)}") 