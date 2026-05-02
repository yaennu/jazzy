import { createClient } from "@/lib/supabase/server";
import Link from "next/link";

export default async function UnsubscribePage({
    searchParams,
}: {
    searchParams: Promise<{ token?: string }>;
}) {
    const { token } = await searchParams;
    let message = "";
    let success = false;

    if (!token) {
        message = "Invalid unsubscribe link.";
    } else {
        const supabase = await createClient();

        const { data: result, error } = await supabase.rpc(
            "unsubscribe_by_token",
            { p_token: token }
        );

        if (error || result === "invalid_token") {
            message = "Invalid unsubscribe link.";
        } else if (result === "already_unsubscribed") {
            message = "You are already unsubscribed.";
            success = true;
        } else {
            message = "You have been unsubscribed from Jazzy recommendations.";
            success = true;
        }
    }

    return (
        <div className="flex items-center justify-center min-h-screen">
            <div className="w-full max-w-md p-8 space-y-8 bg-card rounded-lg shadow-md">
                <div className="text-center">
                    <h1 className="text-3xl font-bold">
                        {success ? "Unsubscribed" : "Error"}
                    </h1>
                    <p className="mt-4 text-sm text-muted-foreground">{message}</p>
                </div>
                <div className="text-center space-y-2">
                    {success && (
                        <p className="text-sm">
                            <Link href="/login" className="text-blue-600 hover:underline">Log in to manage your preferences</Link>
                        </p>
                    )}
                    <p className="text-sm">
                        <Link href="/" className="text-blue-600 hover:underline">Go to Jazzy</Link>
                    </p>
                </div>
            </div>
        </div>
    );
}
