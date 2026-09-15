import { db } from "./db";
import { ragSettings, vectorStoreStats, analyticsData, users } from "@shared/schema";
import { sql, eq } from "drizzle-orm";
import bcrypt from "bcryptjs";

async function seed() {
  console.log("Seeding database...");

  // Check if admin user exists
  const existingAdmin = await db.select().from(users).where(eq(users.email, 'admin@nexusrag.com'));
  if (existingAdmin.length === 0) {
    const hashedPassword = await bcrypt.hash("admin123", 10);
    await db.insert(users).values({
      email: "admin@nexusrag.com",
      passwordHash: hashedPassword,
      name: "Admin User",
      role: "admin",
    });
    console.log("✓ Created admin user (admin@nexusrag.com / admin123)");
  }

  // Check if settings already exist
  const existingSettings = await db.select().from(ragSettings);
  if (existingSettings.length === 0) {
    await db.insert(ragSettings).values({
      defaultTopK: 5,
      defaultTemperature: 0.7,
      defaultChunkSize: 512,
      defaultChunkOverlap: 50,
      cachingEnabled: true,
      rerankingEnabled: false,
      hybridSearchEnabled: false,
    });
    console.log("✓ Created default settings");
  }

  // Check if vector store stats exist
  const existingStats = await db.select().from(vectorStoreStats);
  if (existingStats.length === 0) {
    await db.insert(vectorStoreStats).values({
      totalChunks: 0,
      totalEmbeddings: 0,
      dimensionality: 1536,
      lastUpdated: new Date(),
      healthStatus: "healthy",
      diskUsageMB: 0,
    });
    console.log("✓ Created vector store stats");
  }

  // Create analytics data for last 7 days if not exists
  const existingAnalytics = await db.select().from(analyticsData);
  if (existingAnalytics.length === 0) {
    const last7Days = Array.from({ length: 7 }, (_, i) => {
      const date = new Date();
      date.setDate(date.getDate() - (6 - i));
      return date.toISOString().split('T')[0];
    });

    for (const date of last7Days) {
      await db.insert(analyticsData).values({
        date,
        queryCount: Math.floor(Math.random() * 50) + 10,
        avgResponseTime: Math.floor(Math.random() * 300) + 200,
        tokenUsage: Math.floor(Math.random() * 5000) + 1000,
        errorCount: Math.floor(Math.random() * 3),
      });
    }
    console.log("✓ Created analytics data for last 7 days");
  }

  console.log("Database seeding complete!");
  process.exit(0);
}

seed().catch((error) => {
  console.error("Error seeding database:", error);
  process.exit(1);
});
