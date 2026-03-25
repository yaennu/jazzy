"use client";

import { useState, useEffect } from "react";
import Image from "next/image";
import Link from "next/link";
import { createClient } from "@/lib/supabase/client";
import { RecommendationEmailModal } from "@/components/recommendation-email-modal";

interface Album {
    title: string;
    artist: string;
    release_year?: number | null;
    cover_image_url?: string | null;
    streaming_link_spotify?: string | null;
    streaming_link_apple?: string | null;
    album_summary?: string | null;
    artist_summary?: string | null;
    spotify_link_is_substitute?: boolean | null;
    apple_link_is_substitute?: boolean | null;
}

interface Recommendation {
    sent_date: string;
    albums: Album;
}

export default function HistoryPage() {
    const [recommendations, setRecommendations] = useState<Recommendation[]>([]);
    const [loading, setLoading] = useState(true);
    const [selectedAlbum, setSelectedAlbum] = useState<Album | null>(null);
    const [modalOpen, setModalOpen] = useState(false);
    const supabase = createClient();

    useEffect(() => {
        const fetchRecommendations = async () => {
            const { data: { user } } = await supabase.auth.getUser();
            if (!user) return;

            const { data } = await supabase
                .from("recommendations")
                .select("sent_date, albums(title, artist, release_year, cover_image_url, streaming_link_spotify, streaming_link_apple, album_summary, artist_summary, spotify_link_is_substitute, apple_link_is_substitute)")
                .eq("user_id", user.id)
                .order("sent_date", { ascending: false });

            if (data) {
                setRecommendations(data as unknown as Recommendation[]);
            }
            setLoading(false);
        };
        fetchRecommendations();
    }, [supabase]);

    if (loading) {
        return (
            <div className="max-w-5xl mx-auto px-6 py-12">
                <div className="h-8 w-56 bg-gray-200 rounded animate-pulse mb-2" />
                <div className="h-4 w-72 bg-gray-200 rounded animate-pulse mb-8" />
                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
                    {[1, 2, 3, 4, 5, 6].map((i) => (
                        <div key={i} className="bg-white rounded-lg shadow-md overflow-hidden">
                            <div className="aspect-square bg-gray-200 animate-pulse" />
                            <div className="p-4 space-y-2">
                                <div className="h-5 w-3/4 bg-gray-200 rounded animate-pulse" />
                                <div className="h-4 w-1/2 bg-gray-200 rounded animate-pulse" />
                                <div className="h-3 w-1/3 bg-gray-200 rounded animate-pulse" />
                            </div>
                        </div>
                    ))}
                </div>
            </div>
        );
    }

    if (recommendations.length === 0) {
        return (
            <div className="flex items-center justify-center min-h-[60vh]">
                <div className="text-center max-w-md px-6">
                    <h1 className="text-2xl font-bold mb-2">No recommendations yet</h1>
                    <p className="text-sm text-muted-foreground mb-4">
                        Your first jazz pick will arrive based on your newsletter schedule. Check your email!
                    </p>
                    <Link
                        href="/settings"
                        className="text-sm text-blue-600 hover:underline"
                    >
                        Configure your delivery frequency
                    </Link>
                </div>
            </div>
        );
    }

    return (
        <div className="max-w-5xl mx-auto px-6 py-12">
            <h1 className="text-2xl font-bold mb-1">Your Recommendations</h1>
            <p className="text-sm text-muted-foreground mb-8">
                {recommendations.length} album{recommendations.length !== 1 ? "s" : ""} recommended so far
            </p>
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
                {recommendations.map((rec, index) => {
                    const album = rec.albums;
                    const yearText = album.release_year ? ` (${album.release_year})` : "";
                    const sentDate = new Date(rec.sent_date).toLocaleDateString("en-US", {
                        month: "short",
                        day: "numeric",
                        year: "numeric",
                    });

                    return (
                        <div
                            key={index}
                            className="bg-white rounded-lg shadow-md overflow-hidden cursor-pointer transition-all hover:shadow-lg hover:scale-105"
                            onClick={() => {
                                setSelectedAlbum(album);
                                setModalOpen(true);
                            }}
                        >
                            {album.cover_image_url ? (
                                <div className="aspect-square relative bg-gray-100">
                                    <Image
                                        src={album.cover_image_url}
                                        alt={`${album.title} album cover`}
                                        fill
                                        className="object-cover"
                                        sizes="(max-width: 640px) 100vw, (max-width: 1024px) 50vw, 33vw"
                                    />
                                </div>
                            ) : (
                                <div className="aspect-square bg-gray-100 flex items-center justify-center">
                                    <span className="text-4xl text-gray-300">&#9835;</span>
                                </div>
                            )}
                            <div className="p-4">
                                <h3 className="font-semibold text-sm truncate" title={album.title}>{album.title}</h3>
                                <p className="text-sm text-muted-foreground truncate" title={`${album.artist}${yearText}`}>
                                    {album.artist}{yearText}
                                </p>
                                <p className="text-xs text-gray-400 mt-1">Sent {sentDate}</p>
                                <div className="flex gap-2 mt-3">
                                    {album.streaming_link_spotify && (
                                        <a
                                            href={album.streaming_link_spotify}
                                            target="_blank"
                                            rel="noopener noreferrer"
                                            onClick={(e) => e.stopPropagation()}
                                            className="text-xs font-medium px-3 py-1.5 rounded-md bg-[#1DB954] text-white hover:opacity-90 transition-opacity"
                                        >
                                            Spotify
                                        </a>
                                    )}
                                    {album.streaming_link_apple && (
                                        <a
                                            href={album.streaming_link_apple}
                                            target="_blank"
                                            rel="noopener noreferrer"
                                            onClick={(e) => e.stopPropagation()}
                                            className="text-xs font-medium px-3 py-1.5 rounded-md bg-[#FC3C44] text-white hover:opacity-90 transition-opacity"
                                        >
                                            Apple Music
                                        </a>
                                    )}
                                </div>
                            </div>
                        </div>
                    );
                })}
            </div>

            <RecommendationEmailModal
                album={selectedAlbum}
                open={modalOpen}
                onOpenChange={setModalOpen}
            />
        </div>
    );
}
