import { useEffect, useState } from "react";
import { Form, FormControl, FormField, FormItem, FormLabel, FormMessage } from "@/components/ui/form";
import { Checkbox } from "@/components/ui/checkbox";
import { Separator } from "@/components/ui/separator";
import { Folder, FileText } from "lucide-react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { queryFormSchema, type QueryFormData } from "@shared/schema";
import { apiRequest } from "@/lib/queryClient";


export default function DocumentGroup({onDataChange}: {onDataChange?: (data) => void}) {

    const [groups, setGroups] = useState<[]>([]);
    const [documents, setDocuments] = useState<Document[]>([]);
    const [settings, setSettings] = useState<{}>({});

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

    // get document groups
    useEffect(() => {
        const groups = apiRequest("GET", `${import.meta.env.VITE_API_BASE_URL}/api/documents/group`)
        .then((res) => res.json()).then((data) => {
            setGroups(data);
        }).catch((error) => {
            console.error("Error fetching document groups:", error);
        });
    }, []);

    // get documents
    useEffect(() => {
    const documents = apiRequest("GET", `${import.meta.env.VITE_API_BASE_URL}/api/rag/documents`)
        .then((res) => res.json()).then((data) => {
        setDocuments(data);
        }).catch((error) => {
        console.error("Error fetching documents:", error);
        });
    }, []);



    // notify parent when form data changes
    useEffect(() => {
        const subscription = form.watch((value) => {
            onDataChange?.(value);
        });
        return () => subscription.unsubscribe();
    }, [form.watch, onDataChange]);

    return (
        <>
            <Form {...form}>
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
                            {/* <div className="flex items-center space-x-2">
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
                            </div> */}
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
                        {/* <div className="flex items-center space-x-2">
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
                        </div> */}
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
                
            </Form>
            
        </>
    );
}