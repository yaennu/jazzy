import { redirect } from "next/navigation";
import Link from "next/link";
import { createClient } from "@/lib/supabase/server";
import { createClient as createAdminClient } from "@supabase/supabase-js";
import { JazzyLogo } from "@/components/jazzy-logo";
import { AlbumEmailPreview } from "@/components/album-email-preview";

interface PreviewAlbum {
    title: string;
    artist: string;
    release_year?: number | null;
    cover_image_url?: string | null;
    streaming_link_spotify?: string | null;
    streaming_link_apple?: string | null;
    album_summary?: string | null;
    artist_summary?: string | null;
}

async function getPreviewAlbum(): Promise<PreviewAlbum | null> {
    const albumId = process.env.LANDING_PREVIEW_ALBUM_ID;
    const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL;
    const serviceRoleKey = process.env.SUPABASE_SERVICE_ROLE_KEY;

    if (!albumId || !supabaseUrl || !serviceRoleKey) return null;

    const admin = createAdminClient(supabaseUrl, serviceRoleKey);
    const { data } = await admin
        .from("albums")
        .select("title, artist, release_year, cover_image_url, streaming_link_spotify, streaming_link_apple, album_summary, artist_summary")
        .eq("album_id", albumId)
        .single();

    return data;
}

export default async function Home() {
    const supabase = await createClient();
    const { data: { user } } = await supabase.auth.getUser();

    if (user) {
        redirect("/history");
    }

    const album = await getPreviewAlbum();

    return (
        <div className="flex flex-col">
            {/* Hero */}
            <section className="flex flex-col items-center justify-center px-6 py-24 sm:py-32 text-center">
                <JazzyLogo fill="#18181b" height={56} className="mb-6" />
                <p className="text-lg sm:text-xl text-gray-600 max-w-md mb-8">
                    Discover jazz, one album at a time.
                </p>
                <div className="flex gap-3">
                    <Link
                        href="/register"
                        className="inline-flex items-center justify-center rounded-md bg-gray-900 px-6 py-2.5 text-sm font-medium text-white hover:bg-gray-800 transition-colors"
                    >
                        Get Started
                    </Link>
                    <Link
                        href="/login"
                        className="inline-flex items-center justify-center rounded-md border border-gray-200 px-6 py-2.5 text-sm font-medium text-gray-700 hover:bg-gray-50 transition-colors"
                    >
                        Login
                    </Link>
                </div>
            </section>

            {/* Value Proposition */}
            <section className="px-6 py-16 bg-gray-50">
                <div className="max-w-4xl mx-auto">
                    <h2 className="text-2xl font-bold text-center mb-12">How it works</h2>
                    <div className="grid grid-cols-1 sm:grid-cols-3 gap-8">
                        <div className="text-center">
                            <div className="w-12 h-12 mx-auto mb-4 rounded-full bg-gray-900 flex items-center justify-center text-white text-xl">
                                1
                            </div>
                            <h3 className="font-semibold mb-2">Curated Picks</h3>
                            <p className="text-sm text-gray-600">
                                Hand-selected jazz albums delivered straight to your inbox.
                            </p>
                        </div>
                        <div className="text-center">
                            <div className="w-12 h-12 mx-auto mb-4 rounded-full bg-gray-900 flex items-center justify-center text-white text-xl">
                                2
                            </div>
                            <h3 className="font-semibold mb-2">Your Pace</h3>
                            <p className="text-sm text-gray-600">
                                Choose daily, weekly, or monthly delivery to match your listening habits.
                            </p>
                        </div>
                        <div className="text-center">
                            <div className="w-12 h-12 mx-auto mb-4 rounded-full bg-gray-900 flex items-center justify-center text-white text-xl">
                                3
                            </div>
                            <h3 className="font-semibold mb-2">Start Listening</h3>
                            <p className="text-sm text-gray-600">
                                One-click links to Spotify and Apple Music in every recommendation.
                            </p>
                        </div>
                    </div>
                </div>
            </section>

            {/* Sample Preview */}
            {album && (
                <section className="px-6 py-16">
                    <div className="max-w-xl mx-auto text-center">
                        <h2 className="text-2xl font-bold mb-2">What you&apos;ll get</h2>
                        <p className="text-sm text-gray-600 mb-8">A preview of your jazz recommendations</p>
                        <AlbumEmailPreview album={album} />
                    </div>
                </section>
            )}
        </div>
    );
}
