import { useQuery } from "@tanstack/react-query";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { FileText, Database, Search, TrendingUp, Clock, Zap } from "lucide-react";
import { Line, LineChart, Bar, BarChart, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from "recharts";
import { ChartContainer, ChartTooltip, ChartTooltipContent } from "@/components/ui/chart";
import type { AnalyticsData, Document, QuerySession } from "@shared/schema";
import { useState, useEffect } from "react";
import { apiRequest } from "@/lib/queryClient";

export default function Dashboard() {
  const [stats, setStats] = useState<{}>({});
  const { data: analytics = [] } = useQuery<AnalyticsData[]>({
    queryKey: ["/api/analytics"],
  });

  const { data: documents = [] } = useQuery<Document[]>({
    queryKey: ["/api/documents"],
  });

  const { data: recentQueries = [] } = useQuery<QuerySession[]>({
    queryKey: ["/api/queries/recent"],
  });

  const totalQueries = analytics.reduce((sum, day) => sum + day.queryCount, 0);
  const avgResponseTime = analytics.length > 0
    ? analytics.reduce((sum, day) => sum + day.avgResponseTime, 0) / analytics.length
    : 0;
  const totalTokens = analytics.reduce((sum, day) => sum + day.tokenUsage, 0);

  const chartConfig = {
    queryCount: {
      label: "Queries",
      color: "hsl(var(--chart-1))",
    },
    avgResponseTime: {
      label: "Avg Response Time (ms)",
      color: "hsl(var(--chart-2))",
    },
  };

  // get dashbaord stats
    useEffect(() => {
      const user_id = JSON.parse(localStorage.getItem("user")).id;
      const dashboardStats = apiRequest("GET",
        `${import.meta.env.VITE_API_BASE_URL}/api/dashboard/stats/${user_id}`)
      .then((res) => res.json()).then((data) => {
          setStats(data);
      }).catch((error) => {
          console.error("Error fetching stats:", error);
      });
    }, []);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-semibold tracking-tight">Dashboard</h1>
        <p className="text-sm text-muted-foreground mt-1">
          Overview of your RAG system performance and activity
        </p>
      </div>

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
        <Card>
          <CardHeader className="flex flex-row flex-wrap items-center justify-between gap-2 space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Queries</CardTitle>
            <Search className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-semibold" data-testid="stat-total-queries">
              {stats.query_count}
            </div>
            <p className="text-xs text-muted-foreground mt-1">
              Last 7 days
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row flex-wrap items-center justify-between gap-2 space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Documents</CardTitle>
            <FileText className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-semibold" data-testid="stat-total-documents">
              {stats.document_count}
            </div>
            <p className="text-xs text-muted-foreground mt-1">
              {documents.reduce((sum, doc) => sum + doc.chunkCount, 0)} total chunks
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row flex-wrap items-center justify-between gap-2 space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Avg Response Time</CardTitle>
            <Clock className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-semibold" data-testid="stat-avg-response-time">
              {stats.average_response_time?.toFixed(2)}s
            </div>
            <p className="text-xs text-muted-foreground mt-1">
              Across all queries
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row flex-wrap items-center justify-between gap-2 space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Token Usage</CardTitle>
            <Zap className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-semibold" data-testid="stat-token-usage">
              {totalTokens.toLocaleString()}
            </div>
            <p className="text-xs text-muted-foreground mt-1">
              Total tokens consumed
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row flex-wrap items-center justify-between gap-2 space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Embeddings</CardTitle>
            <Database className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-semibold" data-testid="stat-embeddings">
              {documents.reduce((sum, doc) => sum + doc.chunkCount, 0).toLocaleString()}
            </div>
            <p className="text-xs text-muted-foreground mt-1">
              Vector embeddings stored
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row flex-wrap items-center justify-between gap-2 space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Success Rate</CardTitle>
            <TrendingUp className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-semibold" data-testid="stat-success-rate">
              {totalQueries > 0 
                ? ((1 - analytics.reduce((sum, day) => sum + day.errorCount, 0) / totalQueries) * 100).toFixed(1)
                : '100'}%
            </div>
            <p className="text-xs text-muted-foreground mt-1">
              Query success rate
            </p>
          </CardContent>
        </Card>
      </div>

      <div className="grid gap-6 md:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>Query Volume</CardTitle>
            <p className="text-sm text-muted-foreground">Daily query activity over the last week</p>
          </CardHeader>
          <CardContent>
            <ChartContainer config={chartConfig} className="h-[200px] w-full">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={analytics}>
                  <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
                  <XAxis
                    dataKey="date"
                    stroke="hsl(var(--muted-foreground))"
                    fontSize={12}
                  />
                  <YAxis stroke="hsl(var(--muted-foreground))" fontSize={12} />
                  <ChartTooltip content={<ChartTooltipContent />} />
                  <Line
                    type="monotone"
                    dataKey="queryCount"
                    stroke="var(--color-queryCount)"
                    strokeWidth={2}
                    dot={false}
                  />
                </LineChart>
              </ResponsiveContainer>
            </ChartContainer>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Response Times</CardTitle>
            <p className="text-sm text-muted-foreground">Average response time by day</p>
          </CardHeader>
          <CardContent>
            <ChartContainer config={chartConfig} className="h-[200px] w-full">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={analytics}>
                  <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
                  <XAxis
                    dataKey="date"
                    stroke="hsl(var(--muted-foreground))"
                    fontSize={12}
                  />
                  <YAxis stroke="hsl(var(--muted-foreground))" fontSize={12} />
                  <ChartTooltip content={<ChartTooltipContent />} />
                  <Bar
                    dataKey="avgResponseTime"
                    fill="var(--color-avgResponseTime)"
                    radius={[4, 4, 0, 0]}
                  />
                </BarChart>
              </ResponsiveContainer>
            </ChartContainer>
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Recent Activity</CardTitle>
          <p className="text-sm text-muted-foreground">Latest queries and responses</p>
        </CardHeader>
        <CardContent>
          {recentQueries.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-12 text-center">
              <Search className="h-12 w-12 text-muted-foreground/50 mb-4" />
              <h3 className="font-medium text-lg mb-1">No queries yet</h3>
              <p className="text-sm text-muted-foreground max-w-sm">
                Start using the query interface to ask questions and see your activity here
              </p>
            </div>
          ) : (
            <div className="space-y-4">
              {recentQueries.slice(0, 5).map((query) => (
                <div
                  key={query.id}
                  className="border-l-2 border-primary/50 pl-4 py-2"
                  data-testid={`recent-query-${query.id}`}
                >
                  <div className="flex items-start justify-between gap-4">
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-medium truncate">{query.query}</p>
                      <p className="text-xs text-muted-foreground mt-1 line-clamp-2">
                        {query.response}
                      </p>
                    </div>
                    <div className="text-xs text-muted-foreground whitespace-nowrap">
                      {new Date(query.timestamp).toLocaleTimeString()}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
