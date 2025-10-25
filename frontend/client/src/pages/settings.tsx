import { useQuery, useMutation } from "@tanstack/react-query";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Form, FormControl, FormField, FormItem, FormLabel, FormDescription, FormMessage } from "@/components/ui/form";
import { Switch } from "@/components/ui/switch";
import { Slider } from "@/components/ui/slider";
import { Separator } from "@/components/ui/separator";
import { Settings as SettingsIcon, Save } from "lucide-react";
import { useToast } from "@/hooks/use-toast";
import { apiRequest, queryClient } from "@/lib/queryClient";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { insertRagSettingsSchema, type RagSettings } from "@shared/schema";
import { useEffect } from "react";
import { z } from "zod";

export default function Settings() {
  const { toast } = useToast();

  const { data: settings, isLoading } = useQuery<RagSettings>({
    queryKey: ["/api/settings"],
  });

  const form = useForm<z.infer<typeof insertRagSettingsSchema>>({
    resolver: zodResolver(insertRagSettingsSchema),
    defaultValues: {
      defaultTopK: 5,
      defaultTemperature: 0.7,
      defaultChunkSize: 512,
      defaultChunkOverlap: 50,
      cachingEnabled: true,
      rerankingEnabled: false,
      hybridSearchEnabled: false,
    },
  });

  useEffect(() => {
    if (settings) {
      form.reset({
        defaultTopK: settings.defaultTopK,
        defaultTemperature: settings.defaultTemperature,
        defaultChunkSize: settings.defaultChunkSize,
        defaultChunkOverlap: settings.defaultChunkOverlap,
        cachingEnabled: settings.cachingEnabled,
        rerankingEnabled: settings.rerankingEnabled,
        hybridSearchEnabled: settings.hybridSearchEnabled,
      });
    }
  }, [settings, form]);

  const updateMutation = useMutation({
    mutationFn: async (data: z.infer<typeof insertRagSettingsSchema>) => {
      return apiRequest("PUT", "/api/settings", data);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["/api/settings"] });
      toast({
        title: "Settings saved",
        description: "Your RAG configuration has been updated successfully.",
      });
    },
    onError: () => {
      toast({
        title: "Save failed",
        description: "There was an error saving your settings.",
        variant: "destructive",
      });
    },
  });

  const onSubmit = (data: z.infer<typeof insertRagSettingsSchema>) => {
    updateMutation.mutate(data);
  };

  const defaultTopK = form.watch("defaultTopK");
  const defaultTemperature = form.watch("defaultTemperature");
  const defaultChunkSize = form.watch("defaultChunkSize");
  const defaultChunkOverlap = form.watch("defaultChunkOverlap");

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <h1 className="text-3xl font-semibold tracking-tight">Settings</h1>
          <p className="text-sm text-muted-foreground mt-1">
            Configure default RAG parameters and system behavior
          </p>
        </div>
        <Button
          onClick={form.handleSubmit(onSubmit)}
          disabled={updateMutation.isPending}
          data-testid="button-save-settings"
        >
          <Save className="h-4 w-4 mr-2" />
          {updateMutation.isPending ? "Saving..." : "Save Changes"}
        </Button>
      </div>

      {isLoading ? (
        <div className="flex items-center justify-center py-12">
          <SettingsIcon className="h-6 w-6 animate-spin text-muted-foreground" />
        </div>
      ) : (
        <Form {...form}>
          <form onSubmit={form.handleSubmit(onSubmit)} className="grid gap-6 lg:grid-cols-2">
            <Card>
              <CardHeader>
                <CardTitle>Retrieval Parameters</CardTitle>
                <CardDescription>Default settings for document retrieval and chunking</CardDescription>
              </CardHeader>
              <CardContent className="space-y-6">
                <FormField
                  control={form.control}
                  name="defaultTopK"
                  render={({ field }) => (
                    <FormItem>
                      <div className="flex items-center justify-between">
                        <FormLabel>Default Top K</FormLabel>
                        <span className="text-sm font-medium" data-testid="value-default-top-k">
                          {defaultTopK}
                        </span>
                      </div>
                      <FormControl>
                        <Slider
                          value={[field.value]}
                          onValueChange={([value]) => field.onChange(value)}
                          min={1}
                          max={20}
                          step={1}
                          data-testid="slider-default-top-k"
                        />
                      </FormControl>
                      <FormDescription>
                        Number of document chunks to retrieve by default
                      </FormDescription>
                      <FormMessage />
                    </FormItem>
                  )}
                />

                <Separator />

                <FormField
                  control={form.control}
                  name="defaultChunkSize"
                  render={({ field }) => (
                    <FormItem>
                      <div className="flex items-center justify-between">
                        <FormLabel>Default Chunk Size</FormLabel>
                        <span className="text-sm font-medium" data-testid="value-default-chunk-size">
                          {defaultChunkSize}
                        </span>
                      </div>
                      <FormControl>
                        <Slider
                          value={[field.value]}
                          onValueChange={([value]) => field.onChange(value)}
                          min={128}
                          max={2048}
                          step={128}
                          data-testid="slider-default-chunk-size"
                        />
                      </FormControl>
                      <FormDescription>
                        Default size of document segments in tokens
                      </FormDescription>
                      <FormMessage />
                    </FormItem>
                  )}
                />

                <Separator />

                <FormField
                  control={form.control}
                  name="defaultChunkOverlap"
                  render={({ field }) => (
                    <FormItem>
                      <div className="flex items-center justify-between">
                        <FormLabel>Default Chunk Overlap</FormLabel>
                        <span className="text-sm font-medium" data-testid="value-default-chunk-overlap">
                          {defaultChunkOverlap}
                        </span>
                      </div>
                      <FormControl>
                        <Slider
                          value={[field.value]}
                          onValueChange={([value]) => field.onChange(value)}
                          min={0}
                          max={200}
                          step={10}
                          data-testid="slider-default-chunk-overlap"
                        />
                      </FormControl>
                      <FormDescription>
                        Default overlap between consecutive chunks
                      </FormDescription>
                      <FormMessage />
                    </FormItem>
                  )}
                />
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Generation Parameters</CardTitle>
                <CardDescription>Default settings for AI response generation</CardDescription>
              </CardHeader>
              <CardContent className="space-y-6">
                <FormField
                  control={form.control}
                  name="defaultTemperature"
                  render={({ field }) => (
                    <FormItem>
                      <div className="flex items-center justify-between">
                        <FormLabel>Default Temperature</FormLabel>
                        <span className="text-sm font-medium" data-testid="value-default-temperature">
                          {defaultTemperature.toFixed(2)}
                        </span>
                      </div>
                      <FormControl>
                        <Slider
                          value={[field.value]}
                          onValueChange={([value]) => field.onChange(value)}
                          min={0}
                          max={2}
                          step={0.1}
                          data-testid="slider-default-temperature"
                        />
                      </FormControl>
                      <FormDescription>
                        Controls randomness in AI responses (0 = deterministic, 2 = very random)
                      </FormDescription>
                      <FormMessage />
                    </FormItem>
                  )}
                />
              </CardContent>
            </Card>

            <Card className="lg:col-span-2">
              <CardHeader>
                <CardTitle>Advanced Features</CardTitle>
                <CardDescription>Enable or disable advanced RAG capabilities</CardDescription>
              </CardHeader>
              <CardContent className="space-y-6">
                <FormField
                  control={form.control}
                  name="cachingEnabled"
                  render={({ field }) => (
                    <FormItem className="flex items-center justify-between">
                      <div className="space-y-0.5">
                        <FormLabel>Response Caching</FormLabel>
                        <FormDescription>
                          Cache query responses to improve performance for repeated questions
                        </FormDescription>
                      </div>
                      <FormControl>
                        <Switch
                          checked={field.value}
                          onCheckedChange={field.onChange}
                          data-testid="switch-caching"
                        />
                      </FormControl>
                    </FormItem>
                  )}
                />

                <Separator />

                <FormField
                  control={form.control}
                  name="rerankingEnabled"
                  render={({ field }) => (
                    <FormItem className="flex items-center justify-between">
                      <div className="space-y-0.5">
                        <FormLabel>Result Reranking</FormLabel>
                        <FormDescription>
                          Rerank retrieved chunks using a cross-encoder model for better relevance
                        </FormDescription>
                      </div>
                      <FormControl>
                        <Switch
                          checked={field.value}
                          onCheckedChange={field.onChange}
                          data-testid="switch-reranking"
                        />
                      </FormControl>
                    </FormItem>
                  )}
                />

                <Separator />

                <FormField
                  control={form.control}
                  name="hybridSearchEnabled"
                  render={({ field }) => (
                    <FormItem className="flex items-center justify-between">
                      <div className="space-y-0.5">
                        <FormLabel>Hybrid Search</FormLabel>
                        <FormDescription>
                          Combine vector similarity with keyword search for improved recall
                        </FormDescription>
                      </div>
                      <FormControl>
                        <Switch
                          checked={field.value}
                          onCheckedChange={field.onChange}
                          data-testid="switch-hybrid-search"
                        />
                      </FormControl>
                    </FormItem>
                  )}
                />
              </CardContent>
            </Card>
          </form>
        </Form>
      )}
    </div>
  );
}
