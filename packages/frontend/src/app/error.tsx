"use client";

export default function Error({
    error,
    reset,
}: {
    error: Error & { digest?: string };
    reset: () => void;
}) {
    return (
        <div className="flex items-center justify-center min-h-screen">
            <div className="w-full max-w-md p-8 space-y-6 bg-white rounded-lg shadow-md text-center">
                <h1 className="text-3xl font-bold">Something went wrong</h1>
                <p className="text-sm text-gray-600">
                    An unexpected error occurred. Please try again.
                </p>
                <button
                    onClick={reset}
                    className="inline-flex items-center justify-center rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:bg-primary/90"
                >
                    Try again
                </button>
            </div>
        </div>
    );
}
