"use client";

import { Suspense, useState } from "react";
import { useSearchParams } from "next/navigation";
import { Button } from "@/components/ui/button";

function ReportBugForm() {
    const searchParams = useSearchParams();
    const album_id = searchParams.get("album_id") ?? "";
    const title = searchParams.get("title") ?? "Unknown Album";
    const artist = searchParams.get("artist") ?? "Unknown Artist";

    const [description, setDescription] = useState("");
    const [status, setStatus] = useState<"idle" | "loading" | "success" | "error">("idle");
    const [issueUrl, setIssueUrl] = useState("");
    const [errorMsg, setErrorMsg] = useState("");

    async function handleSubmit(e: React.FormEvent) {
        e.preventDefault();
        setStatus("loading");
        setErrorMsg("");

        try {
            const res = await fetch("/api/report-bug", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ album_id, title, artist, description }),
            });
            const data = await res.json();
            if (!res.ok) {
                setErrorMsg(data.error ?? "Something went wrong.");
                setStatus("error");
            } else {
                setIssueUrl(data.url);
                setStatus("success");
            }
        } catch {
            setErrorMsg("Network error. Please try again.");
            setStatus("error");
        }
    }

    if (status === "success") {
        return (
            <div className="flex items-center justify-center min-h-screen">
                <div className="w-full max-w-md p-8 space-y-4 bg-card rounded-lg shadow-md text-center">
                    <h1 className="text-2xl font-bold">Thanks for the report!</h1>
                    <p className="text-sm text-muted-foreground">
                        Your bug report has been submitted. You can track it on GitHub:
                    </p>
                    <a
                        href={issueUrl}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-sm text-blue-600 hover:underline break-all"
                    >
                        {issueUrl}
                    </a>
                </div>
            </div>
        );
    }

    return (
        <div className="flex items-center justify-center min-h-screen">
            <div className="w-full max-w-md p-8 bg-card rounded-lg shadow-md">
                <h1 className="text-2xl font-bold mb-1">Report a bug</h1>
                <p className="text-sm text-muted-foreground mb-6">
                    Something wrong with{" "}
                    <span className="font-medium text-foreground">
                        {title} &mdash; {artist}
                    </span>
                    ?
                </p>
                <form onSubmit={handleSubmit} className="space-y-4">
                    <div>
                        <label htmlFor="description" className="block text-sm font-medium mb-1">
                            What&apos;s the issue?
                        </label>
                        <textarea
                            id="description"
                            value={description}
                            onChange={(e) => setDescription(e.target.value)}
                            placeholder="e.g. The Spotify link points to the wrong album, the cover image is missing…"
                            rows={5}
                            required
                            className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring resize-none"
                        />
                    </div>
                    {status === "error" && (
                        <p className="text-sm text-destructive">{errorMsg}</p>
                    )}
                    <Button type="submit" disabled={status === "loading"} className="w-full">
                        {status === "loading" ? "Submitting…" : "Submit report"}
                    </Button>
                </form>
            </div>
        </div>
    );
}

export default function ReportBugPage() {
    return (
        <Suspense>
            <ReportBugForm />
        </Suspense>
    );
}
