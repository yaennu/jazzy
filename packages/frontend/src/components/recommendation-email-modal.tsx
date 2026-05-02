"use client";

import Image from "next/image";
import { X } from "lucide-react";

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

function withTargetBlank(html: string): string {
  return html.replace(/<a\s/g, '<a target="_blank" rel="noopener noreferrer" ');
}

const summaryLinkStyles = `
  .jazzy-summaries a {
    color: #52525b;
    text-decoration: underline dotted #a1a1aa;
    text-underline-offset: 2px;
  }
`;

interface RecommendationEmailModalProps {
  album: Album | null;
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

export function RecommendationEmailModal({
  album,
  open,
  onOpenChange,
}: RecommendationEmailModalProps) {
  if (!open || !album) return null;

  const yearText = album.release_year ? ` (${album.release_year})` : "";
  const hasSummaries = album.album_summary || album.artist_summary;

  return (
    <>
      <style>{summaryLinkStyles}</style>

      {/* Overlay — always visible on all screen sizes */}
      <div
        className="fixed inset-0 bg-black/50 z-40"
        onClick={() => onOpenChange(false)}
      />

      {/* Modal wrapper — bottom-sheet on mobile, centered on sm+ */}
      <div className="fixed inset-0 z-50 flex items-end sm:items-center sm:justify-center sm:p-4">
        {/*
          Mobile: anchors to bottom, rounded top corners, fills 90% of viewport height
          Desktop: centered, rounded on all sides, max-width constrained
        */}
        <div
          className="w-full sm:max-w-2xl bg-white rounded-t-2xl sm:rounded-xl flex flex-col"
          style={{ maxHeight: "90dvh" }}
          onClick={(e) => e.stopPropagation()}
        >
          {/* Fixed header — never scrolls */}
          <div className="shrink-0 border-b px-4 py-3 flex items-center justify-between">
            <h2 className="text-base font-semibold">Album Details</h2>
            <button
              onClick={() => onOpenChange(false)}
              className="opacity-60 hover:opacity-100 transition-opacity p-1.5 rounded-md hover:bg-gray-100"
            >
              <X className="h-4 w-4" />
              <span className="sr-only">Close</span>
            </button>
          </div>

          {/* Scrollable content area */}
          <div className="overflow-y-auto flex-1 p-5 sm:p-8">
            {/* Album cover — fixed height on mobile to prevent dominating the screen */}
            {album.cover_image_url && (
              <div className="mb-4">
                <div className="relative w-full aspect-square rounded-lg overflow-hidden bg-gray-100 shrink-0">
                  <Image
                    src={album.cover_image_url}
                    alt={`${album.title} album cover`}
                    fill
                    className="object-cover"
                    sizes="(max-width: 640px) 100vw, 672px"
                  />
                </div>
              </div>
            )}

            {/* Title & artist */}
            <div className="text-center mb-5">
              <p className="text-xl font-bold text-gray-900 mb-1">
                {album.title}
              </p>
              <p className="text-base text-gray-500">
                {album.artist}
                {yearText}
              </p>
            </div>

            {/* Streaming Buttons */}
            {(album.streaming_link_spotify || album.streaming_link_apple) && (
              <div className="flex flex-wrap gap-3 justify-center mb-6">
                {album.streaming_link_spotify && (
                  <a
                    href={album.streaming_link_spotify}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="flex items-center gap-2 bg-[#1DB954] text-white font-semibold px-5 py-2.5 rounded-lg hover:opacity-90 transition-opacity text-sm"
                  >
                    Listen on Spotify
                    {album.spotify_link_is_substitute && (
                      <span className="text-xs bg-black/20 px-1.5 py-0.5 rounded">
                        alternate
                      </span>
                    )}
                  </a>
                )}
                {album.streaming_link_apple && (
                  <a
                    href={album.streaming_link_apple}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="flex items-center gap-2 bg-[#FC3C44] text-white font-semibold px-5 py-2.5 rounded-lg hover:opacity-90 transition-opacity text-sm"
                  >
                    Listen on Apple Music
                    {album.apple_link_is_substitute && (
                      <span className="text-xs bg-black/20 px-1.5 py-0.5 rounded">
                        alternate
                      </span>
                    )}
                  </a>
                )}
              </div>
            )}

            {/* Summaries */}
            {hasSummaries && (
              <div className="jazzy-summaries p-5 bg-gray-50 rounded-lg border-l-4 border-gray-200">
                {album.album_summary && (
                  <div className={album.artist_summary ? "mb-5" : ""}>
                    <p className="text-xs font-semibold uppercase tracking-wider text-gray-900 mb-2">
                      About this album
                    </p>
                    <p
                      className="text-sm leading-relaxed text-gray-700"
                      dangerouslySetInnerHTML={{
                        __html: withTargetBlank(album.album_summary),
                      }}
                    />
                  </div>
                )}
                {album.artist_summary && (
                  <div>
                    <p className="text-xs font-semibold uppercase tracking-wider text-gray-900 mb-2">
                      About the artist
                    </p>
                    <p
                      className="text-sm leading-relaxed text-gray-700"
                      dangerouslySetInnerHTML={{
                        __html: withTargetBlank(album.artist_summary),
                      }}
                    />
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      </div>
    </>
  );
}
