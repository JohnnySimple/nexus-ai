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

interface Message {
  id: string;
  type: "user" | "assistant";
  content: string;
  timestamp: Date;
  chunks?: Array<{ filename: string; similarity: number }>;
}

interface Conversation {
  id: string;
  title: string;
  lastMessage: string;
  timestamp: Date;
  messages: Message[];
}

const DUMMY_CONVERSATIONS: Conversation[] = [
  {
    id: "conv-1",
    title: "Enterprise Security Policy",
    lastMessage: "The complete onboarding timeline typically spans 90 days...",
    timestamp: new Date(Date.now() - 1180000),
    messages: [
      {
        id: "1",
        type: "user",
        content: "What are the key features of our enterprise security policy?",
        timestamp: new Date(Date.now() - 3600000),
      },
      {
        id: "2",
        type: "assistant",
        content: "Based on the enterprise security policy documents, the key features include:\n\n1. Multi-factor authentication (MFA) requirement for all user accounts\n2. Data encryption at rest and in transit using AES-256\n3. Regular security audits conducted quarterly\n4. Role-based access control (RBAC) implementation\n5. Automated threat detection and response systems\n6. Employee security training programs\n\nThese policies ensure comprehensive protection of company assets and customer data.",
        timestamp: new Date(Date.now() - 3580000),
        chunks: [
          { filename: "security-policy-2024.pdf", similarity: 0.92 },
          { filename: "rbac-guidelines.md", similarity: 0.87 },
          { filename: "encryption-standards.pdf", similarity: 0.85 },
        ],
      },
      {
        id: "3",
        type: "user",
        content: "How often are security audits performed?",
        timestamp: new Date(Date.now() - 2400000),
      },
      {
        id: "4",
        type: "assistant",
        content: "According to the security policy documentation, security audits are performed quarterly (every 3 months). Additionally:\n\n- Internal security reviews are conducted monthly\n- External penetration testing is performed bi-annually\n- Compliance audits for regulatory requirements (SOC 2, ISO 27001) are done annually\n- Continuous automated security scanning runs 24/7\n\nThis multi-layered approach ensures ongoing security posture assessment.",
        timestamp: new Date(Date.now() - 2380000),
        chunks: [
          { filename: "security-policy-2024.pdf", similarity: 0.94 },
          { filename: "audit-schedule.md", similarity: 0.89 },
        ],
      },
      {
        id: "5",
        type: "user",
        content: "What is the process for onboarding new employees?",
        timestamp: new Date(Date.now() - 1200000),
      },
      {
        id: "6",
        type: "assistant",
        content: "The employee onboarding process consists of several stages:\n\n**Pre-boarding (Before Day 1):**\n- IT equipment setup and provisioning\n- Account creation and access credentials\n- Background check completion\n- Paperwork and documentation submission\n\n**Day 1 Orientation:**\n- Welcome session with HR\n- Company culture and values presentation\n- Security awareness training\n- Badge and access card issuance\n\n**First Week:**\n- Department-specific training\n- Mentor assignment\n- Tool and system training\n- Introduction to team members\n\n**First Month:**\n- Regular check-ins with manager\n- Goal setting and expectations alignment\n- Continued learning and development\n\nThe complete onboarding timeline typically spans 90 days for full integration.",
        timestamp: new Date(Date.now() - 1180000),
        chunks: [
          { filename: "hr-onboarding-guide.pdf", similarity: 0.91 },
          { filename: "employee-handbook.pdf", similarity: 0.88 },
          { filename: "training-materials.md", similarity: 0.82 },
        ],
      },
    ],
  },
  {
    id: "conv-2",
    title: "Product Roadmap Q1 2025",
    lastMessage: "The roadmap prioritizes AI-powered features and mobile optimization.",
    timestamp: new Date(Date.now() - 7200000),
    messages: [
      {
        id: "7",
        type: "user",
        content: "What are the main priorities in our Q1 2025 product roadmap?",
        timestamp: new Date(Date.now() - 8400000),
      },
      {
        id: "8",
        type: "assistant",
        content: "The Q1 2025 product roadmap focuses on three main priorities:\n\n**1. AI-Powered Features (40% of resources)**\n- Advanced natural language search\n- Intelligent document categorization\n- Automated workflow recommendations\n- Predictive analytics dashboard\n\n**2. Mobile Optimization (30% of resources)**\n- Native iOS and Android apps\n- Responsive design improvements\n- Offline mode functionality\n- Push notification system\n\n**3. Enterprise Integration (30% of resources)**\n- SSO with major providers (Okta, Azure AD)\n- API rate limiting and monitoring\n- Advanced audit logging\n- Custom branding options\n\nTarget launch: End of Q1 with phased rollout.",
        timestamp: new Date(Date.now() - 8380000),
        chunks: [
          { filename: "product-roadmap-2025.pdf", similarity: 0.95 },
          { filename: "engineering-priorities.md", similarity: 0.88 },
        ],
      },
      {
        id: "9",
        type: "user",
        content: "When will the mobile apps be available?",
        timestamp: new Date(Date.now() - 7300000),
      },
      {
        id: "10",
        type: "assistant",
        content: "The mobile app timeline is as follows:\n\n**Beta Release:** Mid-February 2025\n- Limited to internal team members\n- iOS and Android versions\n- Core features only\n\n**Public Beta:** Early March 2025\n- Available to select customers\n- Expanded feature set\n- Feedback collection period\n\n**General Availability:** Late March 2025\n- Full public release\n- Complete feature parity with web app\n- App Store and Google Play\n\nThe roadmap prioritizes AI-powered features and mobile optimization.",
        timestamp: new Date(Date.now() - 7200000),
        chunks: [
          { filename: "mobile-development-plan.pdf", similarity: 0.93 },
          { filename: "release-schedule.md", similarity: 0.86 },
        ],
      },
    ],
  },
  {
    id: "conv-3",
    title: "Data Privacy & GDPR Compliance",
    lastMessage: "We maintain full GDPR compliance through automated data handling...",
    timestamp: new Date(Date.now() - 86400000),
    messages: [
      {
        id: "11",
        type: "user",
        content: "How do we ensure GDPR compliance for customer data?",
        timestamp: new Date(Date.now() - 90000000),
      },
      {
        id: "12",
        type: "assistant",
        content: "Our GDPR compliance strategy includes multiple layers:\n\n**Data Protection Measures:**\n- End-to-end encryption for all personal data\n- Anonymization of analytics data\n- Strict access controls with audit trails\n- Regular security assessments\n\n**User Rights Implementation:**\n- Right to access: Self-service data export\n- Right to erasure: Automated deletion within 30 days\n- Right to portability: JSON/CSV export formats\n- Right to rectification: User profile editing\n\n**Organizational Practices:**\n- Data Protection Officer (DPO) appointment\n- Privacy Impact Assessments (PIAs) for new features\n- Third-party vendor compliance verification\n- Annual GDPR training for all employees\n\nWe maintain full GDPR compliance through automated data handling and regular audits.",
        timestamp: new Date(Date.now() - 86400000),
        chunks: [
          { filename: "gdpr-compliance-guide.pdf", similarity: 0.96 },
          { filename: "data-protection-policy.md", similarity: 0.91 },
          { filename: "privacy-procedures.pdf", similarity: 0.84 },
        ],
      },
    ],
  },
  {
    id: "conv-4",
    title: "Customer Support Best Practices",
    lastMessage: "Our average response time target is under 2 hours...",
    timestamp: new Date(Date.now() - 172800000),
    messages: [
      {
        id: "13",
        type: "user",
        content: "What are our customer support response time targets?",
        timestamp: new Date(Date.now() - 176400000),
      },
      {
        id: "14",
        type: "assistant",
        content: "Our customer support response time targets are:\n\n**Priority Tiers:**\n- Critical (P0): 30 minutes - System down, data loss\n- High (P1): 2 hours - Major feature broken, multiple users affected\n- Medium (P2): 8 hours - Minor feature issue, workaround available\n- Low (P3): 24 hours - Questions, feature requests, documentation\n\n**Channel-Specific SLAs:**\n- Live Chat: 5 minutes average response\n- Email: 4 hours first response\n- Phone: Immediate pickup during business hours\n- In-app messaging: 1 hour during business hours\n\n**Performance Metrics:**\n- Current average response: 1.8 hours\n- Customer satisfaction: 94%\n- First contact resolution: 78%\n- Escalation rate: 12%\n\nOur average response time target is under 2 hours across all priority levels.",
        timestamp: new Date(Date.now() - 172800000),
        chunks: [
          { filename: "support-sla.pdf", similarity: 0.94 },
          { filename: "customer-service-guidelines.md", similarity: 0.89 },
        ],
      },
    ],
  },
];

