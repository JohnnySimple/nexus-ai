import { db } from "./db";
import { documents, documentChunks } from "@shared/schema";
import { eq } from "drizzle-orm";

// Simulated text extraction for different file types
function extractText(buffer: Buffer, mimeType: string): string {
  // In a real implementation, you would use libraries like:
  // - pdf-parse for PDFs
  // - mammoth for DOCX
  // For now, we'll just convert buffer to string for text files
  
  if (mimeType === "text/plain" || mimeType === "text/markdown") {
    return buffer.toString("utf-8");
  }
  
  if (mimeType === "application/pdf") {
    // Simulated PDF text extraction
    return `[Extracted PDF text]\n${buffer.toString("utf-8").slice(0, 1000)}...`;
  }
  
  return buffer.toString("utf-8");
}

// Chunk text into smaller pieces with overlap
function chunkText(text: string, chunkSize: number, overlap: number): string[] {
  const chunks: string[] = [];
  
  // Handle edge cases
  if (text.length === 0) return chunks;
  if (text.length <= chunkSize) {
    chunks.push(text);
    return chunks;
  }
  
  let start = 0;
  
  while (start < text.length) {
    const end = Math.min(start + chunkSize, text.length);
    chunks.push(text.slice(start, end));
    
    // Move to next chunk, ensuring we always advance
    if (end === text.length) break;
    start = end - overlap;
    
    // Ensure we always make progress
    if (start < 0 || overlap >= chunkSize) {
      start = end;
    }
  }
  
  return chunks;
}

// Simulated embedding generation (in real app, call OpenAI/Cohere API)
function generateEmbedding(text: string): number[] {
  // Simulated 1536-dimensional embedding (OpenAI ada-002 size)
  const embedding: number[] = [];
  for (let i = 0; i < 1536; i++) {
    embedding.push(Math.random() * 2 - 1);
  }
  return embedding;
}

export interface ProcessDocumentOptions {
  documentId: string;
  buffer: Buffer;
  filename: string;
  mimeType: string;
  chunkSize?: number;
  chunkOverlap?: number;
}

export async function processDocument(options: ProcessDocumentOptions): Promise<void> {
  const {
    documentId,
    buffer,
    filename,
    mimeType,
    chunkSize = 512,
    chunkOverlap = 50,
  } = options;

  try {
    // 1. Extract text from document
    const text = extractText(buffer, mimeType);
    
    // 2. Chunk the text
    const chunks = chunkText(text, chunkSize, chunkOverlap);
    
    // 3. Generate embeddings and store chunks
    const chunkPromises = chunks.map(async (chunkText, index) => {
      const embedding = generateEmbedding(chunkText);
      
      await db.insert(documentChunks).values({
        documentId,
        text: chunkText,
        chunkIndex: index,
        embedding: JSON.stringify(embedding),
        metadata: JSON.stringify({
          filename,
          mimeType,
          chunkSize,
          chunkOverlap,
        }),
      });
    });
    
    await Promise.all(chunkPromises);
    
    // 4. Update document status and chunk count
    await db
      .update(documents)
      .set({
        status: "completed",
        chunkCount: chunks.length,
      })
      .where(eq(documents.id, documentId));
      
  } catch (error) {
    // Update document status to failed
    await db
      .update(documents)
      .set({
        status: "failed",
      })
      .where(eq(documents.id, documentId));
    
    throw error;
  }
}

export async function getDocumentChunks(documentId: string) {
  return await db
    .select()
    .from(documentChunks)
    .where(eq(documentChunks.documentId, documentId))
    .orderBy(documentChunks.chunkIndex);
}

export async function reEmbedDocument(documentId: string): Promise<void> {
  // Get all chunks for the document
  const chunks = await getDocumentChunks(documentId);
  
  // Regenerate embeddings for each chunk
  const updatePromises = chunks.map(async (chunk) => {
    const newEmbedding = generateEmbedding(chunk.text);
    
    await db
      .update(documentChunks)
      .set({
        embedding: JSON.stringify(newEmbedding),
      })
      .where(eq(documentChunks.id, chunk.id));
  });
  
  await Promise.all(updatePromises);
}
