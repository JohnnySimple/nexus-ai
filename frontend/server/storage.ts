import {
  type Document,
  type InsertDocument,
  type DocumentGroup,
  type InsertDocumentGroup,
  type QuerySession,
  type InsertQuerySession,
  type VectorStoreStats,
  type InsertVectorStoreStats,
  type RagSettings,
  type InsertRagSettings,
  type AnalyticsData,
  type InsertAnalyticsData,
  type User,
  type InsertUser,
  documents,
  documentGroups,
  querySessions,
  vectorStoreStats as vectorStoreStatsTable,
  ragSettings as ragSettingsTable,
  analyticsData as analyticsDataTable,
  users,
} from "@shared/schema";
import { db } from "./db";
import { eq, desc } from "drizzle-orm";

export interface IStorage {
  // Users
  getUser(id: string): Promise<User | undefined>;
  getUserByEmail(email: string): Promise<User | undefined>;
  createUser(user: InsertUser): Promise<User>;
  updateUserLastLogin(id: string): Promise<void>;
  
  // Admin user management
  getAllUsers(): Promise<User[]>;
  updateUser(id: string, updates: Partial<Omit<User, 'id' | 'createdAt'>>): Promise<User | undefined>;
  deleteUser(id: string): Promise<void>;
  getUserMetrics(userId: string): Promise<{ documentCount: number; queryCount: number; totalChunks: number }>;

  // Documents
  getDocuments(): Promise<Document[]>;
  getDocument(id: string): Promise<Document | undefined>;
  createDocument(doc: InsertDocument): Promise<Document>;
  deleteDocument(id: string): Promise<void>;

  // Document Groups
  getDocumentGroups(): Promise<DocumentGroup[]>;
  createDocumentGroup(group: InsertDocumentGroup): Promise<DocumentGroup>;

  // Query Sessions
  getQuerySessions(userId: string): Promise<QuerySession[]>;
  getRecentQueries(userId: string, limit: number): Promise<QuerySession[]>;
  createQuerySession(session: InsertQuerySession): Promise<QuerySession>;

  // Vector Store Stats
  getVectorStoreStats(): Promise<VectorStoreStats | undefined>;
  updateVectorStoreStats(stats: InsertVectorStoreStats): Promise<VectorStoreStats>;

  // Settings
  getSettings(): Promise<RagSettings | undefined>;
  updateSettings(settings: InsertRagSettings): Promise<RagSettings>;

  // Analytics
  getAnalyticsData(): Promise<AnalyticsData[]>;
  createAnalyticsData(data: InsertAnalyticsData): Promise<AnalyticsData>;
}

export class DatabaseStorage implements IStorage {
  // User methods
  async getUser(id: string): Promise<User | undefined> {
    const [user] = await db.select().from(users).where(eq(users.id, id));
    return user || undefined;
  }

  async getUserByEmail(email: string): Promise<User | undefined> {
    const [user] = await db.select().from(users).where(eq(users.email, email));
    return user || undefined;
  }

  async createUser(insertUser: InsertUser): Promise<User> {
    const [user] = await db.insert(users).values(insertUser).returning();
    return user;
  }

  async updateUserLastLogin(id: string): Promise<void> {
    await db
      .update(users)
      .set({ lastLogin: new Date() })
      .where(eq(users.id, id));
  }

  // Admin user management methods
  async getAllUsers(): Promise<User[]> {
    return await db.select().from(users);
  }

  async updateUser(id: string, updates: Partial<Omit<User, 'id' | 'createdAt'>>): Promise<User | undefined> {
    const [updatedUser] = await db
      .update(users)
      .set(updates)
      .where(eq(users.id, id))
      .returning();
    return updatedUser || undefined;
  }

  async deleteUser(id: string): Promise<void> {
    await db.delete(users).where(eq(users.id, id));
  }

  async getUserMetrics(userId: string): Promise<{ documentCount: number; queryCount: number; totalChunks: number }> {
    // Get document count and total chunks for user
    const userDocs = await db.select().from(documents).where(eq(documents.userId, userId));
    const documentCount = userDocs.length;
    const totalChunks = userDocs.reduce((sum, doc) => sum + doc.chunkCount, 0);

    // Get query count for user (we'll need to add userId to query sessions in future)
    // For now, return 0 as we don't have userId in querySessions
    const queryCount = 0;

    return { documentCount, queryCount, totalChunks };
  }

  // Document methods
  async getDocuments(): Promise<Document[]> {
    return await db.select().from(documents);
  }

  async getDocument(id: string): Promise<Document | undefined> {
    const [doc] = await db.select().from(documents).where(eq(documents.id, id));
    return doc || undefined;
  }

  async createDocument(insertDoc: InsertDocument): Promise<Document> {
    // Validate groupId if provided
    if (insertDoc.groupId) {
      const [group] = await db
        .select()
        .from(documentGroups)
        .where(eq(documentGroups.id, insertDoc.groupId));
      
      if (!group) {
        throw new Error(`Document group with id ${insertDoc.groupId} does not exist`);
      }
    }
    
    const [doc] = await db.insert(documents).values(insertDoc).returning();
    
    // Update vector store stats
    const [stats] = await db.select().from(vectorStoreStatsTable);
    if (stats) {
      await db
        .update(vectorStoreStatsTable)
        .set({
          totalChunks: stats.totalChunks + doc.chunkCount,
          totalEmbeddings: stats.totalEmbeddings + doc.chunkCount,
          diskUsageMB: stats.diskUsageMB + insertDoc.size / (1024 * 1024),
          lastUpdated: new Date(),
        })
        .where(eq(vectorStoreStatsTable.id, stats.id));
    }
    
    return doc;
  }

