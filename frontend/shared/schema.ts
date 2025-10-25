import { sql, relations } from "drizzle-orm";
import { pgTable, text, varchar, integer, timestamp, real, boolean } from "drizzle-orm/pg-core";
import { createInsertSchema } from "drizzle-zod";
import { z } from "zod";

// Users Schema (must be first for foreign key references)
export const users = pgTable("users", {
  id: varchar("id").primaryKey().default(sql`gen_random_uuid()`),
  email: text("email").notNull().unique(),
  passwordHash: text("password_hash").notNull(),
  name: text("name").notNull(),
  role: text("role").notNull().default("user"), // "admin" or "user"
  createdAt: timestamp("created_at").notNull().defaultNow(),
  lastLogin: timestamp("last_login"),
});

export const insertUserSchema = createInsertSchema(users).omit({
  id: true,
  createdAt: true,
  lastLogin: true,
});

export type InsertUser = z.infer<typeof insertUserSchema>;
export type User = typeof users.$inferSelect;

// Auth schemas
export const loginSchema = z.object({
  email: z.string().email("Invalid email address"),
  password: z.string().min(6, "Password must be at least 6 characters"),
});

export const registerSchema = z.object({
  email: z.string().email("Invalid email address"),
  password: z.string().min(6, "Password must be at least 6 characters"),
  confirmPassword: z.string(),
  name: z.string().min(1, "Name is required"),
}).refine((data) => data.password === data.confirmPassword, {
  message: "Passwords do not match",
  path: ["confirmPassword"],
});

export type LoginFormData = z.infer<typeof loginSchema>;
export type RegisterFormData = z.infer<typeof registerSchema>;

// Admin user management schemas
export const adminCreateUserSchema = z.object({
  email: z.string().email("Invalid email address"),
  password: z.string().min(6, "Password must be at least 6 characters"),
  name: z.string().min(1, "Name is required"),
  role: z.enum(["admin", "user"]).default("user"),
});

export const adminUpdateUserSchema = z.object({
  email: z.string().email("Invalid email address").optional(),
  name: z.string().min(1, "Name is required").optional(),
  role: z.enum(["admin", "user"]).optional(),
  password: z.string().min(6, "Password must be at least 6 characters").optional(),
});

export type AdminCreateUser = z.infer<typeof adminCreateUserSchema>;
export type AdminUpdateUser = z.infer<typeof adminUpdateUserSchema>;

// User metrics type
export type UserMetrics = {
  userId: string;
  documentCount: number;
  queryCount: number;
  totalChunks: number;
};

// Document Groups Schema (must be defined first for foreign key reference)
export const documentGroups = pgTable("document_groups", {
  id: varchar("id").primaryKey().default(sql`gen_random_uuid()`),
  name: text("name").notNull(),
  description: text("description"),
  color: text("color").notNull(),
  createdAt: timestamp("created_at").notNull().defaultNow(),
});

// Documents Schema
export const documents = pgTable("documents", {
  id: varchar("id").primaryKey().default(sql`gen_random_uuid()`),
  name: text("name").notNull(),
  size: integer("size").notNull(),
  type: text("type").notNull(),
  uploadedAt: timestamp("uploaded_at").notNull().defaultNow(),
  chunkCount: integer("chunk_count").notNull().default(0),
  status: text("status").notNull().default("processing"),
  groupId: varchar("group_id").references(() => documentGroups.id, { onDelete: "set null" }),
  userId: varchar("user_id").references(() => users.id, { onDelete: "cascade" }),
});

export const insertDocumentSchema = createInsertSchema(documents).omit({
  id: true,
  uploadedAt: true,
});

export type InsertDocument = z.infer<typeof insertDocumentSchema>;
export type Document = typeof documents.$inferSelect;

export const insertDocumentGroupSchema = createInsertSchema(documentGroups).omit({
  id: true,
  createdAt: true,
});

export type InsertDocumentGroup = z.infer<typeof insertDocumentGroupSchema>;
export type DocumentGroup = typeof documentGroups.$inferSelect;

// Query Sessions Schema
export const querySessions = pgTable("query_sessions", {
  id: varchar("id").primaryKey().default(sql`gen_random_uuid()`),
  query: text("query").notNull(),
  response: text("response").notNull(),
  model: text("model").notNull(),
  topK: integer("top_k").notNull(),
  temperature: real("temperature").notNull(),
  chunkSize: integer("chunk_size").notNull(),
  chunkOverlap: integer("chunk_overlap").notNull(),
  retrievedChunks: text("retrieved_chunks").array().notNull(),
  timestamp: timestamp("timestamp").notNull().defaultNow(),
  responseTime: integer("response_time").notNull(),
  userId: varchar("user_id").notNull().references(() => users.id, { onDelete: "cascade" }),
});

export const insertQuerySessionSchema = createInsertSchema(querySessions).omit({
  id: true,
  timestamp: true,
});

