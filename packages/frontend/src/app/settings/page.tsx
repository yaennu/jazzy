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
    const [loading, setLoading] = useState(false);
    const [message, setMessage] = useState("");
    const [deleting, setDeleting] = useState(false);
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
        };
        getUser();
    }, [supabase]);

    const handleSave = async (e: React.FormEvent) => {
        e.preventDefault();
        setMessage("");
        setLoading(true);

        if (user) {
            const { error } = await supabase
                .from("users")
                .update({ newsletter_frequency: frequency })
                .eq("user_id", user.id);

            if (error) {
                setMessage(error.message);
            } else {
                setMessage("Settings saved!");
            }
        }
        setLoading(false);
    };

    const handleLogout = async () => {
        await supabase.auth.signOut();
        router.push("/login");
        router.refresh();
    };

    return (
        <div className="flex items-center justify-center min-h-screen">
            <div className="w-full max-w-md p-8 space-y-8 bg-white rounded-lg shadow-md">
                <div className="text-center">
                    <h1 className="text-3xl font-bold">Newsletter Settings</h1>
                    <p className="mt-2 text-sm text-gray-600">Choose how often you want to receive the newsletter.</p>
                </div>
                <form onSubmit={handleSave} className="space-y-6">
                    {message && (
                        <p className="text-sm text-center text-gray-600">{message}</p>
                    )}
                    <RadioGroup value={frequency} onValueChange={setFrequency}>
                        <div className="flex items-center space-x-2">
                            <RadioGroupItem value="daily" id="daily" />
                            <Label htmlFor="daily">Daily</Label>
                        </div>
                        <div className="flex items-center space-x-2">
                            <RadioGroupItem value="weekly" id="weekly" />
                            <Label htmlFor="weekly">Weekly</Label>
                        </div>
                        <div className="flex items-center space-x-2">
                            <RadioGroupItem value="monthly" id="monthly" />
                            <Label htmlFor="monthly">Monthly</Label>
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
                    <h2 className="text-sm font-semibold text-red-600">Danger Zone</h2>
                    <p className="mt-1 text-sm text-gray-500">
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
