CREATE TABLE "analytics_data" (
	"id" varchar PRIMARY KEY DEFAULT gen_random_uuid() NOT NULL,
	"date" text NOT NULL,
	"query_count" integer NOT NULL,
	"avg_response_time" real NOT NULL,
	"token_usage" integer NOT NULL,
	"error_count" integer NOT NULL
);
--> statement-breakpoint
CREATE TABLE "document_chunks" (
	"id" varchar PRIMARY KEY DEFAULT gen_random_uuid() NOT NULL,
	"document_id" varchar NOT NULL,
	"text" text NOT NULL,
	"chunk_index" integer NOT NULL,
	"embedding" text,
	"metadata" text,
	"created_at" timestamp DEFAULT now() NOT NULL
);
--> statement-breakpoint
CREATE TABLE "document_groups" (
	"id" varchar PRIMARY KEY DEFAULT gen_random_uuid() NOT NULL,
	"name" text NOT NULL,
	"description" text,
	"color" text NOT NULL,
	"created_at" timestamp DEFAULT now() NOT NULL
);
--> statement-breakpoint
CREATE TABLE "documents" (
	"id" varchar PRIMARY KEY DEFAULT gen_random_uuid() NOT NULL,
	"name" text NOT NULL,
	"size" integer NOT NULL,
	"type" text NOT NULL,
	"uploaded_at" timestamp DEFAULT now() NOT NULL,
	"chunk_count" integer DEFAULT 0 NOT NULL,
	"status" text DEFAULT 'processing' NOT NULL,
	"group_id" varchar,
	"user_id" varchar
);
--> statement-breakpoint
CREATE TABLE "query_sessions" (
	"id" varchar PRIMARY KEY DEFAULT gen_random_uuid() NOT NULL,
	"query" text NOT NULL,
	"response" text NOT NULL,
	"model" text NOT NULL,
	"top_k" integer NOT NULL,
	"temperature" real NOT NULL,
	"chunk_size" integer NOT NULL,
	"chunk_overlap" integer NOT NULL,
	"retrieved_chunks" text[] NOT NULL,
	"timestamp" timestamp DEFAULT now() NOT NULL,
	"response_time" integer NOT NULL,
	"user_id" varchar NOT NULL
);
--> statement-breakpoint
CREATE TABLE "rag_settings" (
	"id" varchar PRIMARY KEY DEFAULT gen_random_uuid() NOT NULL,
	"default_top_k" integer DEFAULT 5 NOT NULL,
	"default_temperature" real DEFAULT 0.7 NOT NULL,
	"default_chunk_size" integer DEFAULT 512 NOT NULL,
	"default_chunk_overlap" integer DEFAULT 50 NOT NULL,
	"caching_enabled" boolean DEFAULT true NOT NULL,
	"reranking_enabled" boolean DEFAULT false NOT NULL,
	"hybrid_search_enabled" boolean DEFAULT false NOT NULL
);
--> statement-breakpoint
CREATE TABLE "users" (
	"id" varchar PRIMARY KEY DEFAULT gen_random_uuid() NOT NULL,
	"email" text NOT NULL,
	"password_hash" text NOT NULL,
	"name" text NOT NULL,
	"role" text DEFAULT 'user' NOT NULL,
	"created_at" timestamp DEFAULT now() NOT NULL,
	"last_login" timestamp,
	CONSTRAINT "users_email_unique" UNIQUE("email")
);
--> statement-breakpoint
CREATE TABLE "vector_store_stats" (
	"id" varchar PRIMARY KEY DEFAULT gen_random_uuid() NOT NULL,
	"total_chunks" integer NOT NULL,
	"total_embeddings" integer NOT NULL,
	"dimensionality" integer NOT NULL,
	"last_updated" timestamp DEFAULT now() NOT NULL,
	"health_status" text NOT NULL,
	"disk_usage_mb" real NOT NULL
);
--> statement-breakpoint
ALTER TABLE "document_chunks" ADD CONSTRAINT "document_chunks_document_id_documents_id_fk" FOREIGN KEY ("document_id") REFERENCES "public"."documents"("id") ON DELETE cascade ON UPDATE no action;--> statement-breakpoint
ALTER TABLE "documents" ADD CONSTRAINT "documents_group_id_document_groups_id_fk" FOREIGN KEY ("group_id") REFERENCES "public"."document_groups"("id") ON DELETE set null ON UPDATE no action;--> statement-breakpoint
ALTER TABLE "documents" ADD CONSTRAINT "documents_user_id_users_id_fk" FOREIGN KEY ("user_id") REFERENCES "public"."users"("id") ON DELETE cascade ON UPDATE no action;--> statement-breakpoint
ALTER TABLE "query_sessions" ADD CONSTRAINT "query_sessions_user_id_users_id_fk" FOREIGN KEY ("user_id") REFERENCES "public"."users"("id") ON DELETE cascade ON UPDATE no action;