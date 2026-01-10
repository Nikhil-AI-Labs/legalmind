"""
Legal Contract RAG Ingestion Pipeline
======================================
Streamlined version - Creates vector DB and chunks only
"""

import pymupdf as fitz
import pytesseract
from PIL import Image
from io import BytesIO
import os
import json
import platform
import re
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Tuple
from dataclasses import dataclass

from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEndpointEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document
from dotenv import load_dotenv
from tqdm import tqdm

load_dotenv()


# ============================================================================
# CONFIGURATION
# ============================================================================

@dataclass
class PipelineConfig:
    """Minimal configuration for RAG pipeline"""
    
    # Only essential directories
    vector_db_dir: str = "vector_db"
    raw_chunks_dir: str = "rag_storage/raw_chunks"
    
    # OCR Settings
    ocr_dpi: int = 300
    
    # Chunking Strategy
    chunk_size: int = 1000
    chunk_overlap: int = 200
    chunk_separators: List[str] = None
    
    # Embeddings
    embedding_model: str = "google/embeddinggemma-300m"
    embedding_task: str = "feature-extraction"
    
    def __post_init__(self):
        """Initialize separators and create only necessary directories"""
        if self.chunk_separators is None:
            self.chunk_separators = ["\n\n\n", "\n\n", "\n", ". ", "; ", ", ", " ", ""]
        
        # Create only essential directories
        os.makedirs(self.vector_db_dir, exist_ok=True)
        os.makedirs(self.raw_chunks_dir, exist_ok=True)


# ============================================================================
# TESSERACT SETUP
# ============================================================================

def setup_tesseract():
    """Auto-configure Tesseract OCR path"""
    if platform.system() == 'Windows':
        paths = [
            r'C:\Program Files\Tesseract-OCR\tesseract.exe',
            r'C:\Program Files (x86)\Tesseract-OCR\tesseract.exe',
        ]
        for path in paths:
            if os.path.exists(path):
                pytesseract.pytesseract.tesseract_cmd = path
                return


# ============================================================================
# PDF EXTRACTION
# ============================================================================

class PDFExtractor:
    """Hybrid PDF text extraction with OCR fallback"""
    
    def __init__(self, config: PipelineConfig):
        self.config = config
        setup_tesseract()
    
    def extract_text(self, pdf_path: str) -> Tuple[str, int]:
        """Extract text from PDF, return (text, page_count)"""
        print(f"\n{'='*70}")
        print("STAGE 1: PDF TEXT EXTRACTION")
        print(f"{'='*70}\n")
        
        doc = fitz.open(pdf_path)
        total_pages = len(doc)
        
        all_text = []
        
        for page_num in tqdm(range(total_pages), desc="Extracting pages"):
            page = doc[page_num]
            text = page.get_text("text")
            
            # OCR fallback for scanned pages
            if len(text.strip()) < 50:
                try:
                    pix = page.get_pixmap(dpi=self.config.ocr_dpi)
                    img = Image.open(BytesIO(pix.tobytes("png")))
                    text = pytesseract.image_to_string(img)
                except:
                    pass
            
            all_text.append(text)
        
        doc.close()
        
        full_text = "\n\n".join(all_text)
        print(f"✓ Extracted {len(full_text):,} chars from {total_pages} pages\n")
        
        return full_text, total_pages


# ============================================================================
# TEXT CLEANING
# ============================================================================

class TextCleaner:
    """Minimal text cleaning"""
    
    @staticmethod
    def clean(text: str) -> str:
        """Clean OCR artifacts"""
        # Normalize whitespace
        text = re.sub(r' +', ' ', text)
        text = re.sub(r'\n{4,}', '\n\n\n', text)
        
        # Remove non-printable
        text = ''.join(c for c in text if c.isprintable() or c in '\n\t')
        
        # Fix broken hyphens
        text = re.sub(r'(\w+)-\s+(\w+)', r'\1-\2', text)
        
        return text.strip()


# ============================================================================
# CHUNKING
# ============================================================================

class LegalDocumentChunker:
    """Chunk documents for legal text"""
    
    def __init__(self, config: PipelineConfig):
        self.config = config
        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size=config.chunk_size,
            chunk_overlap=config.chunk_overlap,
            separators=config.chunk_separators,
            length_function=len
        )
        
        print(f"{'='*70}")
        print("STAGE 2: CHUNKING")
        print(f"{'='*70}")
        print(f"Chunk size: {config.chunk_size} | Overlap: {config.chunk_overlap}\n")
    
    def chunk_document(self, text: str, filename: str) -> List[Document]:
        """Split text into chunks"""
        chunks = self.splitter.create_documents([text])
        
        # Add minimal metadata
        for i, doc in enumerate(chunks):
            doc.metadata = {
                'chunk_id': i,
                'source': filename,
                'timestamp': datetime.now().isoformat()
            }
        
        print(f"✓ Created {len(chunks)} chunks\n")
        return chunks


# ============================================================================
# EMBEDDINGS
# ============================================================================

