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
      {/* Overlay */}
      <div
        className="fixed inset-0 bg-black/50 z-40 md:block hidden"
        onClick={() => onOpenChange(false)}
      />

      {/* Modal Container */}
      <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
        <div
          className="w-full max-h-[90vh] bg-white rounded-lg overflow-y-auto md:rounded-lg md:max-w-2xl"
          onClick={(e) => e.stopPropagation()}
        >
          {/* Header */}
          <div className="sticky top-0 bg-white border-b p-4 flex items-center justify-between">
            <h2 className="text-lg font-semibold">Album Details</h2>
            <button
              onClick={() => onOpenChange(false)}
              className="opacity-70 hover:opacity-100 transition-opacity p-1"
            >
              <X className="h-5 w-5" />
              <span className="sr-only">Close</span>
            </button>
          </div>

          {/* Content */}
          <div className="p-6 md:p-8">
            {/* Album Card */}
            <div className="rounded-lg border border-gray-200 overflow-hidden bg-white">
              {album.cover_image_url && (
                <div className="p-6 text-center bg-white">
                  <div className="relative w-full aspect-square max-w-sm mx-auto rounded-lg overflow-hidden bg-gray-100">
                    <Image
                      src={album.cover_image_url}
                      alt={`${album.title} album cover`}
                      fill
                      className="object-cover"
                      sizes="(max-width: 640px) 100vw, (max-width: 1024px) 80vw, 400px"
                    />
                  </div>
                </div>
              )}
              <div className="p-6 text-center bg-white">
                <p className="text-xl font-bold text-gray-900 mb-1">
                  {album.title}
                </p>
                <p className="text-base text-gray-600">
                  {album.artist}
                  {yearText}
                </p>
              </div>
            </div>

            {/* Streaming Buttons */}
            {(album.streaming_link_spotify || album.streaming_link_apple) && (
              <div className="flex flex-wrap gap-3 justify-center mt-6">
                {album.streaming_link_spotify && (
                  <a
                    href={album.streaming_link_spotify}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="flex items-center gap-2 bg-[#1DB954] text-white font-semibold px-6 py-3 rounded-lg hover:opacity-90 transition-opacity text-sm"
                  >
                    Listen on Spotify
                    {album.spotify_link_is_substitute && (
                      <span className="text-xs bg-black/20 px-2 py-1 rounded">
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
                    className="flex items-center gap-2 bg-[#FC3C44] text-white font-semibold px-6 py-3 rounded-lg hover:opacity-90 transition-opacity text-sm"
                  >
                    Listen on Apple Music
                    {album.apple_link_is_substitute && (
                      <span className="text-xs bg-black/20 px-2 py-1 rounded">
                        alternate
                      </span>
                    )}
                  </a>
                )}
              </div>
            )}

            {/* Summaries */}
            {hasSummaries && (
              <div className="jazzy-summaries mt-8 p-6 bg-gray-50 rounded-lg border-l-4 border-gray-200">
                {album.album_summary && (
                  <div className="mb-6">
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
