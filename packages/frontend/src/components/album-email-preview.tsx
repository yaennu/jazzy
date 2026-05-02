import Image from "next/image";
import { JazzyLogo } from "@/components/jazzy-logo";

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

interface Album {
    title: string;
    artist: string;
    release_year?: number | null;
    cover_image_url?: string | null;
    streaming_link_spotify?: string | null;
    streaming_link_apple?: string | null;
    album_summary?: string | null;
    artist_summary?: string | null;
}

export function AlbumEmailPreview({ album }: { album: Album }) {
    const yearText = album.release_year ? ` (${album.release_year})` : "";
    const hasSummaries = album.album_summary || album.artist_summary;

    return (
        <>
        <style>{summaryLinkStyles}</style>
        <div style={{ fontFamily: "'Helvetica Neue', Helvetica, Arial, sans-serif", maxWidth: 480, margin: "0 auto", borderRadius: 12, overflow: "hidden", boxShadow: "0 1px 3px rgba(0,0,0,0.1)", border: "1px solid #e4e4e7" }}>
            {/* Header */}
            <div style={{ backgroundColor: "#18181b", padding: "32px 40px", textAlign: "center" }}>
                <JazzyLogo fill="#ffffff" height={40} className="mx-auto" />
                <p style={{ margin: "8px 0 0", color: "#a1a1aa", fontSize: 14 }}>Your jazz album recommendations</p>
            </div>

            {/* Body */}
            <div style={{ padding: "40px", backgroundColor: "#ffffff" }}>
                <h2 style={{ margin: "0 0 16px", color: "#18181b", fontSize: 22, fontWeight: 600 }}>Hey Jazzy Fan!</h2>
                <p style={{ margin: "0 0 24px", color: "#52525b", fontSize: 15, lineHeight: 1.6 }}>
                    We picked a jazz album just for you. Give it a listen and let the music take you somewhere new.
                </p>

                {/* Album Card */}
                <div style={{ borderRadius: 8, border: "1px solid #e4e4e7", overflow: "hidden" }}>
                    {album.cover_image_url && (
                        <div style={{ padding: "24px 24px 0", textAlign: "center", backgroundColor: "#ffffff" }}>
                            <div style={{ position: "relative", width: 260, height: 260, margin: "0 auto", borderRadius: 8, overflow: "hidden" }}>
                                <Image
                                    src={album.cover_image_url}
                                    alt={`${album.title} album cover`}
                                    fill
                                    style={{ objectFit: "cover" }}
                                    sizes="260px"
                                />
                            </div>
                        </div>
                    )}
                    <div style={{ padding: 24, textAlign: "center", backgroundColor: "#ffffff" }}>
                        <p style={{ margin: "0 0 4px", color: "#18181b", fontSize: 20, fontWeight: 700 }}>{album.title}</p>
                        <p style={{ margin: 0, color: "#52525b", fontSize: 16 }}>{album.artist}{yearText}</p>
                    </div>
                </div>

                {/* Streaming Buttons */}
                {(album.streaming_link_spotify || album.streaming_link_apple) && (
                    <div style={{ paddingTop: 24, textAlign: "center" }}>
                        {album.streaming_link_spotify && (
                            <a
                                href={album.streaming_link_spotify}
                                target="_blank"
                                rel="noopener noreferrer"
                                style={{ display: "inline-block", backgroundColor: "#1DB954", color: "#ffffff", textDecoration: "none", fontSize: 14, fontWeight: 600, padding: "12px 24px", borderRadius: 8, margin: 6, minWidth: 160, boxSizing: "border-box", textAlign: "center" }}
                            >
                                Listen on Spotify
                            </a>
                        )}
                        {album.streaming_link_apple && (
                            <a
                                href={album.streaming_link_apple}
                                target="_blank"
                                rel="noopener noreferrer"
                                style={{ display: "inline-block", backgroundColor: "#FC3C44", color: "#ffffff", textDecoration: "none", fontSize: 14, fontWeight: 600, padding: "12px 24px", borderRadius: 8, margin: 6, minWidth: 160, boxSizing: "border-box", textAlign: "center" }}
                            >
                                Listen on Apple Music
                            </a>
                        )}
                    </div>
                )}

                {/* Summaries */}
                {hasSummaries && (
                    <div className="jazzy-summaries" style={{ marginTop: 24, padding: "20px 24px", backgroundColor: "#fafafa", borderRadius: 8, borderLeft: "3px solid #e4e4e7" }}>
                        {album.album_summary && (
                            <>
                                <p style={{ margin: "0 0 8px", color: "#18181b", fontSize: 13, fontWeight: 600, letterSpacing: "0.05em", textTransform: "uppercase" }}>About this album</p>
                                <p style={{ margin: album.artist_summary ? "0 0 20px" : 0, color: "#52525b", fontSize: 14, lineHeight: 1.7 }} dangerouslySetInnerHTML={{ __html: withTargetBlank(album.album_summary) }} />
                            </>
                        )}
                        {album.artist_summary && (
                            <>
                                <p style={{ margin: "0 0 8px", color: "#18181b", fontSize: 13, fontWeight: 600, letterSpacing: "0.05em", textTransform: "uppercase" }}>About the artist</p>
                                <p style={{ margin: 0, color: "#52525b", fontSize: 14, lineHeight: 1.7 }} dangerouslySetInnerHTML={{ __html: withTargetBlank(album.artist_summary) }} />
                            </>
                        )}
                    </div>
                )}
            </div>

            {/* Footer */}
            <div style={{ padding: "24px 40px", borderTop: "1px solid #e4e4e7", textAlign: "center", backgroundColor: "#ffffff" }}>
                <p style={{ margin: 0, color: "#a1a1aa", fontSize: 12 }}>Jazzy — Discover jazz, one album at a time.</p>
            </div>
        </div>
        </>
    );
}
