
import logging
from sentence_transformers import SentenceTransformer
import pickle

from src.config import settings

logger = logging.getLogger(__name__)

class Embeddings:

    def __init__(self):
        self.model = SentenceTransformer(settings.SENTENCE_TRANSFORMER_MODEL)
        self.storage_path = settings.EMBEDDING_STORAGE_PATH

    def get_file_path(self, file_name: str, document_id: str) -> str:
        """Get file path for the given file name and document id"""
        return f"{self.storage_path}/{file_name}_{document_id}.pkl"

    def _split_text(self, text: str) -> list[str]:
        """Split text into chunks"""
        splitted_text = text.split("\n")

        return [line for line in splitted_text if line.strip() != ""]
    

    def create_embedding(self, text: str) -> dict:
        """Create embedding for the given splitted text"""
        try:
            embeddings = []
            chunks = []
            for page in text:
                splitted_text = self._split_text(page["text"])
                page_embeddings = self.model.encode(splitted_text)
                embeddings.append(page_embeddings)
                chunks.append(splitted_text)

            return {
                "chunks": chunks,
                "embeddings": embeddings
            }
        except Exception as e:
            logger.error(f"An error occurred embedding document: {e}")


    def save_embedding(self, document):
        """"
        Save embedding
        """
        try:
            embedding = self.create_embedding(document["content"])
            document["embedding"] = embedding["embeddings"]
            document["chunks"] = embedding["chunks"]
            
            file_path = self.get_file_path(file_name=document["metadata"]["filename"], document_id=document["id"])
            with open(file_path, 'wb') as f:
                pickle.dump([document], f)
        except Exception as e:
            logger.error(f"could not save embedding: {e}")
            return
        
    def load_embedding(self) -> list[float]:
        """
        Load embedding
        """
        try:
            documents = self.load_pkl_files()
            return documents            
            # with open(self.storage_path, 'rb') as f:
            #     loaded_embedding = pickle.load(f)

            # return loaded_embedding

        except Exception as e:
            logger.warning(f"could not load embedding: {e}")
            return []
    
    def load_pkl_files(self) -> list[dict]:
        """Load all pickle files from the storage path"""
        import os
        documents = []
        try:
            for file_name in os.listdir(self.storage_path):
                if file_name.endswith(".pkl"):
                    file_path = os.path.join(self.storage_path, file_name)
                    with open(file_path, 'rb') as f:
                        loaded_data = pickle.load(f)
                        documents.extend(loaded_data)
            return documents
        except Exception as e:
            logger.error(f"Failed to load pickle files: {e}")
            return []