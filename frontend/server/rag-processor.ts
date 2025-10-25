import { db } from "./db";
import { documentChunks, querySessions, documents } from "@shared/schema";
import { sql, inArray, eq, and } from "drizzle-orm";

// Calculate cosine similarity between two vectors
function cosineSimilarity(a: number[], b: number[]): number {
  if (a.length !== b.length) return 0;
  
  let dotProduct = 0;
  let normA = 0;
  let normB = 0;
  
  for (let i = 0; i < a.length; i++) {
    dotProduct += a[i] * b[i];
    normA += a[i] * a[i];
    normB += b[i] * b[i];
  }
  
  if (normA === 0 || normB === 0) return 0;
  
  return dotProduct / (Math.sqrt(normA) * Math.sqrt(normB));
}

// Generate embedding for query (simulated)
function generateQueryEmbedding(query: string): number[] {
  const embedding: number[] = [];
  for (let i = 0; i < 1536; i++) {
    embedding.push(Math.random() * 2 - 1);
  }
  return embedding;
}

// Retrieve relevant chunks using vector similarity
async function retrieveRelevantChunks(
  queryEmbedding: number[], 
  topK: number,
  documentIds?: string[],
  groupIds?: string[]
): Promise<Array<{ text: string; similarity: number; metadata: string | null }>> {
  const hasDocumentFilter = documentIds && documentIds.length > 0;
  const hasGroupFilter = groupIds && groupIds.length > 0;
  
  // If both filters are provided, we need OR logic (union)
  if (hasDocumentFilter && hasGroupFilter) {
    // Get document IDs from selected groups
    const docsInGroups = await db
      .select({ id: documents.id })
      .from(documents)
      .where(inArray(documents.groupId, groupIds));
    
    const groupDocumentIds = docsInGroups.map(d => d.id);
    
    // Combine document IDs (union of explicitly selected docs + docs from selected groups)
    const allDocumentIds = Array.from(new Set([...documentIds, ...groupDocumentIds]));
    
    // Fetch chunks from combined document IDs
    const chunks = await db
      .select()
      .from(documentChunks)
      .where(
        and(
          sql`${documentChunks.embedding} IS NOT NULL`,
          inArray(documentChunks.documentId, allDocumentIds)
        )
      );
    
    // Calculate similarity scores
    const scoredChunks = chunks.map((chunk) => {
      const chunkEmbedding = JSON.parse(chunk.embedding || "[]");
      const similarity = cosineSimilarity(queryEmbedding, chunkEmbedding);
      
      return {
        text: chunk.text,
        similarity,
        metadata: chunk.metadata,
      };
    });
    
    // Sort by similarity and return top K
    return scoredChunks
      .sort((a, b) => b.similarity - a.similarity)
      .slice(0, topK);
  }
  
  // If only group filter is provided
  if (hasGroupFilter) {
    const chunks = await db
      .select({
        id: documentChunks.id,
        documentId: documentChunks.documentId,
        text: documentChunks.text,
        chunkIndex: documentChunks.chunkIndex,
        embedding: documentChunks.embedding,
        metadata: documentChunks.metadata,
        createdAt: documentChunks.createdAt,
      })
      .from(documentChunks)
      .innerJoin(documents, eq(documentChunks.documentId, documents.id))
      .where(
        and(
          sql`${documentChunks.embedding} IS NOT NULL`,
          inArray(documents.groupId, groupIds)
        )
      );
    
    // Calculate similarity scores
    const scoredChunks = chunks.map((chunk) => {
      const chunkEmbedding = JSON.parse(chunk.embedding || "[]");
      const similarity = cosineSimilarity(queryEmbedding, chunkEmbedding);
      
      return {
        text: chunk.text,
        similarity,
        metadata: chunk.metadata,
      };
    });
    
    // Sort by similarity and return top K
    return scoredChunks
      .sort((a, b) => b.similarity - a.similarity)
      .slice(0, topK);
  }
  
  // If only document filter is provided or no filters at all
  const conditions = [sql`${documentChunks.embedding} IS NOT NULL`];
  
  if (hasDocumentFilter) {
    conditions.push(inArray(documentChunks.documentId, documentIds));
  }
  
  const chunks = await db
    .select()
    .from(documentChunks)
    .where(and(...conditions));
  
  // Calculate similarity scores
  const scoredChunks = chunks.map((chunk) => {
    const chunkEmbedding = JSON.parse(chunk.embedding || "[]");
    const similarity = cosineSimilarity(queryEmbedding, chunkEmbedding);
    
    return {
      text: chunk.text,
      similarity,
      metadata: chunk.metadata,
    };
  });
  
  // Sort by similarity and return top K
  return scoredChunks
    .sort((a, b) => b.similarity - a.similarity)
    .slice(0, topK);
}

// Generate response using retrieved context (simulated LLM call)
function generateResponse(query: string, context: string[], model: string, temperature: number): string {
  const contextSummary = context.length > 0 
    ? `Based on ${context.length} relevant document chunks, `
    : "Without specific context, ";
  
  const responses = [
    `${contextSummary}I can provide you with information about ${query.toLowerCase()}. The documents suggest that this is an important topic with several key aspects to consider.`,
    `${contextSummary}here's what I found regarding ${query.toLowerCase()}: The available information indicates several relevant points that address your question.`,
    `${contextSummary}to answer your query about ${query.toLowerCase()}, the system has identified pertinent information from the knowledge base that provides insights into this matter.`,
  ];
  
  const selectedResponse = responses[Math.floor(Math.random() * responses.length)];
  
  // Add temperature-based randomization hint
  const temperatureNote = temperature > 1.0 
    ? " [Note: High temperature setting provides more creative responses]"
    : temperature < 0.3
    ? " [Note: Low temperature setting provides more focused responses]"
    : "";
  
  return selectedResponse + temperatureNote;
}

export interface RAGQueryOptions {
  query: string;
  model: string;
  topK: number;
  temperature: number;
  chunkSize: number;
  chunkOverlap: number;
  documentIds?: string[];
  groupIds?: string[];
}

export async function processRAGQuery(options: RAGQueryOptions) {
  const startTime = Date.now();
  const { query, model, topK, temperature, chunkSize, chunkOverlap, documentIds, groupIds } = options;
  
  // 1. Generate query embedding
  const queryEmbedding = generateQueryEmbedding(query);
  
  // 2. Retrieve relevant chunks (with optional filters)
  const relevantChunks = await retrieveRelevantChunks(queryEmbedding, topK, documentIds, groupIds);
  
  // 3. Extract context text
  const contextTexts = relevantChunks.map(chunk => chunk.text);
  
  // 4. Generate response
  const response = generateResponse(query, contextTexts, model, temperature);
  
  // 5. Calculate response time
  const responseTime = Date.now() - startTime;
  
  // 6. Format retrieved chunks for display
  const retrievedChunks = relevantChunks.map((chunk, idx) => {
    const metadata = chunk.metadata ? JSON.parse(chunk.metadata) : {};
    return `[Chunk ${idx + 1}] (Similarity: ${(chunk.similarity * 100).toFixed(1)}%) from ${metadata.filename || 'unknown'}: ${chunk.text.substring(0, 200)}${chunk.text.length > 200 ? '...' : ''}`;
  });
  
  // If no chunks found, provide fallback
  if (retrievedChunks.length === 0) {
    retrievedChunks.push("No relevant document chunks found in the knowledge base. Upload documents to enable context-based responses.");
  }
  
  return {
    response,
    retrievedChunks,
    responseTime,
  };
}
