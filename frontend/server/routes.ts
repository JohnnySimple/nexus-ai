import type { Express } from "express";
import { createServer, type Server } from "http";
import { storage } from "./storage";
import multer from "multer";
import {
  insertDocumentSchema,
  insertDocumentGroupSchema,
  insertQuerySessionSchema,
  insertRagSettingsSchema,
  queryFormSchema,
  loginSchema,
  registerSchema,
  adminCreateUserSchema,
  adminUpdateUserSchema,
} from "@shared/schema";
import { processDocument } from "./document-processor";
import { hashPassword, comparePassword, generateToken } from "./auth";
import { authenticate, authorize } from "./auth-middleware";

const upload = multer({ storage: multer.memoryStorage() });

export async function registerRoutes(app: Express): Promise<Server> {
  // Auth routes (public)
  app.post("/api/auth/register", async (req, res) => {
    try {
      const validation = registerSchema.safeParse(req.body);
      if (!validation.success) {
        return res.status(400).json({ error: validation.error.flatten() });
      }

      const { email, password, name } = validation.data;

      // Check if user already exists
      const existingUser = await storage.getUserByEmail(email);
      if (existingUser) {
        return res.status(400).json({ error: "User already exists" });
      }

      // Hash password
      const passwordHash = await hashPassword(password);

      // Create user
      const user = await storage.createUser({
        email,
        passwordHash,
        name,
        role: "user", // Default role
      });

      // Generate token
      const token = generateToken(user);

      // Return user without password hash
      const { passwordHash: _, ...userWithoutPassword } = user;
      
      res.json({ user: userWithoutPassword, token });
    } catch (error) {
      console.log(error);
      res.status(500).json({ error: "Failed to register user" });
    }
  });

  app.post("/api/auth/login", async (req, res) => {
    try {
      const validation = loginSchema.safeParse(req.body);
      if (!validation.success) {
        return res.status(400).json({ error: validation.error.flatten() });
      }

      const { email, password } = validation.data;

      // Get user by email
      const user = await storage.getUserByEmail(email);
      if (!user) {
        return res.status(401).json({ error: "Invalid credentials" });
      }

      // Verify password
      const isValid = await comparePassword(password, user.passwordHash);
      if (!isValid) {
        return res.status(401).json({ error: "Invalid credentials" });
      }

      // Update last login
      await storage.updateUserLastLogin(user.id);

      // Generate token
      const token = generateToken(user);

      // Return user without password hash
      const { passwordHash: _, ...userWithoutPassword } = user;
      
      res.json({ user: userWithoutPassword, token });
    } catch (error) {
      res.status(500).json({ error: "Failed to login" });
    }
  });

  app.get("/api/auth/me", authenticate, async (req, res) => {
    try {
      const user = await storage.getUser(req.user!.userId);
      if (!user) {
        return res.status(404).json({ error: "User not found" });
      }

      const { passwordHash: _, ...userWithoutPassword } = user;
      res.json(userWithoutPassword);
    } catch (error) {
      res.status(500).json({ error: "Failed to get user profile" });
    }
  });

  // Admin routes (protected, admin only)
  app.get("/api/admin/users", authenticate, authorize(["admin"]), async (req, res) => {
    try {
      const allUsers = await storage.getAllUsers();
      
      // Get metrics for each user
      const usersWithMetrics = await Promise.all(
        allUsers.map(async (user) => {
          const metrics = await storage.getUserMetrics(user.id);
          const { passwordHash: _, ...userWithoutPassword } = user;
          return {
            ...userWithoutPassword,
            ...metrics,
          };
        })
      );

      res.json(usersWithMetrics);
    } catch (error) {
      res.status(500).json({ error: "Failed to fetch users" });
    }
  });

  app.post("/api/admin/users", authenticate, authorize(["admin"]), async (req, res) => {
    try {
      const validation = adminCreateUserSchema.safeParse(req.body);
      if (!validation.success) {
        return res.status(400).json({ error: validation.error.flatten() });
      }

      const { email, password, name, role } = validation.data;

      // Check if user already exists
      const existingUser = await storage.getUserByEmail(email);
      if (existingUser) {
        return res.status(400).json({ error: "User already exists" });
      }

      // Hash password
      const passwordHash = await hashPassword(password);

      // Create user
      const user = await storage.createUser({
        email,
        passwordHash,
        name,
        role,
      });

      const { passwordHash: _, ...userWithoutPassword } = user;
      res.json(userWithoutPassword);
    } catch (error) {
      res.status(500).json({ error: "Failed to create user" });
    }
  });

  app.patch("/api/admin/users/:id", authenticate, authorize(["admin"]), async (req, res) => {
    try {
      const validation = adminUpdateUserSchema.safeParse(req.body);
      if (!validation.success) {
        return res.status(400).json({ error: validation.error.flatten() });
      }

      const updates: any = { ...validation.data };

      // Hash password if provided
      if (updates.password) {
        updates.passwordHash = await hashPassword(updates.password);
        delete updates.password;
      }

      const user = await storage.updateUser(req.params.id, updates);
      if (!user) {
        return res.status(404).json({ error: "User not found" });
      }

      const { passwordHash: _, ...userWithoutPassword } = user;
      res.json(userWithoutPassword);
    } catch (error) {
      res.status(500).json({ error: "Failed to update user" });
    }
  });

  app.delete("/api/admin/users/:id", authenticate, authorize(["admin"]), async (req, res) => {
    try {
      // Prevent self-deletion
      if (req.params.id === req.user!.userId) {
        return res.status(400).json({ error: "Cannot delete your own account" });
      }

      await storage.deleteUser(req.params.id);
      res.json({ success: true });
    } catch (error) {
      res.status(500).json({ error: "Failed to delete user" });
    }
  });

  // Document routes (protected)
  app.get("/api/documents", authenticate, async (req, res) => {
    try {
      const documents = await storage.getDocuments();
      res.json(documents);
    } catch (error) {
      res.status(500).json({ error: "Failed to fetch documents" });
    }
  });

  app.post("/api/documents/upload", authenticate, upload.single("file"), async (req, res) => {
    try {
      if (!req.file) {
        return res.status(400).json({ error: "No file uploaded" });
      }

      const fileExtension = req.file.originalname.split('.').pop() || 'txt';
      const mimeTypes: Record<string, string> = {
        'pdf': 'application/pdf',
        'txt': 'text/plain',
        'md': 'text/markdown',
      };

      // Create document in processing state
      const document = await storage.createDocument({
        name: req.file.originalname,
        size: req.file.size,
        type: mimeTypes[fileExtension] || 'application/octet-stream',
        chunkCount: 0,
        status: "processing",
        groupId: null,
      });

      // Process document asynchronously
      processDocument({
        documentId: document.id,
        buffer: req.file.buffer,
        filename: req.file.originalname,
        mimeType: mimeTypes[fileExtension] || 'application/octet-stream',
      }).catch((error) => {
        console.error("Error processing document:", error);
      });

      res.json(document);
    } catch (error) {
      res.status(500).json({ error: "Failed to upload document" });
    }
  });

  app.delete("/api/documents/:id", authenticate, async (req, res) => {
    try {
      await storage.deleteDocument(req.params.id);
      res.json({ success: true });
    } catch (error) {
      res.status(500).json({ error: "Failed to delete document" });
    }
  });

  app.get("/api/documents/:id/chunks", authenticate, async (req, res) => {
    try {
      const { getDocumentChunks } = await import("./document-processor");
      const chunks = await getDocumentChunks(req.params.id);
      res.json(chunks);
    } catch (error) {
      res.status(500).json({ error: "Failed to fetch document chunks" });
    }
  });

  app.post("/api/documents/:id/re-embed", authenticate, async (req, res) => {
    try {
      const { reEmbedDocument } = await import("./document-processor");
      await reEmbedDocument(req.params.id);
      res.json({ success: true });
    } catch (error) {
      res.status(500).json({ error: "Failed to re-embed document" });
    }
  });

  // Document Groups routes
  app.get("/api/document-groups", authenticate, async (req, res) => {
    try {
      const groups = await storage.getDocumentGroups();
      res.json(groups);
    } catch (error) {
      res.status(500).json({ error: "Failed to fetch document groups" });
    }
  });

  app.post("/api/document-groups", authenticate, async (req, res) => {
    try {
      const validation = insertDocumentGroupSchema.safeParse(req.body);
      if (!validation.success) {
        return res.status(400).json({ error: validation.error });
      }

      const group = await storage.createDocumentGroup(validation.data);
      res.json(group);
    } catch (error) {
      res.status(500).json({ error: "Failed to create document group" });
    }
  });

  // Query routes
  app.post("/api/query", authenticate, async (req, res) => {
    try {
      const validation = queryFormSchema.safeParse(req.body);
      if (!validation.success) {
        return res.status(400).json({ error: validation.error });
      }

      const { query, model, topK, temperature, chunkSize, chunkOverlap, documentIds, groupIds } = validation.data;

      const { processRAGQuery } = await import("./rag-processor");
      const { response, retrievedChunks, responseTime } = await processRAGQuery({
        query,
        model,
        topK,
        temperature,
        chunkSize,
        chunkOverlap,
        documentIds,
        groupIds,
      });

      const session = await storage.createQuerySession({
        query,
        response,
        model,
        topK,
        temperature,
        chunkSize,
        chunkOverlap,
        retrievedChunks,
        responseTime,
        userId: req.user!.id,
      });

      res.json(session);
    } catch (error) {
      res.status(500).json({ error: "Failed to process query" });
    }
  });

  app.get("/api/queries/sessions", authenticate, async (req, res) => {
    try {
      const sessions = await storage.getQuerySessions(req.user!.id);
      res.json(sessions);
    } catch (error) {
      res.status(500).json({ error: "Failed to fetch query sessions" });
    }
  });

  app.get("/api/queries/recent", authenticate, async (req, res) => {
    try {
      const sessions = await storage.getRecentQueries(req.user!.id, 10);
      res.json(sessions);
    } catch (error) {
      res.status(500).json({ error: "Failed to fetch recent queries" });
    }
  });

  // Vector Store routes
  app.get("/api/vector-store/stats", authenticate, async (req, res) => {
    try {
      const stats = await storage.getVectorStoreStats();
      res.json(stats);
    } catch (error) {
      res.status(500).json({ error: "Failed to fetch vector store stats" });
    }
  });

  app.post("/api/vector-store/reindex", authenticate, async (req, res) => {
    try {
      const stats = await storage.getVectorStoreStats();
      if (stats) {
        const updatedStats = await storage.updateVectorStoreStats({
          ...stats,
          lastUpdated: new Date(),
          healthStatus: "healthy",
        });
        res.json(updatedStats);
      } else {
        res.status(404).json({ error: "Vector store stats not found" });
      }
    } catch (error) {
      res.status(500).json({ error: "Failed to reindex vector store" });
    }
  });

  // Settings routes
  app.get("/api/settings", authenticate, async (req, res) => {
    try {
      const settings = await storage.getSettings();
      res.json(settings);
    } catch (error) {
      res.status(500).json({ error: "Failed to fetch settings" });
    }
  });

  app.put("/api/settings", authenticate, async (req, res) => {
    try {
      const validation = insertRagSettingsSchema.safeParse(req.body);
      if (!validation.success) {
        return res.status(400).json({ error: validation.error });
      }

      const settings = await storage.updateSettings(validation.data);
      res.json(settings);
    } catch (error) {
      res.status(500).json({ error: "Failed to update settings" });
    }
  });

  // Analytics routes
  app.get("/api/analytics", authenticate, async (req, res) => {
    try {
      const analytics = await storage.getAnalyticsData();
      res.json(analytics);
    } catch (error) {
      res.status(500).json({ error: "Failed to fetch analytics data" });
    }
  });

  const httpServer = createServer(app);

  return httpServer;
}
