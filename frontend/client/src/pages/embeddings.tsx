import { useQuery, useMutation } from "@tanstack/react-query";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { Database, RefreshCw, Activity, HardDrive, Layers, CheckCircle2 } from "lucide-react";
import { useToast } from "@/hooks/use-toast";
import { apiRequest, queryClient } from "@/lib/queryClient";
import type { VectorStoreStats } from "@shared/schema";
import { useEffect, useState } from "react";

export default function Embeddings() {
  const { toast } = useToast();
  const [stats, setStats] = useState<{}>({});
  const [isLoading, setIsLoading] = useState(false);

  // const { data: stats, isLoading } = useQuery<VectorStoreStats>({
  //   queryKey: ["/api/vector-store/stats"],
  // });

  // get dashbaord stats
  useEffect(() => {
    setIsLoading(true);
    const user_id = JSON.parse(localStorage.getItem("user")).id;
    const dashboardStats = apiRequest("GET",
      `${import.meta.env.VITE_API_BASE_URL}/api/dashboard/stats/${user_id}`)
    .then((res) => res.json()).then((data) => {
        setStats(data);
        setIsLoading(false);
    }).catch((error) => {
        console.error("Error fetching stats:", error);
    });
  }, []);

  const reindexMutation = useMutation({
    mutationFn: async () => {
      return apiRequest("POST", "/api/vector-store/reindex", {});
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["/api/vector-store/stats"] });
      toast({
        title: "Reindexing started",
        description: "Vector store optimization is in progress.",
      });
    },
  });

  const getHealthColor = (status: string) => {
    switch (status) {
      case "healthy":
        return "text-green-500";
      case "warning":
        return "text-yellow-500";
      case "error":
        return "text-red-500";
      default:
        return "text-muted-foreground";
    }
  };

  const getHealthBadgeVariant = (status: string): "default" | "secondary" | "destructive" => {
    switch (status) {
      case "healthy":
        return "default";
      case "warning":
        return "secondary";
      case "error":
        return "destructive";
      default:
        return "secondary";
    }
  };

  const healthPercentage = stats?.healthStatus === "healthy" ? 100 : stats?.healthStatus === "warning" ? 70 : 30;

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <h1 className="text-3xl font-semibold tracking-tight">Vector Store</h1>
          <p className="text-sm text-muted-foreground mt-1">
            Manage embeddings and vector database health
          </p>
        </div>
        <Button
          onClick={() => reindexMutation.mutate()}
          disabled={reindexMutation.isPending}
          data-testid="button-reindex"
        >
          <RefreshCw className={`h-4 w-4 mr-2 ${reindexMutation.isPending ? 'animate-spin' : ''}`} />
          {reindexMutation.isPending ? "Reindexing..." : "Optimize Index"}
        </Button>
      </div>

      {isLoading ? (
        <div className="flex items-center justify-center py-12">
          <RefreshCw className="h-6 w-6 animate-spin text-muted-foreground" />
        </div>
      ) : stats ? (
        <>
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
            <Card>
              <CardHeader className="flex flex-row items-center justify-between gap-2 space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">Total Chunks</CardTitle>
                <Layers className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-semibold" data-testid="stat-total-chunks">
                  {/* {stats.total_chunks.toLocaleString()} */}
                  { stats.total_chunks }
                </div>
                <p className="text-xs text-muted-foreground mt-1">
                  Document segments
                </p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="flex flex-row items-center justify-between gap-2 space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">Embeddings</CardTitle>
                <Database className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-semibold" data-testid="stat-total-embeddings">
                  {/* {stats.totalEmbeddings.toLocaleString()} */}
                  {stats.total_embeddings}
                </div>
                <p className="text-xs text-muted-foreground mt-1">
                  Vector embeddings
                </p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="flex flex-row items-center justify-between gap-2 space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">Dimensionality</CardTitle>
                <Activity className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-semibold" data-testid="stat-dimensionality">
                  {stats.dimensionality}
                </div>
                <p className="text-xs text-muted-foreground mt-1">
                  Vector dimensions
                </p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="flex flex-row items-center justify-between gap-2 space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">Disk Usage</CardTitle>
                <HardDrive className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-semibold" data-testid="stat-disk-usage">
                  {/* {stats.diskUsageMB.toFixed(1)} MB */}
                  {stats.disk_usage_mb} MB
                </div>
                <p className="text-xs text-muted-foreground mt-1">
                  Storage footprint
                </p>
              </CardContent>
            </Card>
          </div>

          <div className="grid gap-6 md:grid-cols-2">
            <Card>
              <CardHeader>
                <CardTitle>Database Health</CardTitle>
                <p className="text-sm text-muted-foreground">Current vector store status</p>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <CheckCircle2 className={`h-5 w-5 ${getHealthColor(stats.healthStatus)}`} />
                    <span className="font-medium">Status</span>
                  </div>
                  <Badge variant={getHealthBadgeVariant(stats.health_status)} data-testid="badge-health-status">
                    {/* {stats.healthStatus.charAt(0).toUpperCase() + stats.healthStatus.slice(1)} */}
                    {stats.health_status + stats.health_status}
                  </Badge>
                </div>
                <div className="space-y-2">
                  <div className="flex items-center justify-between text-sm">
                    <span className="text-muted-foreground">Health Score</span>
                    <span className="font-medium">{healthPercentage}%</span>
                  </div>
                  <Progress value={healthPercentage} className="h-2" />
                </div>
                <div className="text-sm text-muted-foreground">
                  Last updated: {new Date(stats.lastUpdated).toLocaleString()}
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Database Configuration</CardTitle>
                <p className="text-sm text-muted-foreground">Vector store setup details</p>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="space-y-3">
                  <div className="flex items-center justify-between text-sm">
                    <span className="text-muted-foreground">Database</span>
                    <span className="font-mono font-medium">Postgres + pgvector</span>
                  </div>
                  <div className="flex items-center justify-between text-sm">
                    <span className="text-muted-foreground">Vector Type</span>
                    <span className="font-mono font-medium">float32[{stats.dimensionality}]</span>
                  </div>
                  <div className="flex items-center justify-between text-sm">
                    <span className="text-muted-foreground">Index Type</span>
                    <span className="font-mono font-medium">HNSW</span>
                  </div>
                  <div className="flex items-center justify-between text-sm">
                    <span className="text-muted-foreground">Distance Metric</span>
                    <span className="font-mono font-medium">Cosine Similarity</span>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>

          <Card>
            <CardHeader>
              <CardTitle>Sample Vectors</CardTitle>
              <p className="text-sm text-muted-foreground">Preview of stored embeddings</p>
            </CardHeader>
            <CardContent>
              <div className="bg-muted rounded-lg p-4 font-mono text-xs space-y-2">
                <div className="text-muted-foreground">// Sample vector (first 10 dimensions)</div>
                <div className="text-foreground">
                  [0.1234, -0.5678, 0.9012, -0.3456, 0.7890, 0.2345, -0.6789, 0.4567, -0.8901, 0.1111, ...]
                </div>
                <div className="text-muted-foreground mt-4">// Similarity score example</div>
                <div className="text-foreground">
                  cosine_similarity(query_vector, doc_vector) = 0.8734
                </div>
              </div>
            </CardContent>
          </Card>
        </>
      ) : (
        <div className="flex flex-col items-center justify-center py-12 text-center">
          <Database className="h-12 w-12 text-muted-foreground/50 mb-4" />
          <h3 className="font-medium text-lg mb-1">No vector store data</h3>
          <p className="text-sm text-muted-foreground max-w-sm">
            Upload documents to generate embeddings and populate the vector store
          </p>
        </div>
      )}
    </div>
  );
}