export type InsertQuerySession = z.infer<typeof insertQuerySessionSchema>;
export type QuerySession = typeof querySessions.$inferSelect;

// Vector Store Stats Schema
export const vectorStoreStats = pgTable("vector_store_stats", {
  id: varchar("id").primaryKey().default(sql`gen_random_uuid()`),
  totalChunks: integer("total_chunks").notNull(),
  totalEmbeddings: integer("total_embeddings").notNull(),
  dimensionality: integer("dimensionality").notNull(),
  lastUpdated: timestamp("last_updated").notNull().defaultNow(),
  healthStatus: text("health_status").notNull(),
  diskUsageMB: real("disk_usage_mb").notNull(),
});

export const insertVectorStoreStatsSchema = createInsertSchema(vectorStoreStats).omit({
  id: true,
});

export type InsertVectorStoreStats = z.infer<typeof insertVectorStoreStatsSchema>;
export type VectorStoreStats = typeof vectorStoreStats.$inferSelect;

// RAG Settings Schema
export const ragSettings = pgTable("rag_settings", {
  id: varchar("id").primaryKey().default(sql`gen_random_uuid()`),
  defaultTopK: integer("default_top_k").notNull().default(5),
  defaultTemperature: real("default_temperature").notNull().default(0.7),
  defaultChunkSize: integer("default_chunk_size").notNull().default(512),
  defaultChunkOverlap: integer("default_chunk_overlap").notNull().default(50),
  cachingEnabled: boolean("caching_enabled").notNull().default(true),
  rerankingEnabled: boolean("reranking_enabled").notNull().default(false),
  hybridSearchEnabled: boolean("hybrid_search_enabled").notNull().default(false),
});

export const insertRagSettingsSchema = createInsertSchema(ragSettings).omit({
  id: true,
});

export type InsertRagSettings = z.infer<typeof insertRagSettingsSchema>;
export type RagSettings = typeof ragSettings.$inferSelect;

// Analytics Data Schema
export const analyticsData = pgTable("analytics_data", {
  id: varchar("id").primaryKey().default(sql`gen_random_uuid()`),
  date: text("date").notNull(),
  queryCount: integer("query_count").notNull(),
  avgResponseTime: real("avg_response_time").notNull(),
  tokenUsage: integer("token_usage").notNull(),
  errorCount: integer("error_count").notNull(),
});

export const insertAnalyticsDataSchema = createInsertSchema(analyticsData).omit({
  id: true,
});

export type InsertAnalyticsData = z.infer<typeof insertAnalyticsDataSchema>;
export type AnalyticsData = typeof analyticsData.$inferSelect;

// Form-specific schemas for validation
export const documentUploadFormSchema = z.object({
  file: z.any().refine((file) => file instanceof File, "File is required"),
});

export const documentGroupFormSchema = insertDocumentGroupSchema.extend({
  name: z.string().min(1, "Group name is required"),
  description: z.string().optional(),
  color: z.string(),
});

export const queryFormSchema = z.object({
  query: z.string().min(1, "Query is required"),
  model: z.string(),
  topK: z.number().min(1).max(20),
  temperature: z.number().min(0).max(2),
  chunkSize: z.number().min(128).max(2048),
  chunkOverlap: z.number().min(0).max(200),
  documentIds: z.array(z.string()).optional(),
  groupIds: z.array(z.string()).optional(),
});

export type QueryFormData = z.infer<typeof queryFormSchema>;
export type DocumentGroupFormData = z.infer<typeof documentGroupFormSchema>;

// Document Chunks Schema
export const documentChunks = pgTable("document_chunks", {
  id: varchar("id").primaryKey().default(sql`gen_random_uuid()`),
  documentId: varchar("document_id").notNull().references(() => documents.id, { onDelete: "cascade" }),
  text: text("text").notNull(),
  chunkIndex: integer("chunk_index").notNull(),
  embedding: text("embedding"),
  metadata: text("metadata"),
  createdAt: timestamp("created_at").notNull().defaultNow(),
});

export const insertDocumentChunkSchema = createInsertSchema(documentChunks).omit({
  id: true,
  createdAt: true,
});

export type InsertDocumentChunk = z.infer<typeof insertDocumentChunkSchema>;
export type DocumentChunk = typeof documentChunks.$inferSelect;

// Relations
export const usersRelations = relations(users, ({ many }) => ({
  documents: many(documents),
}));

export const documentGroupsRelations = relations(documentGroups, ({ many }) => ({
  documents: many(documents),
}));

export const documentsRelations = relations(documents, ({ one, many }) => ({
  group: one(documentGroups, {
    fields: [documents.groupId],
    references: [documentGroups.id],
  }),
  user: one(users, {
    fields: [documents.userId],
    references: [users.id],
  }),
  chunks: many(documentChunks),
}));

export const documentChunksRelations = relations(documentChunks, ({ one }) => ({
  document: one(documents, {
    fields: [documentChunks.documentId],
    references: [documents.id],
  }),
}));
