export default function SettingsLoading() {
    return (
        <div className="flex items-center justify-center min-h-screen">
            <div className="w-full max-w-md p-8 space-y-8 bg-white rounded-lg shadow-md">
                <div className="text-center space-y-2">
                    <div className="h-8 w-48 bg-gray-200 rounded animate-pulse mx-auto" />
                    <div className="h-4 w-64 bg-gray-100 rounded animate-pulse mx-auto" />
                </div>
                <div className="space-y-4">
                    <div className="h-5 w-20 bg-gray-200 rounded animate-pulse" />
                    <div className="space-y-3">
                        <div className="h-6 w-32 bg-gray-100 rounded animate-pulse" />
                        <div className="h-6 w-32 bg-gray-100 rounded animate-pulse" />
                        <div className="h-6 w-32 bg-gray-100 rounded animate-pulse" />
                    </div>
                    <div className="h-10 w-full bg-gray-200 rounded animate-pulse" />
                </div>
            </div>
        </div>
    );
}
