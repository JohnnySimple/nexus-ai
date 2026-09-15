import { useQuery } from "@tanstack/react-query";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Line, LineChart, Bar, BarChart, Area, AreaChart, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend } from "recharts";
import { ChartContainer, ChartTooltip, ChartTooltipContent } from "@/components/ui/chart";
import { TrendingUp, TrendingDown, Activity, AlertCircle, Zap, Clock } from "lucide-react";
import type { AnalyticsData } from "@shared/schema";
import { useState, useEffect } from "react";
import { apiRequest } from "@/lib/queryClient";


export default function Analytics() {
  const [stats, setStats] = useState<{}>({});
  const { data: analytics = [], isLoading } = useQuery<AnalyticsData[]>({
    queryKey: ["/api/analytics"],
  });

  const totalQueries = analytics.reduce((sum, day) => sum + day.queryCount, 0);
  const totalErrors = analytics.reduce((sum, day) => sum + day.errorCount, 0);
  const avgResponseTime = analytics.length > 0
    ? analytics.reduce((sum, day) => sum + day.avgResponseTime, 0) / analytics.length
    : 0;
  const totalTokens = analytics.reduce((sum, day) => sum + day.tokenUsage, 0);

  const errorRate = totalQueries > 0 ? (totalErrors / totalQueries) * 100 : 0;
  const successRate = 100 - errorRate;

  const chartConfig = {
    queryCount: {
      label: "Queries",
      color: "hsl(var(--chart-1))",
    },
    avgResponseTime: {
      label: "Response Time (ms)",
      color: "hsl(var(--chart-2))",
    },
    tokenUsage: {
      label: "Tokens",
      color: "hsl(var(--chart-3))",
    },
    errorCount: {
      label: "Errors",
      color: "hsl(var(--destructive))",
    },
  };

  // get dashbaord stats
  useEffect(() => {
    const dashboardStats = apiRequest("GET",
      `${import.meta.env.VITE_API_BASE_URL}/api/dashboard/stats`)
    .then((res) => res.json()).then((data) => {
        setStats(data);
    }).catch((error) => {
        console.error("Error fetching stats:", error);
    });
  }, []);

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <h1 className="text-3xl font-semibold tracking-tight">Analytics</h1>
          <p className="text-sm text-muted-foreground mt-1">
            Monitor system performance and usage metrics
          </p>
        </div>
      </div>

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between gap-2 space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Queries</CardTitle>
            <Activity className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-semibold" data-testid="analytics-total-queries">
              {stats.query_count}
            </div>
            <div className="flex items-center gap-1 mt-1">
              <TrendingUp className="h-3 w-3 text-green-500" />
              <p className="text-xs text-muted-foreground">
                +12% from last week
              </p>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between gap-2 space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Avg Response Time</CardTitle>
            <Clock className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-semibold" data-testid="analytics-avg-response">
              {stats.average_response_time?.toFixed(0)}ms
            </div>
            <div className="flex items-center gap-1 mt-1">
              <TrendingDown className="h-3 w-3 text-green-500" />
              <p className="text-xs text-muted-foreground">
                -8% improvement
              </p>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between gap-2 space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Token Usage</CardTitle>
            <Zap className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-semibold" data-testid="analytics-token-usage">
              {(totalTokens / 1000).toFixed(1)}K
            </div>
            <p className="text-xs text-muted-foreground mt-1">
              Total tokens consumed
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between gap-2 space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Success Rate</CardTitle>
            <AlertCircle className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-semibold" data-testid="analytics-success-rate">
              {successRate.toFixed(1)}%
            </div>
            <p className="text-xs text-muted-foreground mt-1">
              {totalErrors} errors total
            </p>
          </CardContent>
        </Card>
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>Query Volume Over Time</CardTitle>
            <p className="text-sm text-muted-foreground">Daily query activity</p>
          </CardHeader>
          <CardContent>
            {analytics.length === 0 ? (
              <div className="flex items-center justify-center h-[300px] text-muted-foreground">
                No data available
              </div>
            ) : (
              <ChartContainer config={chartConfig} className="h-[300px] w-full">
                <ResponsiveContainer width="100%" height="100%">
                  <AreaChart data={analytics}>
                    <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
                    <XAxis
                      dataKey="date"
                      stroke="hsl(var(--muted-foreground))"
                      fontSize={12}
                    />
                    <YAxis stroke="hsl(var(--muted-foreground))" fontSize={12} />
                    <ChartTooltip content={<ChartTooltipContent />} />
                    <Area
                      type="monotone"
                      dataKey="queryCount"
                      stroke="var(--color-queryCount)"
                      fill="var(--color-queryCount)"
                      fillOpacity={0.2}
                      strokeWidth={2}
                    />
                  </AreaChart>
                </ResponsiveContainer>
              </ChartContainer>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Response Time Trend</CardTitle>
            <p className="text-sm text-muted-foreground">Average response time by day</p>
          </CardHeader>
          <CardContent>
            {analytics.length === 0 ? (
              <div className="flex items-center justify-center h-[300px] text-muted-foreground">
                No data available
              </div>
            ) : (
              <ChartContainer config={chartConfig} className="h-[300px] w-full">
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
                      dataKey="avgResponseTime"
                      stroke="var(--color-avgResponseTime)"
                      strokeWidth={2}
                      dot={{ r: 4 }}
                    />
                  </LineChart>
                </ResponsiveContainer>
              </ChartContainer>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Token Consumption</CardTitle>
            <p className="text-sm text-muted-foreground">Daily token usage</p>
          </CardHeader>
          <CardContent>
            {analytics.length === 0 ? (
              <div className="flex items-center justify-center h-[300px] text-muted-foreground">
                No data available
              </div>
            ) : (
              <ChartContainer config={chartConfig} className="h-[300px] w-full">
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
                      dataKey="tokenUsage"
                      fill="var(--color-tokenUsage)"
                      radius={[4, 4, 0, 0]}
                    />
                  </BarChart>
                </ResponsiveContainer>
              </ChartContainer>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Error Tracking</CardTitle>
            <p className="text-sm text-muted-foreground">Query failures over time</p>
          </CardHeader>
          <CardContent>
            {analytics.length === 0 ? (
              <div className="flex items-center justify-center h-[300px] text-muted-foreground">
                No data available
              </div>
            ) : (
              <ChartContainer config={chartConfig} className="h-[300px] w-full">
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
                      dataKey="errorCount"
                      fill="var(--color-errorCount)"
                      radius={[4, 4, 0, 0]}
                    />
                  </BarChart>
                </ResponsiveContainer>
              </ChartContainer>
            )}
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>System Performance Summary</CardTitle>
          <p className="text-sm text-muted-foreground">Key metrics and insights</p>
        </CardHeader>
        <CardContent>
          <div className="grid gap-4 md:grid-cols-3">
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-sm text-muted-foreground">Peak Query Day</span>
                <Badge variant="secondary">
                  {analytics.length > 0
                    ? analytics.reduce((max, day) => day.queryCount > max.queryCount ? day : max, analytics[0]).date
                    : 'N/A'}
                </Badge>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm text-muted-foreground">Fastest Response</span>
                <Badge variant="secondary">
                  {analytics.length > 0
                    ? Math.min(...analytics.map(d => d.avgResponseTime)).toFixed(0) + 'ms'
                    : 'N/A'}
                </Badge>
              </div>
            </div>
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-sm text-muted-foreground">Most Active Day</span>
                <Badge variant="secondary">
                  {analytics.length > 0
                    ? analytics.reduce((max, day) => day.queryCount > max.queryCount ? day : max, analytics[0]).date
                    : 'N/A'}
                </Badge>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm text-muted-foreground">Avg Daily Queries</span>
                <Badge variant="secondary">
                  {analytics.length > 0
                    ? Math.round(totalQueries / analytics.length)
                    : 0}
                </Badge>
              </div>
            </div>
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-sm text-muted-foreground">Error Rate</span>
                <Badge variant={errorRate > 5 ? "destructive" : "secondary"}>
                  {errorRate.toFixed(2)}%
                </Badge>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm text-muted-foreground">Total Tokens</span>
                <Badge variant="secondary">
                  {totalTokens.toLocaleString()}
                </Badge>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
