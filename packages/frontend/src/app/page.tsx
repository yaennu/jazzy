import { redirect } from "next/navigation";
import Image from "next/image";
import Link from "next/link";
import { createClient } from "@/lib/supabase/server";
import { createClient as createAdminClient } from "@supabase/supabase-js";
import { JazzyLogo } from "@/components/jazzy-logo";

interface PreviewAlbum {
    title: string;
    artist: string;
    release_year?: number | null;
    cover_image_url?: string | null;
    streaming_link_spotify?: string | null;
    streaming_link_apple?: string | null;
}

async function getPreviewAlbum(): Promise<PreviewAlbum | null> {
    const albumId = process.env.LANDING_PREVIEW_ALBUM_ID;
    const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL;
    const serviceRoleKey = process.env.SUPABASE_SERVICE_ROLE_KEY;

    if (!albumId || !supabaseUrl || !serviceRoleKey) return null;

    const admin = createAdminClient(supabaseUrl, serviceRoleKey);
    const { data } = await admin
        .from("albums")
        .select("title, artist, release_year, cover_image_url, streaming_link_spotify, streaming_link_apple")
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
            <section className="px-6 py-16">
                <div className="max-w-md mx-auto text-center">
                    <h2 className="text-2xl font-bold mb-2">What you&apos;ll get</h2>
                    <p className="text-sm text-gray-600 mb-8">A preview of your jazz recommendations</p>
                    <div className="bg-white rounded-lg shadow-md border border-gray-100 overflow-hidden">
                        <div className="bg-gray-900 px-6 py-4 text-center">
                            <JazzyLogo fill="#ffffff" height={20} className="mx-auto" />
                            <p className="text-gray-400 text-xs mt-1">Your jazz album recommendations</p>
                        </div>
                        <div className="p-6">
                            <div className="rounded-lg border border-gray-200 overflow-hidden">
                                {album?.cover_image_url && (
                                    <div className="relative aspect-square bg-gray-100">
                                        <Image
                                            src={album.cover_image_url}
                                            alt={`${album.title} album cover`}
                                            fill
                                            className="object-cover"
                                            sizes="(max-width: 448px) 100vw, 448px"
                                        />
                                    </div>
                                )}
                                <div className="p-6 text-center">
                                    <p className="text-lg font-bold text-gray-900">{album?.title ?? "Kind of Blue"}</p>
                                    <p className="text-gray-600 text-sm">
                                        {album?.artist ?? "Miles Davis"}
                                        {(album?.release_year ?? 1959) ? ` (${album?.release_year ?? 1959})` : ""}
                                    </p>
                                </div>
                            </div>
                            <div className="flex justify-center gap-2 mt-4">
                                {(album?.streaming_link_spotify !== null) && (
                                    <span className="inline-block bg-[#1DB954] text-white text-xs font-semibold px-4 py-2 rounded-md">
                                        Listen on Spotify
                                    </span>
                                )}
                                {(album?.streaming_link_apple !== null) && (
                                    <span className="inline-block bg-[#FC3C44] text-white text-xs font-semibold px-4 py-2 rounded-md">
                                        Apple Music
                                    </span>
                                )}
                            </div>
                        </div>
                    </div>
                </div>
            </section>
        </div>
    );
}
