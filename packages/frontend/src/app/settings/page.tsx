"use client";

import { useState, useEffect } from "react";
import { Label } from "../../components/ui/label";
import { RadioGroup, RadioGroupItem } from "../../components/ui/radio-group";
import { Button } from "../../components/ui/button";
import { supabase } from "../../lib/supabase";

export default function SettingsPage() {
    const [frequency, setFrequency] = useState("weekly");
    const [user, setUser] = useState<any>(null);

    useEffect(() => {
        const getUser = async () => {
            const { data: { user } } = await supabase.auth.getUser();
            if (user) {
                setUser(user);
                const { data, error } = await supabase
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
    }, []);

    const handleSave = async (e: React.FormEvent) => {
        e.preventDefault();
        if (user) {
            const { error } = await supabase
                .from("users")
                .update({ newsletter_frequency: frequency })
                .eq("user_id", user.id);

            if (error) {
                alert(error.message);
            } else {
                alert("Settings saved!");
            }
        }
    };

    return (
        <div className="flex items-center justify-center min-h-screen">
            <div className="w-full max-w-md p-8 space-y-8 bg-white rounded-lg shadow-md">
                <div className="text-center">
                    <h1 className="text-3xl font-bold">Newsletter Settings</h1>
                    <p className="mt-2 text-sm text-gray-600">Choose how often you want to receive the newsletter.</p>
                </div>
                <form onSubmit={handleSave} className="space-y-6">
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
                    <Button type="submit" className="w-full">Save Settings</Button>
                </form>
            </div>
        </div>
    );
}