export default function Conversation() {
  const [conversations, setConversations] = useState<Conversation[]>([]);
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
  const chooseConversation = (conversationId) => {
    console.log(`convesation id: ${conversationId}`);
    setSelectedConversation(null)
    const conversation = apiRequest("GET",
      `${import.meta.env.VITE_API_BASE_URL}/api/query/query-session/conversation/${conversationId}`)
    .then((res) => res.json()).then((data) => {
        console.log(data);
        setSelectedConversation(data);
    }).catch((error) => {
        console.error("Error fetching conversation:", error);
    });
  }

  useEffect(() => {
    scrollToBottom();
  }, [selectedConversation]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!inputValue.trim() || !selectedConversation) return;

    const userMessage: Message = {
      id: String(Date.now()),
      type: "user",
      content: inputValue.trim(),
      timestamp: new Date(),
    };

    // setConversations((prev) =>
    //   prev.map((conv) =>
    //     conv.id === selectedConversationId
    //       ? { 
    //           ...conv, 
    //           messages: [...conv.messages, userMessage],
    //           lastMessage: userMessage.content,
    //           timestamp: userMessage.timestamp,
    //         }
    //       : conv
    //   )
    // );
    // setInputValue("");
    // setIsTyping(true);

    // setTimeout(() => {
    //   const assistantMessage: Message = {
    //     id: String(Date.now() + 1),
    //     type: "assistant",
    //     content: "This is a demo conversation page with dummy data. In a real implementation, this response would come from the RAG system based on your query and the relevant document chunks retrieved from the vector database.",
    //     timestamp: new Date(),
    //     chunks: [
    //       { filename: "sample-document.pdf", similarity: 0.85 },
    //       { filename: "example-guide.md", similarity: 0.78 },
    //     ],
    //   };
    //   setConversations((prev) =>
    //     prev.map((conv) =>
    //       conv.id === selectedConversationId
    //         ? { 
    //             ...conv, 
    //             messages: [...conv.messages, assistantMessage],
    //             lastMessage: assistantMessage.content,
    //             timestamp: assistantMessage.timestamp,
    //           }
    //         : conv
    //     )
    //   );
    //   setIsTyping(false);
    // }, 1500);
  };

  const handleNewConversation = () => {
    // const newConv: Conversation = {
    //   id: `conv-${Date.now()}`,
    //   title: "New Conversation",
    //   lastMessage: "Start a new conversation...",
    //   timestamp: new Date(),
    //   messages: [],
    // };
    // setConversations([newConv, ...conversations]);
    // setSelectedConversationId(newConv.id);
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
                {selectedConversation.length === 0 ? (
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
                    // <div
                    //   key={message.id}
                    //   className={`flex gap-4 ${
                    //     message.type === "user" ? "justify-end" : "justify-start"
                    //   }`}
                    //   data-testid={`message-${message.id}`}
                    // >
                    //   {message.type === "assistant" && (
                    //     <div className="flex-shrink-0">
                    //       <div className="w-8 h-8 rounded-full bg-primary flex items-center justify-center">
                    //         <Bot className="w-4 h-4 text-primary-foreground" />
                    //       </div>
                    //     </div>
                    //   )}

                    //   <div
                    //     className={`flex-1 max-w-2xl ${
                    //       message.type === "user" ? "flex justify-end" : ""
                    //     }`}
                    //   >
                    //     <Card
                    //       className={`p-4 ${
                    //         message.type === "user"
                    //           ? "bg-primary text-primary-foreground"
                    //           : ""
                    //       }`}
                    //     >
                    //       <div className="space-y-2">
                    //         <p
                    //           className="text-sm leading-relaxed whitespace-pre-wrap"
                    //           data-testid={`text-message-content-${message.id}`}
                    //         >
                    //           {message.content}
                    //         </p>

                    //         {message.chunks && message.chunks.length > 0 && (
                    //           <div className="mt-3 pt-3 border-t space-y-2">
                    //             <p className="text-xs font-medium text-muted-foreground">
                    //               Retrieved Chunks:
                    //             </p>
                    //             <div className="flex flex-wrap gap-2">
                    //               {message.chunks.map((chunk, idx) => (
                    //                 <Badge
                    //                   key={idx}
                    //                   variant="secondary"
                    //                   className="text-xs"
                    //                   data-testid={`badge-chunk-${message.id}-${idx}`}
                    //                 >
                    //                   {chunk.filename} ({(chunk.similarity * 100).toFixed(0)}%)
                    //                 </Badge>
                    //               ))}
                    //             </div>
                    //           </div>
                    //         )}

                    //         <p
                    //           className={`text-xs ${
                    //             message.type === "user"
                    //               ? "text-primary-foreground/70"
                    //               : "text-muted-foreground"
                    //           } mt-2`}
                    //           data-testid={`text-timestamp-${message.id}`}
                    //         >
                    //           {formatTime(message.timestamp)}
                    //         </p>
                    //       </div>
                    //     </Card>
                    //   </div>

                    //   {message.type === "user" && (
                    //     <div className="flex-shrink-0">
                    //       <div className="w-8 h-8 rounded-full bg-muted flex items-center justify-center">
                    //         <User className="w-4 h-4" />
                    //       </div>
                    //     </div>
                    //   )}
                    // </div>
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