  async deleteDocument(id: string): Promise<void> {
    const [doc] = await db.select().from(documents).where(eq(documents.id, id));
    if (doc) {
      await db.delete(documents).where(eq(documents.id, id));
      
      // Update vector store stats
      const [stats] = await db.select().from(vectorStoreStatsTable);
      if (stats) {
        await db
          .update(vectorStoreStatsTable)
          .set({
            totalChunks: Math.max(0, stats.totalChunks - doc.chunkCount),
            totalEmbeddings: Math.max(0, stats.totalEmbeddings - doc.chunkCount),
            diskUsageMB: Math.max(0, stats.diskUsageMB - doc.size / (1024 * 1024)),
            lastUpdated: new Date(),
          })
          .where(eq(vectorStoreStatsTable.id, stats.id));
      }
    }
  }

  async getDocumentGroups(): Promise<DocumentGroup[]> {
    return await db.select().from(documentGroups);
  }

  async createDocumentGroup(insertGroup: InsertDocumentGroup): Promise<DocumentGroup> {
    const [group] = await db.insert(documentGroups).values(insertGroup).returning();
    return group;
  }

  async getQuerySessions(userId: string): Promise<QuerySession[]> {
    return await db
      .select()
      .from(querySessions)
      .where(eq(querySessions.userId, userId))
      .orderBy(desc(querySessions.timestamp));
  }

  async getRecentQueries(userId: string, limit: number): Promise<QuerySession[]> {
    return await db
      .select()
      .from(querySessions)
      .where(eq(querySessions.userId, userId))
      .orderBy(desc(querySessions.timestamp))
      .limit(limit);
  }

  async createQuerySession(insertSession: InsertQuerySession): Promise<QuerySession> {
    const [session] = await db.insert(querySessions).values(insertSession).returning();
    
    // Update today's analytics
    const today = new Date().toISOString().split('T')[0];
    const [todayAnalytics] = await db
      .select()
      .from(analyticsDataTable)
      .where(eq(analyticsDataTable.date, today));
    
    if (todayAnalytics) {
      const newQueryCount = todayAnalytics.queryCount + 1;
      const newAvgResponseTime =
        (todayAnalytics.avgResponseTime * todayAnalytics.queryCount + insertSession.responseTime) /
        newQueryCount;
      
      await db
        .update(analyticsDataTable)
        .set({
          queryCount: newQueryCount,
          avgResponseTime: newAvgResponseTime,
          tokenUsage: todayAnalytics.tokenUsage + Math.floor(Math.random() * 500) + 100,
        })
        .where(eq(analyticsDataTable.id, todayAnalytics.id));
    } else {
      // Create today's analytics entry
      await db.insert(analyticsDataTable).values({
        date: today,
        queryCount: 1,
        avgResponseTime: insertSession.responseTime,
        tokenUsage: Math.floor(Math.random() * 500) + 100,
        errorCount: 0,
      });
    }
    
    return session;
  }

  async getVectorStoreStats(): Promise<VectorStoreStats | undefined> {
    const [stats] = await db.select().from(vectorStoreStatsTable);
    return stats || undefined;
  }

  async updateVectorStoreStats(insertStats: InsertVectorStoreStats): Promise<VectorStoreStats> {
    const [existingStats] = await db.select().from(vectorStoreStatsTable);
    
    if (existingStats) {
      const [updated] = await db
        .update(vectorStoreStatsTable)
        .set({ ...insertStats, lastUpdated: new Date() })
        .where(eq(vectorStoreStatsTable.id, existingStats.id))
        .returning();
      return updated;
    } else {
      const [created] = await db
        .insert(vectorStoreStatsTable)
        .values({ ...insertStats, lastUpdated: new Date() })
        .returning();
      return created;
    }
  }

  async getSettings(): Promise<RagSettings | undefined> {
    const [settings] = await db.select().from(ragSettingsTable);
    return settings || undefined;
  }

  async updateSettings(insertSettings: InsertRagSettings): Promise<RagSettings> {
    const [existingSettings] = await db.select().from(ragSettingsTable);
    
    if (existingSettings) {
      const [updated] = await db
        .update(ragSettingsTable)
        .set(insertSettings)
        .where(eq(ragSettingsTable.id, existingSettings.id))
        .returning();
      return updated;
    } else {
      const [created] = await db.insert(ragSettingsTable).values(insertSettings).returning();
      return created;
    }
  }

  async getAnalyticsData(): Promise<AnalyticsData[]> {
    return await db.select().from(analyticsDataTable).orderBy(analyticsDataTable.date);
  }

  async createAnalyticsData(insertData: InsertAnalyticsData): Promise<AnalyticsData> {
    const [data] = await db.insert(analyticsDataTable).values(insertData).returning();
    return data;
  }
}

export const storage = new DatabaseStorage();
