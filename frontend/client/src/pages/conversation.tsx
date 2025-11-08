import { useState, useRef, useEffect } from "react";
import { Send, Bot, User, Plus, MessageSquare, ChevronLeft, ChevronRight, Trash2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Separator } from "@/components/ui/separator";
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/components/ui/alert-dialog";
import { useToast } from "@/hooks/use-toast";
import { apiRequest } from "@/lib/queryClient";


export default function Conversation() {
  const [conversations, setConversations] = useState<[]>([]);
  const [selectedConversationId, setSelectedConversationId] = useState<string>("");
  const [selectedConversation, setSelectedConversation] = useState<[]>([]);
  const [inputValue, setInputValue] = useState("");
  const [isTyping, setIsTyping] = useState(false);
  const [isSidebarCollapsed, setIsSidebarCollapsed] = useState(false);
  const [deleteConfirmId, setDeleteConfirmId] = useState<string | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const { toast } = useToast();

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  // get conversations
  useEffect(() => {
    const user_id = JSON.parse(localStorage.getItem("user")).id;
    const conversations = apiRequest("GET",
      `${import.meta.env.VITE_API_BASE_URL}/api/query/query-session/user/${user_id}?distinct_conversation=true`)
    .then((res) => res.json()).then((data) => {
        setConversations(data);
        chooseConversation(data[0].conversation_id);
    }).catch((error) => {
        console.error("Error fetching conversation:", error);
    });
  }, []);

  // choose conversation
  const chooseConversation = async (conversationId) => {
    setSelectedConversation([]);
    setSelectedConversationId("");
    
    if (conversationId.startsWith("conv-")) {
      setSelectedConversationId(conversationId);
      setSelectedConversation([
        {
          conversation_id: conversationId,
          query: "",
          response: "",
          top_k: null,
          chunk_size: null,
          created_at: new Date().toISOString(),
          document_ids: []
        }
      ]);
      return;
    }

    try {
      const res = await apiRequest(
        "GET",
        `${import.meta.env.VITE_API_BASE_URL}/api/query/query-session/conversation/${conversationId}`
      );
      const data = await res.json();
      setSelectedConversation(data);
      setSelectedConversationId(conversationId);
    } catch (error) {
      console.error("Error fetching conversation:", error);
    }

    // setSelectedConversation(null)
    // const conversation = apiRequest("GET",
    //   `${import.meta.env.VITE_API_BASE_URL}/api/query/query-session/conversation/${conversationId}`)
    // .then((res) => res.json()).then((data) => {
    //     console.log(data);
    //     setSelectedConversation(data);
    // }).catch((error) => {
    //     console.error("Error fetching conversation:", error);
    // });
  }

  const refreshSelectedConversation = (conversationId) => {
    chooseConversation(conversationId);
  }

  useEffect(() => {
    scrollToBottom();
  }, [selectedConversation]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!inputValue.trim() || !selectedConversation) return;

    // optimistic UI
    const newUserMessage = {
      id: `temp-${Date.now()}`,
      query: inputValue,
      response: "...",
      created_at: new Date().toISOString()
    }

    // show new query immediately
    setSelectedConversation(prev => [...prev, newUserMessage]);
    setIsTyping(true);
    setInputValue("");

    const params = new URLSearchParams({
        query: inputValue,
        // top_k: data.topK,
        with_llm_response: true,
        user_id: JSON.parse(localStorage.getItem("user")).id,
        // model: data.model,
        conversation_id: selectedConversation[0].conversation_id
      });

      selectedConversation[0].document_ids?.forEach(id => {
        params.append("document_ids", id);
      });
      
      try{
        const res = await apiRequest("GET", `${import.meta.env.VITE_API_BASE_URL}/api/rag/query?${params.toString()}`);
        const response = await res.json();

        refreshSelectedConversation(selectedConversation[0].conversation_id);
      } catch (err) {
        console.error("Error submitting query: ", err);
      } finally {
        setIsTyping(false);
        scrollToBottom();
      }
  };

  const handleNewConversation = () => {
    const newConversationId = `conv-${Date.now()}`;

    setSelectedConversation([]);
    setSelectedConversationId("");

    const newConversationMessages = [{
      conversation_id: newConversationId,
      // title: "New Converstation",
      query: "",
      response: "",
      created_at: new Date().toISOString()
    }]

    // add new conversation history to list on sidebar
    const newConversationPreview = {
      conversation_id: newConversationId,
      title: "New Conversation",
      created_at: new Date().toISOString(),
      query: ""
    }

    setConversations((prev) => [newConversationPreview, ...prev]);
    setSelectedConversationId(newConversationId);
    setSelectedConversation(newConversationMessages);
  };

  const handleDeleteConversation = (id: string) => {
    const deletedConv = conversations.find((c) => c.id === id);
    setConversations((prev) => prev.filter((conv) => conv.id !== id));
    
    if (selectedConversationId === id) {
      const remaining = conversations.filter((conv) => conv.id !== id);
      if (remaining.length > 0) {
        setSelectedConversationId(remaining[0].id);
      }
    }
    
    setDeleteConfirmId(null);
    toast({
      title: "Conversation deleted",
      description: `"${deletedConv?.title}" has been removed.`,
    });
  };

  const formatTime = (date: Date) => {
    return date.toLocaleTimeString("en-US", {
      hour: "2-digit",
      minute: "2-digit",
    });
  };

  const formatConversationTime = (date: Date) => {
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMs / 3600000);
    const diffDays = Math.floor(diffMs / 86400000);

    if (diffMins < 60) return `${diffMins}m ago`;
    if (diffHours < 24) return `${diffHours}h ago`;
    if (diffDays < 7) return `${diffDays}d ago`;
    return date.toLocaleDateString();
  };

  return (
    // <div className="flex h-full gap-6" data-testid="page-conversation">
    <div className="flex h-screen overflow-hidden gap-6" data-testid="page-conversation">
      <div
        // className={`flex flex-col gap-4 transition-all duration-300 ${
        //   isSidebarCollapsed ? "w-16" : "w-80"
        // }`}
        className={`flex flex-col gap-4 transition-all duration-300 overflow-y-auto ${
          isSidebarCollapsed ? "w-16" : "w-85"
        }`}
      >
        <div className="flex items-center justify-between gap-2">
          {!isSidebarCollapsed && (
            <div className="flex-1">
              <h2 className="text-lg font-semibold">Conversations</h2>
              <p className="text-xs text-muted-foreground">
                {conversations.length} total
              </p>
            </div>
          )}
          <div className="flex items-center gap-2">
            {!isSidebarCollapsed && (
              <Button
                size="icon"
                variant="default"
                onClick={handleNewConversation}
                data-testid="button-new-conversation"
              >
                <Plus className="w-4 h-4" />
              </Button>
            )}
            <Button
              size="icon"
              variant="ghost"
              onClick={() => setIsSidebarCollapsed(!isSidebarCollapsed)}
              data-testid="button-toggle-sidebar"
            >
              {isSidebarCollapsed ? (
                <ChevronRight className="w-4 h-4" />
              ) : (
                <ChevronLeft className="w-4 h-4" />
              )}
            </Button>
          </div>
        </div>

        {!isSidebarCollapsed && (
          <ScrollArea className="flex-1" data-testid="conversation-list">
            <div className="space-y-2">
              {[...conversations]
                // .sort((a, b) => b.created_at - a.created_at)
                .map((conv) => (
                  <Card
                    key={conv.id}
                    className={`group p-4 cursor-pointer transition-all hover-elevate ${
                      selectedConversationId === conv.conversation_id
                        ? "bg-accent border-accent-border"
                        : ""
                    }`}
                    // onClick={() => setSelectedConversationId(conv.conversation_id)}
                    onClick={() => chooseConversation(conv.conversation_id)}
                    data-testid={`conversation-item-${conv.id}`}
                  >
                    <div className="flex items-start gap-3">
                      <div className="flex-shrink-0 mt-1">
                        <div className="w-8 h-8 rounded-full bg-primary/10 flex items-center justify-center">
                          <MessageSquare className="w-4 h-4 text-primary" />
                        </div>
                      </div>
                      <div className="flex-1 min-w-0">
                        <div className="flex items-start justify-between gap-2 mb-1">
                          <h3
                            className="font-medium text-sm truncate"
                            data-testid={`text-conversation-title-${conv.id}`}
                          >
                            {conv.title}
                          </h3>
                          <div className="flex items-center gap-2 flex-shrink-0">
                            <span className="text-xs text-muted-foreground">
                              {formatConversationTime(new Date(conv.created_at))}
                            </span>
                            <Button
                              size="icon"
                              variant="ghost"
                              className="h-6 w-6 opacity-0 group-hover:opacity-100 hover:bg-destructive/10 hover:text-destructive"
                              onClick={(e) => {
                                e.stopPropagation();
                                setDeleteConfirmId(conv.id);
                              }}
                              data-testid={`button-delete-${conv.id}`}
                            >
                              <Trash2 className="w-3 h-3" />
                            </Button>
                          </div>
                        </div>
                        <p
                          className="text-xs text-muted-foreground line-clamp-2"
                          data-testid={`text-conversation-preview-${conv.id}`}
                        >
                          {conv.query}
                        </p>
                      </div>
                    </div>
                  </Card>
                ))}
            </div>
          </ScrollArea>
        )}
      </div>

      {!isSidebarCollapsed && <Separator orientation="vertical" className="h-auto" />}

      <div className="flex-1 flex flex-col min-w-0 overflow-hidden">
        {selectedConversation ? (
          <>
            <div className="border-b px-6 py-4">
              <div className="flex items-center justify-between">
                <div>
                  <h1 className="text-2xl font-semibold" data-testid="text-conversation-title">
                    {/* {selectedConversation.title} */}
                    title
                  </h1>
                  <p className="text-sm text-muted-foreground mt-1">
                    {selectedConversation.length} messages
                  </p>
                </div>
              </div>
            </div>

            <ScrollArea className="flex-1 px-6 overlow-y-auto" data-testid="scroll-area-messages">
              <div className="py-6 space-y-6 max-w-4xl mx-auto">
                {selectedConversation.length === 0 || selectedConversation[0].conversation_id.startsWith("conv-") ? (
                  <div className="text-center py-12">
                    <div className="w-16 h-16 rounded-full bg-muted mx-auto mb-4 flex items-center justify-center">
                      <MessageSquare className="w-8 h-8 text-muted-foreground" />
                    </div>
                    <h3 className="text-lg font-medium mb-2">Start a conversation</h3>
                    <p className="text-sm text-muted-foreground">
                      Ask a question about your documents to get started
                    </p>
                  </div>
                ) : (
                  selectedConversation.map((turn) => (
                    <>
                    {/* user query */}
                    <div
                        key={turn.id}
                        className="flex gap-4 justify-end"
                        data-testid={`message-${turn.id}`}
                    >
                        <div className="flex-1 max-w-2xl flex justify-end">
                            <Card className="p-4 bg-primary text-primary-foreground">
                                <div className="space-y-2">
                                    <p className="text-sm leading-relaxed whitespace-pre-wrap" 
                                        data-testid={`text-message-content-${turn.id}`}
                                    >
                                        {turn.query}
                                    </p>

                                    <p
                                        className={`text-xs "text-primary-foreground/70" mt-2`}
                                        data-testid={`text-timestamp-${turn.id}`}
                                    >
                                        {formatTime(new Date(turn.created_at))}
                                    </p>
                                </div>
                            </Card>
                        </div>

                        <div className="flex-shrink-0">
                            <div className="w-8 h-8 rounded-full bg-muted flex items-center justify-center">
                            <User className="w-4 h-4" />
                            </div>
                        </div>
                    </div>
                    {/* end of user query */}
                        {turn.response != "..." && (
                          <div
                              key={turn.id}
                              className='flex gap-4 "justify-start"'
                              data-testid={`message-${turn.id}`}
                          >
                          <div className="flex-shrink-0">
                              <div className="w-8 h-8 rounded-full bg-primary flex items-center justify-center">
                              <Bot className="w-4 h-4 text-primary-foreground" />
                              </div>
                          </div>
                          <div className="flex-1 max-w-2xl">
                            <Card className="p-4">
                                <div className="space-y-2">
                                    <p className="text-sm leading-relaxed whitespace-pre-wrap" 
                                        data-testid={`text-message-content-${turn.id}`}
                                    >
                                        {turn.response}
                                    </p>

                                    {turn.retrieved_chunks && turn.retrieved_chunks.length > 0 && (
                                        <div className="mt-3 pt-3 border-t space-y-2">
                                        <p className="text-xs font-medium text-muted-foreground">
                                            Retrieved Chunks:
                                        </p>
                                        <div className="flex flex-wrap gap-2">
                                            {turn.retrieved_chunks[0].map((chunk, idx) => (
                                            <Badge
                                                key={idx}
                                                variant="secondary"
                                                className="text-xs"
                                                data-testid={`badge-chunk-${turn.id}-${idx}`}
                                            >
                                                {chunk.document_name} ({(chunk.similarity_score * 100).toFixed(0)}%)
                                            </Badge>
                                            ))}
                                        </div>
                                        </div>
                                    )}
                                    <p
                                        className={`text-xs "text-muted-foreground" mt-2`}
                                        data-testid={`text-timestamp-${turn.id}`}
                                    >
                                        {formatTime(new Date(turn.created_at))}
                                    </p>
                                </div>
                            </Card>
                          </div>
                          </div>
                        )}
                    </>
                  ))
                )}

                {isTyping && (
                  <div className="flex gap-4" data-testid="typing-indicator">
                    <div className="flex-shrink-0">
                      <div className="w-8 h-8 rounded-full bg-primary flex items-center justify-center">
                        <Bot className="w-4 h-4 text-primary-foreground" />
                      </div>
                    </div>
                    <Card className="p-4">
                      <div className="flex gap-1">
                        <div className="w-2 h-2 bg-muted-foreground/50 rounded-full animate-bounce" />
                        <div className="w-2 h-2 bg-muted-foreground/50 rounded-full animate-bounce [animation-delay:0.2s]" />
                        <div className="w-2 h-2 bg-muted-foreground/50 rounded-full animate-bounce [animation-delay:0.4s]" />
                      </div>
                    </Card>
                  </div>
                )}
                <div ref={messagesEndRef} />
              </div>
            </ScrollArea>

            <div className="border-t p-6">
              <form onSubmit={handleSubmit} className="max-w-4xl mx-auto">
                <div className="flex items-end gap-3">
                  <Textarea
                    value={inputValue}
                    onChange={(e) => setInputValue(e.target.value)}
                    placeholder="Ask a question about your documents..."
                    className="min-h-[60px] resize-none"
                    onKeyDown={(e) => {
                      if (e.key === "Enter" && !e.shiftKey) {
                        e.preventDefault();
                        handleSubmit(e);
                      }
                    }}
                    data-testid="textarea-conversation-input"
                  />
                  <Button
                    type="submit"
                    size="icon"
                    className="flex-shrink-0"
                    disabled={!inputValue.trim() || isTyping}
                    data-testid="button-send-message"
                  >
                    <Send className="w-5 h-5" />
                  </Button>
                </div>
                <p className="text-xs text-muted-foreground mt-2">
                  Press Enter to send, Shift + Enter for new line
                </p>
              </form>
            </div>
          </>
        ) : (
          <div className="flex items-center justify-center h-full">
            <div className="text-center">
              <MessageSquare className="w-16 h-16 text-muted-foreground mx-auto mb-4" />
              <h3 className="text-lg font-medium mb-2">No conversation selected</h3>
              <p className="text-sm text-muted-foreground">
                Select a conversation from the list to view messages
              </p>
            </div>
          </div>
        )}
      </div>

      <AlertDialog open={deleteConfirmId !== null} onOpenChange={() => setDeleteConfirmId(null)}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Delete Conversation</AlertDialogTitle>
            <AlertDialogDescription>
              Are you sure you want to delete this conversation? This action cannot be undone and all
              messages will be permanently removed.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel data-testid="button-cancel-delete">Cancel</AlertDialogCancel>
            <AlertDialogAction
              onClick={() => deleteConfirmId && handleDeleteConversation(deleteConfirmId)}
              className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
              data-testid="button-confirm-delete"
            >
              Delete
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  );
}
