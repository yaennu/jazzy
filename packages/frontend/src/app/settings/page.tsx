"use client";

import { useState, useEffect } from "react";
import { Label } from "@/components/ui/label";
import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group";
import { Button } from "@/components/ui/button";
import {
    AlertDialog,
    AlertDialogAction,
    AlertDialogCancel,
    AlertDialogContent,
    AlertDialogDescription,
    AlertDialogFooter,
    AlertDialogHeader,
    AlertDialogTitle,
    AlertDialogTrigger,
} from "@/components/ui/alert-dialog";
import { createClient } from "@/lib/supabase/client";
import { useRouter } from "next/navigation";

export default function SettingsPage() {
    const [frequency, setFrequency] = useState("weekly");
    const [user, setUser] = useState<{ id: string } | null>(null);
    const [initialLoading, setInitialLoading] = useState(true);
    const [loading, setLoading] = useState(false);
    const [message, setMessage] = useState("");
    const [isError, setIsError] = useState(false);
    const [deleting, setDeleting] = useState(false);
    const [exporting, setExporting] = useState(false);
    const router = useRouter();
    const supabase = createClient();

    useEffect(() => {
        const getUser = async () => {
            const { data: { user } } = await supabase.auth.getUser();
            if (user) {
                setUser(user);
                const { data } = await supabase
                    .from("users")
                    .select("newsletter_frequency")
                    .eq("user_id", user.id)
                    .single();
                if (data) {
                    setFrequency(data.newsletter_frequency);
                }
            }
            setInitialLoading(false);
        };
        getUser();
    }, [supabase]);

    const handleSave = async (e: React.FormEvent) => {
        e.preventDefault();
        setMessage("");
        setIsError(false);
        setLoading(true);

        if (user) {
            const { error } = await supabase
                .from("users")
                .update({ newsletter_frequency: frequency })
                .eq("user_id", user.id);

            if (error) {
                setMessage(error.message);
                setIsError(true);
            } else {
                setMessage("Settings saved!");
                setIsError(false);
            }
        }
        setLoading(false);
    };

    const handleExportData = async () => {
        if (!user) return;
        setExporting(true);

        const { data: userData } = await supabase
            .from("users")
            .select("email, name, subscription_status, newsletter_frequency, created_at")
            .eq("user_id", user.id)
            .single();

        const { data: recommendations } = await supabase
            .from("recommendations")
            .select("sent_date, albums(title, artist, release_year)")
            .eq("user_id", user.id)
            .order("sent_date", { ascending: false });

        const exportData = {
            exported_at: new Date().toISOString(),
            account: userData,
            recommendations: recommendations ?? [],
        };

        const blob = new Blob([JSON.stringify(exportData, null, 2)], { type: "application/json" });
        const url = URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url;
        a.download = "jazzy-my-data.json";
        a.click();
        URL.revokeObjectURL(url);
        setExporting(false);
    };

    const handleLogout = async () => {
        await supabase.auth.signOut();
        router.push("/login");
        router.refresh();
    };

    if (initialLoading) {
        return (
            <div className="flex items-center justify-center min-h-screen">
                <div className="w-full max-w-md p-8 space-y-8 bg-card rounded-lg shadow-md">
                    <div className="space-y-2">
                        <div className="h-8 w-48 mx-auto bg-gray-200 rounded animate-pulse" />
                        <div className="h-4 w-64 mx-auto bg-gray-200 rounded animate-pulse" />
                    </div>
                    <div className="space-y-4">
                        {[1, 2, 3].map((i) => (
                            <div key={i} className="flex items-center space-x-2">
                                <div className="h-4 w-4 bg-gray-200 rounded-full animate-pulse" />
                                <div className="h-4 w-20 bg-gray-200 rounded animate-pulse" />
                            </div>
                        ))}
                    </div>
                    <div className="h-10 w-full bg-gray-200 rounded animate-pulse" />
                    <div className="h-10 w-full bg-gray-200 rounded animate-pulse" />
                </div>
            </div>
        );
    }

    return (
        <div className="flex items-center justify-center min-h-screen">
            <div className="w-full max-w-md p-8 space-y-8 bg-card rounded-lg shadow-md">
                <div className="text-center">
                    <h1 className="text-3xl font-bold">Newsletter Settings</h1>
                    <p className="mt-2 text-sm text-muted-foreground">Choose how often you want to receive the newsletter.</p>
                </div>
                <form onSubmit={handleSave} className="space-y-6">
                    {message && (
                        <p className={`text-sm text-center ${isError ? "text-red-600" : "text-green-600"}`}>{message}</p>
                    )}
                    <RadioGroup value={frequency} onValueChange={setFrequency}>
                        <div>
                            <div className="flex items-center space-x-2">
                                <RadioGroupItem value="daily" id="daily" />
                                <Label htmlFor="daily">Daily</Label>
                            </div>
                            <p className="text-xs text-muted-foreground ml-6 mt-0.5">Every day at 6:00</p>
                        </div>
                        <div>
                            <div className="flex items-center space-x-2">
                                <RadioGroupItem value="weekly" id="weekly" />
                                <Label htmlFor="weekly">Weekly</Label>
                            </div>
                            <p className="text-xs text-muted-foreground ml-6 mt-0.5">Every Monday at 6:00</p>
                        </div>
                        <div>
                            <div className="flex items-center space-x-2">
                                <RadioGroupItem value="monthly" id="monthly" />
                                <Label htmlFor="monthly">Monthly</Label>
                            </div>
                            <p className="text-xs text-muted-foreground ml-6 mt-0.5">1st of each month at 6:00</p>
                        </div>
                    </RadioGroup>
                    <Button type="submit" className="w-full" disabled={loading}>
                        {loading ? "Saving..." : "Save Settings"}
                    </Button>
                </form>
                <Button variant="outline" className="w-full" onClick={handleLogout}>
                    Logout
                </Button>
                <div className="border-t pt-6">
                    <h2 className="text-sm font-semibold text-foreground">Your Data</h2>
                    <p className="mt-1 text-sm text-muted-foreground">
                        Download a copy of all your personal data as a JSON file.
                    </p>
                    <Button variant="outline" className="w-full mt-3" onClick={handleExportData} disabled={exporting}>
                        {exporting ? "Exporting..." : "Export My Data"}
                    </Button>
                </div>
                <div className="border-t pt-6">
                    <h2 className="text-sm font-semibold text-red-600">Danger Zone</h2>
                    <p className="mt-1 text-sm text-muted-foreground">
                        Permanently delete your account and all associated data.
                    </p>
                    <AlertDialog>
                        <AlertDialogTrigger asChild>
                            <Button variant="destructive" className="w-full mt-3">
                                Delete Account
                            </Button>
                        </AlertDialogTrigger>
                        <AlertDialogContent>
                            <AlertDialogHeader>
                                <AlertDialogTitle>Delete your account?</AlertDialogTitle>
                                <AlertDialogDescription>
                                    This action cannot be undone. Your account, preferences, and recommendation history will be permanently deleted.
                                </AlertDialogDescription>
                            </AlertDialogHeader>
                            <AlertDialogFooter>
                                <AlertDialogCancel>Cancel</AlertDialogCancel>
                                <AlertDialogAction
                                    variant="destructive"
                                    disabled={deleting}
                                    onClick={async (e) => {
                                        e.preventDefault();
                                        setDeleting(true);
                                        const { error } = await supabase.rpc("delete_account");
                                        if (error) {
                                            setMessage("Failed to delete account. Please try again.");
                                            setIsError(true);
                                            setDeleting(false);
                                            return;
                                        }
                                        await supabase.auth.signOut();
                                        router.push("/login");
                                        router.refresh();
                                    }}
                                >
                                    {deleting ? "Deleting..." : "Delete Account"}
                                </AlertDialogAction>
                            </AlertDialogFooter>
                        </AlertDialogContent>
                    </AlertDialog>
                </div>
            </div>
        </div>
    );
}
