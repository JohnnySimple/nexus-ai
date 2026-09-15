import { Home, FileText, Database, Search, MessageSquare, Settings, BarChart3, Shield, LogOut } from "lucide-react";
import { Link, useLocation } from "wouter";
import { useQuery } from "@tanstack/react-query";
import {
  Sidebar,
  SidebarContent,
  SidebarGroup,
  SidebarGroupContent,
  SidebarGroupLabel,
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
  SidebarHeader,
  SidebarFooter,
} from "@/components/ui/sidebar";

const menuItems = [
  {
    title: "Dashboard",
    url: "/",
    icon: Home,
  },
  {
    title: "Documents",
    url: "/documents",
    icon: FileText,
  },
  {
    title: "Vector Store",
    url: "/embeddings",
    icon: Database,
  },
  {
    title: "Query Interface",
    url: "/query",
    icon: Search,
  },
  {
    title: "Conversation",
    url: "/conversation",
    icon: MessageSquare,
  },
  {
    title: "Analytics",
    url: "/analytics",
    icon: BarChart3,
  },
  {
    title: "Settings",
    url: "/settings",
    icon: Settings,
  },
];

const adminMenuItem = {
  title: "Admin",
  url: "/admin",
  icon: Shield,
};

type User = {
  id: string;
  email: string;
  name: string;
  role: string;
};

export function AppSidebar() {
  const [location, setLocation] = useLocation();
  
  const { data: currentUser } = useQuery<User>({
    queryKey: ["/api/auth/me"],
  });

  const isAdmin = currentUser?.role === "admin";
  const displayMenuItems = isAdmin ? [...menuItems, adminMenuItem] : menuItems;

  const logout = () => {
    localStorage.removeItem("auth_token");
    localStorage.removeItem("user");
    setLocation("/login");
  }

  return (
    <Sidebar>
      <SidebarHeader className="border-b border-sidebar-border p-6">
        <div className="flex items-center gap-2">
          <div className="flex h-8 w-8 items-center justify-center rounded-md bg-primary">
            <Database className="h-5 w-5 text-primary-foreground" />
          </div>
          <div>
            <h2 className="text-lg font-semibold tracking-tight">Nexus RAG</h2>
            <p className="text-xs text-muted-foreground">Enterprise RAG System</p>
          </div>
        </div>
      </SidebarHeader>
      <SidebarContent>
        <SidebarGroup>
          <SidebarGroupLabel>Navigation</SidebarGroupLabel>
          <SidebarGroupContent>
            <SidebarMenu>
              {displayMenuItems.map((item) => (
                <SidebarMenuItem key={item.title}>
                  <SidebarMenuButton
                    asChild
                    isActive={location === item.url}
                    data-testid={`nav-${item.title.toLowerCase().replace(/\s+/g, '-')}`}
                  >
                    <Link href={item.url}>
                      <item.icon className="h-4 w-4" />
                      <span>{item.title}</span>
                    </Link>
                  </SidebarMenuButton>
                </SidebarMenuItem>
              ))}
              <SidebarMenuItem key="">
                <SidebarMenuButton
                  asChild
                >
                  <Link href="" onClick={logout}>
                    <LogOut className="h-4 w-4" />
                    <span>Logout</span>
                  </Link>
                </SidebarMenuButton>
              </SidebarMenuItem>

            </SidebarMenu>
          </SidebarGroupContent>
        </SidebarGroup>
      </SidebarContent>
      <SidebarFooter className="border-t border-sidebar-border p-4">
        <div className="text-xs text-muted-foreground">
          v1.0.0
        </div>
      </SidebarFooter>
    </Sidebar>
  );
}