class EmbeddingGenerator:
    """Generate embeddings using google/embeddinggemma-300m"""
    
    def __init__(self, config: PipelineConfig):
        self.config = config
        
        print(f"{'='*70}")
        print("STAGE 3: EMBEDDING MODEL")
        print(f"{'='*70}\n")
        
        hf_token = os.getenv("HF_TOKEN") or os.getenv("HUGGINGFACE_API_TOKEN")
        if not hf_token:
            raise ValueError("HF_TOKEN not found in .env file!")
        
        self.embeddings = HuggingFaceEndpointEmbeddings(
            repo_id=config.embedding_model,
            task=config.embedding_task,
            huggingfacehub_api_token=hf_token
        )
        
        print("✓ Embedding model loaded\n")
    
    def get_embeddings_model(self):
        return self.embeddings


# ============================================================================
# VECTOR STORE
# ============================================================================

class VectorStoreManager:
    """Create and save FAISS vector store"""
    
    def __init__(self, config: PipelineConfig):
        self.config = config
    
    def create_and_save(self, documents: List[Document], embeddings, doc_name: str) -> str:
        """Create FAISS index and save"""
        print(f"{'='*70}")
        print("STAGE 4: VECTOR STORE")
        print(f"{'='*70}")
        print(f"Creating FAISS index for {len(documents)} chunks...\n")
        
        # Create vector store
        vector_store = FAISS.from_documents(
            documents=documents,
            embedding=embeddings
        )
        
        # Save to disk
        save_path = os.path.join(self.config.vector_db_dir, f"{doc_name}_faiss_index")
        vector_store.save_local(save_path)
        
        print(f"✓ Vector store saved: {save_path}\n")
        return save_path


# ============================================================================
# MAIN PIPELINE
# ============================================================================

class IngestionPipeline:
    """Streamlined RAG ingestion pipeline"""
    
    def __init__(self, config: PipelineConfig = None):
        self.config = config or PipelineConfig()
        
        self.pdf_extractor = PDFExtractor(self.config)
        self.text_cleaner = TextCleaner()
        self.chunker = LegalDocumentChunker(self.config)
        self.embedding_generator = EmbeddingGenerator(self.config)
        self.vector_store_manager = VectorStoreManager(self.config)
    
    def ingest_document(self, pdf_path: str) -> Dict:
        """Process PDF: extract → clean → chunk → embed → save"""
        print(f"\n{'#'*70}")
        print("LEGAL CONTRACT RAG INGESTION")
        print(f"{'#'*70}\n")
        
        doc_name = Path(pdf_path).stem
        
        # Extract text
        raw_text, total_pages = self.pdf_extractor.extract_text(pdf_path)
        
        # Clean text (in-place, no extra storage)
        cleaned_text = self.text_cleaner.clean(raw_text)
        del raw_text  # Free memory
        
        # Chunk text
        documents = self.chunker.chunk_document(cleaned_text, Path(pdf_path).name)
        del cleaned_text  # Free memory
        
        # Get embeddings
        embeddings = self.embedding_generator.get_embeddings_model()
        
        # Create and save vector store
        vector_db_path = self.vector_store_manager.create_and_save(
            documents, embeddings, doc_name
        )
        
        # Save raw chunks (for risk detection)
        chunks_data = [
            {
                'chunk_id': doc.metadata['chunk_id'],
                'text': doc.page_content
            }
            for doc in documents
        ]
        
        chunks_path = os.path.join(
            self.config.raw_chunks_dir,
            f"{doc_name}_chunks.json"
        )
        
        with open(chunks_path, 'w', encoding='utf-8') as f:
            json.dump(chunks_data, f, indent=2, ensure_ascii=False)
        
        # Summary
        print(f"{'='*70}")
        print("✅ INGESTION COMPLETE")
        print(f"{'='*70}")
        print(f"Vector DB: {vector_db_path}")
        print(f"Chunks: {chunks_path}")
        print(f"Total: {len(documents)} chunks\n")
        
        return {
            'vector_db_path': vector_db_path,
            'chunks_path': chunks_path,
            'total_chunks': len(documents)
        }


# ============================================================================
# USAGE
# ============================================================================

if __name__ == "__main__":
    config = PipelineConfig(
        chunk_size=1000,
        chunk_overlap=200,
        embedding_model="google/embeddinggemma-300m"
    )
    
    pipeline = IngestionPipeline(config)
    
    pdf_path = r"C:\Users\Nikhil Pathak\Downloads\CUAD_v1\CUAD_v1\full_contract_pdf\Part_II\Service\BLACKSTONEGSOLONG-SHORTCREDITINCOMEFUND_05_11_2020-EX-99.(K)(1)-SERVICE AGREEMENT.PDF"
    
    try:
        result = pipeline.ingest_document(pdf_path)
        print(f"✅ SUCCESS!")
        print(f"   Chunks: {result['total_chunks']}")
        print(f"   Ready for risk detection!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
