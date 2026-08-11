import { ImageResponse } from "next/og";
import { site } from "@/lib/site";

export const alt = `${site.name} · ${site.tagline}`;
export const size = { width: 1200, height: 630 };
export const contentType = "image/png";

export default async function OpengraphImage() {
  return new ImageResponse(
    (
      <div
        style={{
          width: "100%",
          height: "100%",
          display: "flex",
          flexDirection: "column",
          justifyContent: "space-between",
          padding: 80,
          background: "#08100f",
          color: "#e8f1ef",
          fontFamily: "sans-serif",
        }}
      >
        <div
          style={{
            display: "flex",
            alignItems: "center",
            gap: 14,
            fontSize: 22,
            letterSpacing: 4,
            textTransform: "uppercase",
            color: "#16d6bd",
          }}
        >
          <div
            style={{ width: 12, height: 12, borderRadius: "50%", background: "#16d6bd" }}
          />
          Authentication for FastAPI
        </div>

        <div
          style={{
            display: "flex",
            flexDirection: "column",
            fontSize: 82,
            fontWeight: 800,
            lineHeight: 1.05,
            letterSpacing: -2,
          }}
        >
          <span>Login, tokens, and roles.</span>
          <span style={{ display: "flex", gap: 20 }}>
            Wired in
            <span
              style={{
                background: "#16d6bd",
                color: "#04231f",
                padding: "0 20px",
                borderRadius: 14,
              }}
            >
              one call
            </span>
          </span>
        </div>

        <div
          style={{
            display: "flex",
            justifyContent: "space-between",
            alignItems: "flex-end",
            fontSize: 24,
            color: "#93a6a2",
          }}
        >
          <div style={{ display: "flex", gap: 22 }}>
            <span style={{ color: "#16d6bd" }}>$</span>
            <span>uv add fastauth_iq</span>
          </div>
          <div style={{ display: "flex", gap: 16, fontSize: 20, color: "#677a76" }}>
            <span>v{site.version}</span>
            <span>·</span>
            <span>MIT</span>
            <span>·</span>
            <span>by {site.author.name}</span>
          </div>
        </div>
      </div>
    ),
    { ...size }
  );
}
