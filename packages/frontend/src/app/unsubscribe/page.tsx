import { createClient } from "@/lib/supabase/server";

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

        const { data: user } = await supabase
            .from("users")
            .select("user_id, subscription_status")
            .eq("unsubscribe_token", token)
            .single();

        if (!user) {
            message = "Invalid unsubscribe link.";
        } else if (user.subscription_status === "inactive") {
            message = "You are already unsubscribed.";
            success = true;
        } else {
            const { error } = await supabase
                .from("users")
                .update({ subscription_status: "inactive" })
                .eq("user_id", user.user_id);

            if (error) {
                message = "Something went wrong. Please try again later.";
            } else {
                message = "You have been unsubscribed from Jazzy recommendations.";
                success = true;
            }
        }
    }

    return (
        <div className="flex items-center justify-center min-h-screen">
            <div className="w-full max-w-md p-8 space-y-8 bg-white rounded-lg shadow-md">
                <div className="text-center">
                    <h1 className="text-3xl font-bold">
                        {success ? "Unsubscribed" : "Error"}
                    </h1>
                    <p className="mt-4 text-sm text-gray-600">{message}</p>
                </div>
            </div>
        </div>
    );
}
