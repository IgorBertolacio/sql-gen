"""
Serviço para carregamento de índices FAISS.
"""

import os
import faiss
import pickle
from typing import Dict, Any, Tuple

class IndexLoader:
    """
    Serviço para carregamento de índices FAISS e metadados associados.
    Responsável por carregar e fornecer acesso aos índices vetoriais e seus metadados.
    """
    
    # Caminho para os arquivos FAISS e PKL
    FAISS_INDEX_PATH = os.path.join("vdb", "models_text-embedding-004", "schema_element_index_norm.index")
    METADATA_PATH = os.path.join("vdb", "models_text-embedding-004", "schema_element_metadata_norm.pkl")
    
    @staticmethod
    def load_index() -> Tuple[Any, Dict]:
        """
        Carrega o índice FAISS e os metadados.
        
        Returns:
            Tuple contendo o índice FAISS e os metadados.
        """
        # Carrega o índice FAISS
        index = faiss.read_index(IndexLoader.FAISS_INDEX_PATH)
        
        # Carrega os metadados
        with open(IndexLoader.METADATA_PATH, 'rb') as f:
            metadata = pickle.load(f)
        
        return index, metadata
