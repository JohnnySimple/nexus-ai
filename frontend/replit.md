# Nexus RAG - Enterprise RAG System Dashboard

## Overview
Nexus RAG is an enterprise-grade dashboard for managing Retrieval-Augmented Generation (RAG) systems. Built with React, TypeScript, and a modern tech stack, it provides data scientists and AI engineers with comprehensive tools to manage knowledge bases, configure RAG parameters, and monitor system performance.

## Project Architecture

### Frontend Stack
- **Framework**: React with TypeScript
- **Build Tool**: Vite
- **Styling**: Tailwind CSS with dark-first design
- **Component Library**: shadcn/ui (Radix UI primitives)
- **State Management**: TanStack Query for server state
- **Routing**: Wouter for client-side routing
- **Charts**: Recharts for data visualization
- **Forms**: React Hook Form with Zod validation

### Backend Stack
- **Runtime**: Node.js with Express
- **Database**: PostgreSQL with Drizzle ORM
- **Authentication**: JWT-based with bcryptjs password hashing
- **File Upload**: Multer for document processing
- **Validation**: Zod schemas for type-safe API validation
- **Document Processing**: Text extraction for PDF/TXT/MD files
- **RAG Engine**: Cosine similarity-based vector search with simulated embeddings

## Core Features

### 1. Dashboard
- Real-time metrics overview (queries, documents, response times, tokens)
- Query volume and response time charts
- Recent activity timeline
- Success rate and error tracking

### 2. Document Management
- Document upload with drag-and-drop support
- Document table with filtering and sorting
- Document grouping for organization
- Chunk count and status tracking
- File type support: PDF, TXT, MD

### 3. Vector Store Management
- Vector database health monitoring
- Embedding statistics (chunks, dimensionality, disk usage)
- Index optimization and reindexing
- Sample vector preview
- Database configuration details

### 4. Query Interface
- Natural language query input
- Model selection (GPT-4, GPT-3.5, Claude 3, Local LLM)
- Parameter controls:
  - Top K (number of chunks to retrieve)
  - Temperature (response randomness)
  - Chunk Size (segment size in tokens)
  - Chunk Overlap (overlap between chunks)
- Chat-style query history with retrieved chunks
- Response time tracking

### 5. Analytics
- Query volume trends (line chart)
- Response time analysis (bar chart)
- Token consumption tracking
- Error rate monitoring
- Performance metrics summary

### 6. Settings
- Default RAG parameter configuration
- Advanced features toggle:
  - Response caching
  - Result reranking
  - Hybrid search

## Data Model

### Users
- ID, email (unique), password hash
- Name, role (admin/user)
- Created at, last login timestamp

### Documents
- ID, name, size, type
- Upload timestamp
- Chunk count and status
- Optional group assignment
- User ID (owner)

### Document Chunks
- ID, document ID (foreign key with cascade delete)
- Text content, chunk index
- Embedding (1536-dimensional vector as JSON)
- Metadata (filename, type)

### Document Groups
- Organizational categories
- Color-coded for visual distinction

### Query Sessions
- Query text and response
- Model and parameters used
- Retrieved chunks and metadata
- Response time metrics
- User ID (owner) for per-user tracking

### Vector Store Stats
- Total chunks and embeddings
- Dimensionality and disk usage
- Health status
- Last update timestamp

### RAG Settings
- Default retrieval parameters
- Feature flags for advanced capabilities

### Analytics Data
- Daily aggregated metrics
- Query counts and response times
- Token usage and error counts

## Recent Changes

### 2024-10-12 (Phase 3 - Admin Features & Query Filtering)
- **Admin Dashboard**: Implemented comprehensive admin user management
  - Created admin-only routes for listing, creating, updating, and deleting users
  - Added user metrics display (document count, query count, total chunks)
  - Built admin UI with user table, create/edit dialogs, and role management
  - Protected admin routes with authorize(["admin"]) middleware
- **Query Sessions User Association**: Added userId to query sessions
  - Modified query_sessions table to include userId foreign key
  - Updated query routes to associate sessions with authenticated users
  - Modified getQuerySessions and getRecentQueries to filter by userId
  - Enables per-user query tracking and metrics
- **Document/Group Filtering in Query Interface**: Implemented selective search
  - Added documentIds and groupIds optional arrays to queryFormSchema
  - Created checkbox UI for selecting specific documents or groups
  - Implemented "All Documents" and "All Groups" options (empty arrays)
  - Updated RAG processor with filtered chunk retrieval using OR logic (union)
- **Admin User Seed**: Enhanced database seed script
  - Added admin user creation (admin@nexusrag.com / admin123)
  - Seed script now checks and creates admin user if not exists
  - Ensures proper admin access for new deployments

### 2024-10-12 (Phase 2 - Database & Authentication)
- **Database Migration**: Migrated from in-memory storage to PostgreSQL with Drizzle ORM
  - Added all database tables with proper foreign key relationships
  - Implemented cascade delete for document chunks
  - Created database seed script for default settings and analytics data
