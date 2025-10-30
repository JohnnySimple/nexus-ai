
import logging
from sentence_transformers import SentenceTransformer, CrossEncoder
import pickle
import torch

from src.config import settings
import src.helper_functions as helper_functions

from sqlalchemy.ext.asyncio import AsyncSession
from src.crud.document_crud import (create_document, create_document_with_pages_and_embeddings)
from src.db.models import Document, Page, ChunkEmbedding


logger = logging.getLogger(__name__)

class Embeddings:

    def __init__(self):
        self.device = "cuda" if torch.cuda.is_available() else "cpu"

        self.model = SentenceTransformer(settings.SENTENCE_TRANSFORMER_MODEL, self.device)
        self.storage_path = settings.EMBEDDING_STORAGE_PATH

    def get_file_path(self, file_name: str, document_id: str) -> str:
        """Get file path for the given file name and document id"""
        return f"{self.storage_path}/{file_name}_{document_id}.pkl"

    def _split_text(self, text: str) -> list[str]:
        """Split text into chunks"""
        splitted_text = text.split("\n")

        return [line for line in splitted_text if line.strip() != ""]
    

    def create_embedding(self, text: str) -> dict:
    # def create_embedding(self, document: list) -> dict:
        """Create embedding for the given splitted text"""
        try:
            embeddings = []
            chunks = []

            # data = helper_functions.create_content_page_chunks(text)

            # for page in data:
            #     page_embeddings = self.model.encode(page["sentences"])
            #     embeddings.append(page_embeddings)
            #     chunks.append(page["sentences"])

            # data = helper_functions.create_semantic_chunks(text)
            data = helper_functions.create_content_page_chunks_reload(text)

            for page in data:
                if not page.get("chunks"):
                    continue

                page_embeddings = self.model.encode(page["chunks"], convert_to_tensor=False)
                embeddings.append(page_embeddings)
                chunks.append(page["chunks"])

            # for page in document["content"]:
            #     page_chunks = helper_functions.create_semantic_chunks([page])
            #     print(f"page_chunks: {page_chunks}")
            #     page_embeddings = self.model.encode([page_chunks["text"] for chunk in page_chunks])
            #     page["chunks"] = page_chunks
            #     chunks.append(page_chunks)
            #     embeddings.append(page_embeddings)

            return {
                "chunks": chunks,
                "embeddings": embeddings
            }
        except Exception as e:
            logger.error(f"An error occurred embedding document: {e}")


    async def save_embedding(self, document, group_id: str):
        """"
        Save embedding
        """
        try:
            embedding = self.create_embedding(document["content"])
            # embedding = self.create_embedding(document)
            document["embedding"] = embedding["embeddings"]
            document["chunks"] = embedding["chunks"]

            # if specified persist the document in db
            if settings.USE_DB:
                from src.db.database import get_session
                
                async for session in get_session():
                    db_document = Document(
                        id=document["id"],
                        filename=document["metadata"]["filename"],
                        created_at=document["metadata"]["created_at"],
                        document_group_id=group_id
                    )

                    pages = []
                    for page_content, page_embeddings, chunk_list in zip(document["content"], document["embedding"], document["chunks"]):
                        single_page = Page(
                            page_number=page_content["page_number"],
                            text=page_content["text"],
                            sentence_count=len(self._split_text(page_content["text"]))
                            )

                        single_page_embeddings = []
                        for chunk_text, embedding_vector in zip(chunk_list, page_embeddings):
                            single_chunk_embedding = ChunkEmbedding(
                                chunk_text=chunk_text,
                                embedding=embedding_vector
                            )
                            single_page_embeddings.append(single_chunk_embedding)

                        pages.append({
                            "page": single_page,
                            "embeddings": single_page_embeddings
                            })

                    await create_document_with_pages_and_embeddings(session, db_document, pages)
            else:
                # else store as pickle file
                file_path = self.get_file_path(file_name=document["metadata"]["filename"], document_id=document["id"])
                with open(file_path, 'wb') as f:
                    pickle.dump([document], f)

        except Exception as e:
            logger.error(f"could not save embedding: {e}")
            raise e

    def save_all_embeddings(self, documents: list[dict]):
        """Save all embeddings"""
        try:
            for document in documents:
                self.save_embedding(document)
        except Exception as e:
            logger.error(f"could not save all embeddings: {e}")
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

    def delete_embedding(self, document_id: str) -> bool:
        """Delete embedding file for the given document id"""
        import os
        try:
            for file_name in os.listdir(self.storage_path):
                if file_name.endswith(f"_{document_id}.pkl"):
                    file_path = os.path.join(self.storage_path, file_name)
                    os.remove(file_path)
                    return True
            return False
        except Exception as e:
            logger.error(f"Failed to delete embedding: {e}")
            return False
    
    def similarity(self, vec1: list[float], vec2: list[float]) -> list[float]:
        """Get similiarity between two vectors"""
        return self.model.similarity(vec1, vec2)
    
    def get_top_similarities_from_page(self, query: str, page_texts_embeddings,
                                       page_split, top_k: int = 5, document_id: str = "", page_number: int = 0) -> list[tuple]:
        """Get answer to the query from the page texts embeddings"""
        question_embedding = self.model.encode(query)
        similarities = self.similarity(page_texts_embeddings, question_embedding)

        sorted_similarities, indices = torch.sort(similarities, dim=0, descending=True)
        top_similarities = sorted_similarities[:top_k]
        top_indices = indices[:top_k]
        top_values = similarities[top_indices]

        top_similarities_answers = [page_split[i] if i < len(page_split) else None
                                    for i in top_indices]

        results =  [(ans, round(float(val), 4), document_id, page_number) for ans, val
                    in zip(top_similarities_answers, top_values)]
        return results

    def search_with_documents(self, query: str, documents: list, top_k: int = 5) -> list[dict]:
        """Search for similar chunks in all specified documents"""
        potential_answers = []

        if settings.RERANK_TOP_K:
            top_k = top_k * 2

        for doc in documents:

            print(f"keys: {list(doc.keys())}")
            print(f"doc: {doc['content'][0]['embedding']}")

            similar_chunks = []
            
            # for page_index, page_embedding in enumerate(doc["embedding"]):
            for page in doc["content"]:
                similarity = self.get_top_similarities_from_page(query, page["embedding"], page["chunks"], top_k,
                                                                    document_id=doc["id"], page_number=page["page_number"])
                
                if settings.RERANK_TOP_K:
                    similarity = self.rerank(query, similarity, top_k/2)

                similar_chunks.append(similarity)
            
            potential_answers.append({
                "document": {
                    "id": doc["id"],
                    "filename": doc["metadata"]["filename"],
                    "metadata": doc["metadata"]
                },
                "relevant_chunks": similar_chunks
            })

        return potential_answers
        
    
    def search(self, query: str, top_k: int = 5, document_ids: list[str] = []) -> list[dict]:
        """Search for similar chunks in all specified documents"""
        loaded_embeddings = self.load_embedding()

        potential_answers = []

        if settings.RERANK_TOP_K:
            top_k = top_k * 2

        for doc in loaded_embeddings:
            if doc["id"] in document_ids:

                similar_chunks = []
                
                for page_index, page_embedding in enumerate(doc["embedding"]):
                    similarity = self.get_top_similarities_from_page(query, page_embedding, doc["chunks"][page_index], top_k,
                                                                     document_id=doc["id"], page_number=page_index)
                    
                    if settings.RERANK_TOP_K:
                        similarity = self.rerank(query, similarity, top_k/2)

                    similar_chunks.append(similarity)
                
                potential_answers.append({
                    "document": {
                        "id": doc["id"],
                        "filename": doc["metadata"]["filename"],
                        "metadata": doc["metadata"]
                    },
                    "relevant_chunks": similar_chunks
                })

        return potential_answers
    
    def rerank(self, query: str, similarity, top_k) -> list[dict]:
        """Rerank the top similar chunks using a cross-encoder model"""
        reranker = CrossEncoder(settings.CROSS_ENCODER_MODEL)

        pairs = [(query, chunk[0]) for chunk in similarity if chunk[0] is not None]
        scores = reranker.predict(pairs).tolist()

        for index, chunk in enumerate(similarity):
            chunk = list(chunk)
            chunk.append(scores[index])
            similarity[index] = tuple(chunk)

        reranked = sorted(similarity, key=lambda x: x[4], reverse=True)[:int(top_k)]  # x[4] is the new score

        return reranked
