import { useEffect, useState } from "react";
import { useQuery, useMutation } from "@tanstack/react-query";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Form, FormControl, FormField, FormItem, FormLabel, FormMessage } from "@/components/ui/form";
import { Textarea } from "@/components/ui/textarea";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Separator } from "@/components/ui/separator";
import { Badge } from "@/components/ui/badge";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Send, Bot, User, Sparkles, Clock, Layers, FileText, Folder } from "lucide-react";
import { useToast } from "@/hooks/use-toast";
import { apiRequest, queryClient } from "@/lib/queryClient";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { queryFormSchema, type QueryFormData } from "@shared/schema";
import type { QuerySession, RagSettings, Document, DocumentGroup } from "@shared/schema";
import { Slider } from "@/components/ui/slider";
import { Label } from "@/components/ui/label";
import { Checkbox } from "@/components/ui/checkbox";
import { set } from "date-fns";

export default function Query() {
  const { toast } = useToast();
  const [groups, setGroups] = useState<DocumentGroup[]>([]);
  const [sessions, setSessions] = useState<[]>([]);
  const [documents, setDocuments] = useState<Document[]>([]);
  const [llms, setLlms] = useState<[]>([]);

  const { data: settings } = useQuery<RagSettings>({
    queryKey: ["/api/settings"],
  });

  // const { data: sessions = [] } = useQuery<QuerySession[]>({
  //   queryKey: ["/api/queries/sessions"],
  // });

  // const { data: documents = [] } = useQuery<Document[]>({
  //   queryKey: ["/api/documents"],
  // });

  // const { data: groups = [] } = useQuery<DocumentGroup[]>({
  //   queryKey: ["/api/document-groups"],
  // });

  // get document groups
  useEffect(() => {
    const groups = apiRequest("GET", `${import.meta.env.VITE_API_BASE_URL}/api/documents/group`)
      .then((res) => res.json()).then((data) => {
        setGroups(data);
      }).catch((error) => {
        console.error("Error fetching document groups:", error);
      });
  }, []);

  // get sessions
  useEffect(() => {
    const user_id = JSON.parse(localStorage.getItem("user")).id;
    const sessions = apiRequest("GET", `${import.meta.env.VITE_API_BASE_URL}/api/query/query-session/user/${user_id}`)
      .then((res) => res.json()).then((data) => {
        setSessions(data);
      }).catch((error) => {
        console.error("Error fetching query sessions", error);
      })
  }, [])

  // get documents
  useEffect(() => {
    const documents = apiRequest("GET", `${import.meta.env.VITE_API_BASE_URL}/api/rag/documents`)
      .then((res) => res.json()).then((data) => {
        setDocuments(data);
      }).catch((error) => {
        console.error("Error fetching documents:", error);
      });
  }, []);

  // get llms
  useEffect(() => {
    const llms = apiRequest("GET", `${import.meta.env.VITE_API_BASE_URL}/api/rag/llms`)
      .then((res) => res.json()).then((data) => {
        setLlms(data.models);
      }).catch((error) => {
        console.error("Error fetching LLMs:", error);
      });
  }, []);

  const form = useForm<QueryFormData>({
    resolver: zodResolver(queryFormSchema),
    defaultValues: {
      query: "",
      model: "gpt-4",
      topK: settings?.defaultTopK || 5,
      temperature: settings?.defaultTemperature || 0.7,
      chunkSize: settings?.defaultChunkSize || 512,
      chunkOverlap: settings?.defaultChunkOverlap || 50,
      documentIds: [],
      groupIds: [],
    },
  });

  const queryMutation = useMutation({
    mutationFn: async (data: QueryFormData) => {

      const params = new URLSearchParams({
        query: data.query,
        top_k: data.topK,
        // document_ids: data.documentIds,
        with_llm_response: true,
        user_id: JSON.parse(localStorage.getItem("user")).id,
        model: data.model
      });

      data.documentIds?.forEach(id => {
        params.append("document_ids", id);
      });
      
      const res = await apiRequest("GET", `${import.meta.env.VITE_API_BASE_URL}/api/rag/query?${params.toString()}`);
      const response = await res.json();
    },
    onSuccess: () => {
      // queryClient.invalidateQueries({ queryKey: ["/api/queries/sessions"] });
      // queryClient.invalidateQueries({ queryKey: ["/api/queries/recent"] });
      form.reset({
        query: "",
        model: form.getValues("model"),
        topK: form.getValues("topK"),
        temperature: form.getValues("temperature"),
        chunkSize: form.getValues("chunkSize"),
        chunkOverlap: form.getValues("chunkOverlap"),
      });
      toast({
        title: "Query completed",
        description: "Your question has been processed successfully.",
      });
    },
    onError: () => {
      toast({
        title: "Query failed",
        description: "There was an error processing your query.",
        variant: "destructive",
      });
    },
  });

  const onSubmit = (data: QueryFormData) => {
    queryMutation.mutate(data);
  };

  const topK = form.watch("topK");
  const temperature = form.watch("temperature");
  const chunkSize = form.watch("chunkSize");
  const chunkOverlap = form.watch("chunkOverlap");

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-semibold tracking-tight">Query Interface</h1>
        <p className="text-sm text-muted-foreground mt-1">
          Ask questions and get AI-powered answers from your knowledge base
        </p>
      </div>

      <div className="grid gap-6 lg:grid-cols-3">
        <div className="lg:col-span-2 space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Ask a Question</CardTitle>
            </CardHeader>
            <CardContent>
              <Form {...form}>
                <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-4">
                  <FormField
                    control={form.control}
                    name="query"
                    render={({ field }) => (
                      <FormItem>
                        <FormLabel>Your Question</FormLabel>
                        <FormControl>
                          <Textarea
                            placeholder="What would you like to know about your documents?"
                            rows={4}
                            data-testid="textarea-query"
                            {...field}
                          />
                        </FormControl>
                        <FormMessage />
                      </FormItem>
                    )}
                  />

                  <div className="grid gap-4 sm:grid-cols-2">
                    <FormField
                      control={form.control}
                      name="documentIds"
                      render={({ field }) => (
                        <FormItem>
                          <FormLabel className="flex items-center gap-2">
                            <FileText className="h-4 w-4" />
                            Search Documents
                          </FormLabel>
                          <div className="border rounded-md p-3 space-y-2 max-h-[200px] overflow-y-auto" data-testid="documents-selection">
                            <div className="flex items-center space-x-2">
                              <Checkbox
                                id="all-documents"
                                checked={!field.value || field.value.length === 0}
                                onCheckedChange={(checked) => {
                                  if (checked) {
                                    field.onChange([]);
                                  }
                                }}
                                data-testid="checkbox-all-documents"
                              />
                              <label
                                htmlFor="all-documents"
                                className="text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70"
                              >
                                All Documents
                              </label>
                            </div>
                            <Separator />
                            {documents.length === 0 ? (
                              <p className="text-sm text-muted-foreground">No documents available</p>
                            ) : (
                              documents.map((doc) => (
                                <div key={doc.id} className="flex items-center space-x-2">
                                  <Checkbox
                                    id={`doc-${doc.id}`}
                                    checked={field.value?.includes(doc.id)}
                                    onCheckedChange={(checked) => {
                                      const current = field.value || [];
                                      if (checked) {
                                        field.onChange([...current, doc.id]);
                                      } else {
                                        field.onChange(current.filter((id) => id !== doc.id));
                                      }
                                    }}
                                    data-testid={`checkbox-doc-${doc.id}`}
                                  />
                                  <label
                                    htmlFor={`doc-${doc.id}`}
                                    className="text-sm leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70"
                                  >
                                    {doc.filename}
                                  </label>
                                </div>
                              ))
                            )}
                          </div>
                          <FormMessage />
                        </FormItem>
                      )}
                    />

                    <FormField
                      control={form.control}
                      name="groupIds"
                      render={({ field }) => (
                        <FormItem>
                          <FormLabel className="flex items-center gap-2">
                            <Folder className="h-4 w-4" />
                            Search Groups
                          </FormLabel>
                          <div className="border rounded-md p-3 space-y-2 max-h-[200px] overflow-y-auto" data-testid="groups-selection">
                            <div className="flex items-center space-x-2">
                              <Checkbox
                                id="all-groups"
                                checked={!field.value || field.value.length === 0}
                                onCheckedChange={(checked) => {
                                  if (checked) {
                                    field.onChange([]);
                                  }
                                }}
                                data-testid="checkbox-all-groups"
                              />
                              <label
                                htmlFor="all-groups"
                                className="text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70"
                              >
                                All Groups
                              </label>
                            </div>
                            <Separator />
                            {groups.length === 0 ? (
                              <p className="text-sm text-muted-foreground">No groups available</p>
                            ) : (
                              groups.map((group) => (
                                <div key={group.id} className="flex items-center space-x-2">
                                  <Checkbox
                                    id={`group-${group.id}`}
                                    checked={field.value?.includes(group.id)}
                                    onCheckedChange={(checked) => {
                                      const current = field.value || [];
                                      if (checked) {
                                        field.onChange([...current, group.id]);
                                      } else {
                                        field.onChange(current.filter((id) => id !== group.id));
                                      }
                                    }}
                                    data-testid={`checkbox-group-${group.id}`}
                                  />
                                  <label
                                    htmlFor={`group-${group.id}`}
                                    className="text-sm leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70"
                                  >
                                    {group.name}
                                  </label>
                                </div>
                              ))
                            )}
                          </div>
                          <FormMessage />
                        </FormItem>
                      )}
                    />
                  </div>

                  <div className="flex items-center gap-2">
                    <FormField
                      control={form.control}
                      name="model"
                      render={({ field }) => (
                        <FormItem>
                          <FormControl>
                            <Select value={field.value} onValueChange={field.onChange}>
                              <SelectTrigger className="w-[200px]" data-testid="select-model">
                                <SelectValue placeholder="Select model" />
                              </SelectTrigger>
                              <SelectContent>
                                {/* <SelectItem value="gpt-4">GPT-4</SelectItem>
                                <SelectItem value="gpt-3.5-turbo">GPT-3.5 Turbo</SelectItem>
                                <SelectItem value="claude-3">Claude 3</SelectItem>
                                <SelectItem value="local-llm">Local LLM</SelectItem> */}
                                {
                                  llms.length === 0 ? (
                                    <SelectItem value="none">No models available</SelectItem>
                                  ) : (
                                    llms.map((llm: any) => (
                                      <SelectItem key={llm.name} value={llm.model as string}>{llm.name}</SelectItem>
                                    ))
                                  )
                                }
                              </SelectContent>
                            </Select>
                          </FormControl>
                        </FormItem>
                      )}
                    />
                    <Button
                      type="submit"
                      className="ml-auto"
                      disabled={queryMutation.isPending}
                      data-testid="button-submit-query"
                    >
                      {queryMutation.isPending ? (
                        <>Processing...</>
                      ) : (
                        <>
                          <Send className="h-4 w-4 mr-2" />
                          Send Query
                        </>
                      )}
                    </Button>
                  </div>
                </form>
              </Form>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Query History</CardTitle>
              <p className="text-sm text-muted-foreground">Recent queries and responses</p>
            </CardHeader>
            <CardContent>
              <ScrollArea className="h-[400px] pr-4">
                {sessions.length === 0 ? (
                  <div className="flex flex-col items-center justify-center py-12 text-center">
                    <Sparkles className="h-12 w-12 text-muted-foreground/50 mb-4" />
                    <h3 className="font-medium text-lg mb-1">No queries yet</h3>
                    <p className="text-sm text-muted-foreground max-w-sm">
                      Ask your first question to see responses appear here
                    </p>
                  </div>
                ) : (
                  <div className="space-y-6">
                    {sessions.map((session) => (
                      <div key={session.id} className="space-y-3" data-testid={`session-${session.id}`}>
                        <div className="flex items-start gap-3">
                          <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-primary/10">
                            <User className="h-4 w-4 text-primary" />
                          </div>
                          <div className="flex-1 space-y-1">
                            <p className="text-sm font-medium" data-testid={`query-text-${session.id}`}>{session.query}</p>
                            <div className="flex items-center gap-2 text-xs text-muted-foreground">
                              <Clock className="h-3 w-3" />
                              <span data-testid={`query-time-${session.id}`}>
                                {new Date(session.created_at).toLocaleString()}
                              </span>
                              <span>•</span>
                              <Badge variant="outline" className="text-xs" data-testid={`query-model-${session.id}`}>
                                {session.model}
                              </Badge>
                            </div>
                          </div>
                        </div>
                        <div className="flex items-start gap-3 pl-11">
                          <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-chart-2/10">
                            <Bot className="h-4 w-4 text-chart-2" />
                          </div>
                          <div className="flex-1 space-y-2">
                            <p className="text-sm text-muted-foreground leading-relaxed" data-testid={`response-text-${session.id}`}>
                              {session.response}
                            </p>
                            {session.retrieved_chunks.length > 0 && (
                              <div className="mt-2 pt-2 border-t border-border">
                                <div className="flex items-center gap-1 text-xs text-muted-foreground mb-2">
                                  <Layers className="h-3 w-3" />
                                  <span data-testid={`chunks-count-${session.id}`}>
                                    Retrieved {session.retrieved_chunks.length} chunks
                                  </span>
                                  <span>•</span>
                                  <span data-testid={`response-time-${session.id}`}>{session.response_time}ms</span>
                                </div>
                                <div className="space-y-1">
                                  {/* {session.retrieved_chunks.flat(1).slice(0,2).map((chunk, idx) => (
                                    <div
                                      key={idx}
                                      className="text-xs bg-muted rounded p-2 font-mono line-clamp-2"
                                      data-testid={`chunk-${session.id}-${idx}`}
                                    >
                                      {chunk}
                                    </div>
                                  ))} */}
                                  {session.retrieved_chunks.slice(0,2).map((chunk, idx) => (
                                    <div
                                      key={idx}
                                      className="text-xs bg-muted rounded p-2 font-mono line-clamp-2"
                                      data-testid={`chunk-${session.id}-${idx}`}>
                                      {chunk.document_name} - Pg. {chunk.page_number}
                                    </div>
                                  ))}
                                </div>
                              </div>
                            )}
                          </div>
                        </div>
                        <Separator />
                      </div>
                    ))}
                  </div>
                )}
              </ScrollArea>
            </CardContent>
          </Card>
        </div>

        <div className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Parameters</CardTitle>
              <p className="text-sm text-muted-foreground">Adjust retrieval settings</p>
            </CardHeader>
            <CardContent className="space-y-6">
              <FormField
                control={form.control}
                name="topK"
                render={({ field }) => (
                  <div className="space-y-3">
                    <div className="flex items-center justify-between">
                      <Label htmlFor="top-k">Top K Results</Label>
                      <span className="text-sm font-medium" data-testid="value-top-k">{topK}</span>
                    </div>
                    <Slider
                      id="top-k"
                      value={[field.value]}
                      onValueChange={([value]) => field.onChange(value)}
                      min={1}
                      max={20}
                      step={1}
                      data-testid="slider-top-k"
                    />
                    <p className="text-xs text-muted-foreground">
                      Number of document chunks to retrieve
                    </p>
                  </div>
                )}
              />

              <Separator />

              <FormField
                control={form.control}
                name="temperature"
                render={({ field }) => (
                  <div className="space-y-3">
                    <div className="flex items-center justify-between">
                      <Label htmlFor="temperature">Temperature</Label>
                      <span className="text-sm font-medium" data-testid="value-temperature">{temperature.toFixed(2)}</span>
                    </div>
                    <Slider
                      id="temperature"
                      value={[field.value]}
                      onValueChange={([value]) => field.onChange(value)}
                      min={0}
                      max={2}
                      step={0.1}
                      data-testid="slider-temperature"
                    />
                    <p className="text-xs text-muted-foreground">
                      Controls randomness in responses
                    </p>
                  </div>
                )}
              />

              <Separator />

              <FormField
                control={form.control}
                name="chunkSize"
                render={({ field }) => (
                  <div className="space-y-3">
                    <div className="flex items-center justify-between">
                      <Label htmlFor="chunk-size">Chunk Size</Label>
                      <span className="text-sm font-medium" data-testid="value-chunk-size">{chunkSize}</span>
                    </div>
                    <Slider
                      id="chunk-size"
                      value={[field.value]}
                      onValueChange={([value]) => field.onChange(value)}
                      min={128}
                      max={2048}
                      step={128}
                      data-testid="slider-chunk-size"
                    />
                    <p className="text-xs text-muted-foreground">
                      Size of document segments in tokens
                    </p>
                  </div>
                )}
              />

              <Separator />

              <FormField
                control={form.control}
                name="chunkOverlap"
                render={({ field }) => (
                  <div className="space-y-3">
                    <div className="flex items-center justify-between">
                      <Label htmlFor="chunk-overlap">Chunk Overlap</Label>
                      <span className="text-sm font-medium" data-testid="value-chunk-overlap">{chunkOverlap}</span>
                    </div>
                    <Slider
                      id="chunk-overlap"
                      value={[field.value]}
                      onValueChange={([value]) => field.onChange(value)}
                      min={0}
                      max={200}
                      step={10}
                      data-testid="slider-chunk-overlap"
                    />
                    <p className="text-xs text-muted-foreground">
                      Overlap between consecutive chunks
                    </p>
                  </div>
                )}
              />
            </CardContent>
          </Card>

          {settings && (
            <Card>
              <CardHeader>
                <CardTitle>Default Settings</CardTitle>
              </CardHeader>
              <CardContent className="space-y-2 text-sm">
                <div className="flex items-center justify-between">
                  <span className="text-muted-foreground">Top K</span>
                  <span className="font-medium" data-testid="default-top-k">{settings.defaultTopK}</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-muted-foreground">Temperature</span>
                  <span className="font-medium" data-testid="default-temperature">{settings.defaultTemperature}</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-muted-foreground">Chunk Size</span>
                  <span className="font-medium" data-testid="default-chunk-size">{settings.defaultChunkSize}</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-muted-foreground">Chunk Overlap</span>
                  <span className="font-medium" data-testid="default-chunk-overlap">{settings.defaultChunkOverlap}</span>
                </div>
              </CardContent>
            </Card>
          )}
        </div>
      </div>
    </div>
  );
}