- **Document Processing**: Implemented real document processing pipeline
  - Text extraction for PDF/TXT/MD files
  - Chunking logic with configurable size and overlap (fixed infinite loop bug)
  - Simulated embedding generation (1536 dimensions)
  - Async processing with status tracking (processing → completed/failed)
- **RAG Query Engine**: Built real query processing with vector similarity search
  - Cosine similarity-based chunk retrieval
  - Top-K selection with similarity scores
  - Contextual response generation
  - Response time tracking and session management
- **Authentication System**: Implemented JWT-based authentication
  - User registration and login with bcrypt password hashing
  - Protected API routes with authentication middleware
  - Login and register pages with form validation
  - Protected route wrapper on frontend
  - Token storage in localStorage with Authorization header injection

### 2024-10-12 (Phase 1 - Initial Implementation)
- Initial implementation of complete RAG dashboard
- Implemented all core features (Dashboard, Documents, Embeddings, Query, Analytics, Settings)
- Added comprehensive form validation using Zod schemas
- Implemented dark-first UI with Inter and JetBrains Mono fonts
- Created in-memory storage with mock data for testing
- Added file upload support with multer
- Implemented all API endpoints with proper validation

## User Preferences

### Design Preferences
- Dark mode as default (follows design_guidelines.md)
- Clean, data-centric interface inspired by AI platforms
- Minimal shadows and subtle elevations
- Information density over decoration
- Professional color palette with vibrant blue primary color

### Technical Preferences
- TypeScript for type safety
- Form validation with Zod
- Server state management with TanStack Query
- Component-based architecture with shadcn/ui
- Responsive design for desktop and tablet

## Project Structure

```
├── client/
│   ├── src/
│   │   ├── components/
│   │   │   ├── ui/          # shadcn components
│   │   │   ├── app-sidebar.tsx
│   │   │   ├── theme-provider.tsx
│   │   │   └── theme-toggle.tsx
│   │   ├── pages/
│   │   │   ├── dashboard.tsx
│   │   │   ├── documents.tsx
│   │   │   ├── embeddings.tsx
│   │   │   ├── query.tsx
│   │   │   ├── analytics.tsx
│   │   │   └── settings.tsx
│   │   ├── lib/
│   │   │   └── queryClient.ts
│   │   ├── App.tsx
│   │   └── index.css
│   └── index.html
├── server/
│   ├── routes.ts
│   ├── storage.ts
│   └── index.ts
├── shared/
│   └── schema.ts          # Shared types and schemas
└── design_guidelines.md   # UI/UX design system
```

## API Endpoints

### Authentication (Public)
- POST `/api/auth/register` - Register new user
- POST `/api/auth/login` - Login user
- GET `/api/auth/me` - Get current user profile (protected)

### Documents (Protected)
- GET `/api/documents` - List all documents
- POST `/api/documents/upload` - Upload new document
- DELETE `/api/documents/:id` - Delete document
- GET `/api/documents/:id/chunks` - Get document chunks
- POST `/api/documents/:id/re-embed` - Re-embed document

### Document Groups (Protected)
- GET `/api/document-groups` - List all groups
- POST `/api/document-groups` - Create new group

### Queries (Protected)
- POST `/api/query` - Execute RAG query
- GET `/api/queries/sessions` - Get all query sessions
- GET `/api/queries/recent` - Get recent queries

### Vector Store (Protected)
- GET `/api/vector-store/stats` - Get vector store statistics
- POST `/api/vector-store/reindex` - Reindex vector database

### Settings (Protected)
- GET `/api/settings` - Get RAG settings
- PUT `/api/settings` - Update RAG settings

### Analytics (Protected)
- GET `/api/analytics` - Get analytics data

## Development Notes

- The application uses PostgreSQL database with Drizzle ORM for persistence
- All API routes are protected with JWT authentication middleware
- Document processing uses simulated embeddings (1536 dimensions)
- RAG query uses cosine similarity for vector search
- Analytics data is seeded for last 7 days on initialization
- All forms use proper validation with Zod schemas
- UI follows design guidelines religiously for visual consistency

## Technical Details

### Authentication Flow
1. User registers/logs in via `/api/auth/register` or `/api/auth/login`
2. Server generates JWT token with user ID, email, and role
3. Token stored in localStorage on frontend
4. All API requests include `Authorization: Bearer <token>` header
5. Backend middleware validates token and attaches user to request
6. Protected routes return 401 if token is missing/invalid

### Document Processing Flow
1. User uploads document via `/api/documents/upload`
2. Document created in database with "processing" status
3. Text extraction runs asynchronously (PDF/TXT/MD support)
4. Text chunked with configurable size and overlap
5. Simulated embeddings generated for each chunk (1536-d vectors)
6. Chunks stored in database with metadata
7. Document status updated to "completed" or "failed"

### RAG Query Flow
1. User submits query with parameters (model, topK, temperature, etc.)
2. Query embedding generated (simulated 1536-d vector)
3. Cosine similarity computed against all document chunk embeddings
4. Top-K chunks selected based on similarity scores
5. Context extracted from selected chunks
6. Response generated using context (simulated LLM call)
7. Query session saved with response, chunks, and metrics
