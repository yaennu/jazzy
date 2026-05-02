import { NextRequest, NextResponse } from "next/server";

const GITHUB_TOKEN = process.env.GITHUB_TOKEN;
const GITHUB_REPO = "yaennu/jazzy";

export async function POST(request: NextRequest) {
    if (!GITHUB_TOKEN) {
        return NextResponse.json({ error: "Bug reporting is not configured." }, { status: 503 });
    }

    const { album_id, title, artist, description } = await request.json();

    if (!description?.trim()) {
        return NextResponse.json({ error: "Description is required." }, { status: 400 });
    }

    const issueTitle = `Bug report: ${title} by ${artist}`;
    const issueBody = [
        `**Album:** ${title} by ${artist}`,
        `**Album ID:** \`${album_id}\``,
        "",
        "**Description:**",
        description.trim(),
        "",
        "---",
        "*Submitted via Jazzy bug report form*",
    ].join("\n");

    const response = await fetch(`https://api.github.com/repos/${GITHUB_REPO}/issues`, {
        method: "POST",
        headers: {
            Authorization: `Bearer ${GITHUB_TOKEN}`,
            Accept: "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
            "Content-Type": "application/json",
        },
        body: JSON.stringify({ title: issueTitle, body: issueBody, labels: ["bug"] }),
    });

    if (!response.ok) {
        const text = await response.text();
        console.error("GitHub API error:", response.status, text);
        return NextResponse.json({ error: "Failed to create issue." }, { status: 502 });
    }

    const issue = await response.json();
    return NextResponse.json({ url: issue.html_url });
}
