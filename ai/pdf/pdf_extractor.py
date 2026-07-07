"""PDF text extraction service."""

import logging
import tempfile
from pathlib import Path
from typing import Optional

log = logging.getLogger(__name__)


class PDFExtractor:
    """Extrait le texte d'un fichier PDF."""
    
    @staticmethod
    async def extract_text(file_content: bytes, filename: str) -> str:
        """
        Extrait le texte d'un PDF.
        
        Args:
            file_content: Contenu binaire du fichier
            filename: Nom du fichier (pour logs)
        
        Returns:
            Texte extrait du PDF
        """
        try:
            import pdfplumber
            
            log.info(f"Extraction du PDF: {filename} ({len(file_content)} bytes)")
            
            # Écrire le contenu dans un fichier temporaire
            with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp:
                tmp.write(file_content)
                tmp_path = tmp.name
            
            try:
                # Extraire le texte
                text_parts = []
                with pdfplumber.open(tmp_path) as pdf:
                    total_pages = len(pdf.pages)
                    log.info(f"PDF contient {total_pages} pages")
                    
                    for i, page in enumerate(pdf.pages):
                        page_text = page.extract_text()
                        if page_text:
                            text_parts.append(page_text)
                        log.debug(f"Page {i+1}: {len(page_text or '')} caractères")
                
                full_text = "\n\n".join(text_parts)
                
                # Nettoyer le texte
                full_text = PDFExtractor._clean_text(full_text)
                
                log.info(f"✅ Texte extrait: {len(full_text)} caractères")
                
                if len(full_text) < 50:
                    log.warning("⚠️ Texte très court, PDF peut contenir des images")
                    return f"[PDF avec peu de texte extractible] {full_text}"
                
                return full_text
                
            finally:
                # Supprimer le fichier temporaire
                Path(tmp_path).unlink(missing_ok=True)
                
        except ImportError:
            log.error("❌ pdfplumber non installé. Exécutez: pip install pdfplumber")
            raise ValueError("Service d'extraction PDF non disponible")
        except Exception as e:
            log.error(f"❌ Erreur extraction PDF: {e}", exc_info=True)
            raise ValueError(f"Impossible d'extraire le texte du PDF: {str(e)}")
    
    @staticmethod
    def _clean_text(text: str) -> str:
        """Nettoie le texte extrait."""
        if not text:
            return ""
        
        # Normaliser les espaces et sauts de ligne
        lines = text.split('\n')
        cleaned_lines = []
        
        for line in lines:
            line = line.strip()
            if line:
                cleaned_lines.append(line)
        
        # Joindre avec des espaces
        text = ' '.join(cleaned_lines)
        
        # Supprimer les espaces multiples
        import re
        text = re.sub(r'\s+', ' ', text)
        
        # Supprimer les caractères bizarres
        text = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', '', text)
        
        return text.strip()
    
    @staticmethod
    def validate_file(filename: str, content_type: str, size: int) -> Optional[str]:
        """
        Valide le fichier uploadé.
        
        Returns:
            None si valide, message d'erreur sinon
        """
        # Vérifier l'extension
        if not filename.lower().endswith('.pdf'):
            return "Seuls les fichiers PDF sont acceptés"
        
        # Vérifier le type MIME
        if content_type not in ['application/pdf', 'application/x-pdf']:
            return "Type de fichier invalide"
        
        # Vérifier la taille (max 10 MB)
        max_size = 10 * 1024 * 1024  # 10 MB
        if size > max_size:
            return f"Fichier trop volumineux (max 10 MB, reçu {size / 1024 / 1024:.1f} MB)"
        
        if size < 100:
            return "Fichier trop petit"
        
        return None
