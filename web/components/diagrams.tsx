/**
 * Inline SVG sequence diagrams. Colours come from the theme's CSS variables so
 * both light and dark work with no duplicate markup, and the text is real text,
 * so it scales and stays selectable.
 */

const MONO = "var(--font-spline-mono), ui-monospace, monospace";

type Step = {
  /** Direction the arrow points. */
  dir: "right" | "left";
  label: string;
  /** Dimmed styling, for failure or elapsed-time steps. */
  muted?: boolean;
  /** Drawn as a dashed arrow, for a rejected or expired exchange. */
  dashed?: boolean;
};

function Sequence({
  left,
  right,
  steps,
  notes = [],
  title,
}: {
  left: string;
  right: string;
  steps: Step[];
  /** Index-keyed captions rendered between steps, e.g. an elapsed-time marker. */
  notes?: { after: number; label: string }[];
  title: string;
}) {
  const W = 760;
  const LEFT_X = 96;
  const RIGHT_X = 664;
  const HEAD = 54;
  const STEP_H = 46;
  const NOTE_H = 30;

  // Lay out rows top to bottom, inserting notes where they were requested.
  const rows: ({ kind: "step"; step: Step } | { kind: "note"; label: string })[] = [];
  steps.forEach((step, i) => {
    rows.push({ kind: "step", step });
    notes
      .filter((n) => n.after === i)
      .forEach((n) => rows.push({ kind: "note", label: n.label }));
  });

  const bodyH = rows.reduce(
    (h, row) => h + (row.kind === "step" ? STEP_H : NOTE_H),
    0
  );
  const H = HEAD + bodyH + 28;

  let y = HEAD + 18;

  return (
    <figure className="my-8">
      <svg
        viewBox={`0 0 ${W} ${H}`}
        className="w-full"
        role="img"
        aria-label={title}
      >
        <defs>
          <marker
            id="arrow-fwd"
            viewBox="0 0 10 10"
            refX="9"
            refY="5"
            markerWidth="6"
            markerHeight="6"
            orient="auto-start-reverse"
          >
            <path d="M 0 0 L 10 5 L 0 10 z" fill="var(--muted)" />
          </marker>
        </defs>

        {/* Lifelines */}
        <line
          x1={LEFT_X}
          y1={HEAD - 12}
          x2={LEFT_X}
          y2={H - 14}
          stroke="var(--line)"
          strokeWidth="1"
        />
        <line
          x1={RIGHT_X}
          y1={HEAD - 12}
          x2={RIGHT_X}
          y2={H - 14}
          stroke="var(--line)"
          strokeWidth="1"
        />

        {/* Actor labels */}
        {[
          { x: LEFT_X, label: left },
          { x: RIGHT_X, label: right },
        ].map((actor) => (
          <g key={actor.label}>
            <rect
              x={actor.x - 62}
              y={16}
              width={124}
              height={30}
              rx={8}
              fill="var(--accent-soft)"
              stroke="var(--accent-line)"
            />
            <text
              x={actor.x}
              y={36}
              textAnchor="middle"
              fontFamily={MONO}
              fontSize="12"
              fill="var(--accent)"
            >
              {actor.label}
            </text>
          </g>
        ))}

        {/* Messages */}
        {rows.map((row, i) => {
          if (row.kind === "note") {
            const noteY = y + 4;
            y += NOTE_H;
            return (
              <text
                key={i}
                x={W / 2}
                y={noteY}
                textAnchor="middle"
                fontFamily={MONO}
                fontSize="11"
                fill="var(--muted-2)"
                fontStyle="italic"
              >
                {row.label}
              </text>
            );
          }

          const { dir, label, muted, dashed } = row.step;
          const lineY = y + 16;
          const from = dir === "right" ? LEFT_X : RIGHT_X;
          const to = dir === "right" ? RIGHT_X : LEFT_X;
          y += STEP_H;

          return (
            <g key={i}>
              <text
                x={(LEFT_X + RIGHT_X) / 2}
                y={lineY - 8}
                textAnchor="middle"
                fontFamily={MONO}
                fontSize="12"
                fill={muted ? "var(--muted-2)" : "var(--foreground)"}
              >
                {label}
              </text>
              <line
                x1={from}
                y1={lineY}
                x2={to}
                y2={lineY}
                stroke={muted ? "var(--muted-2)" : "var(--muted)"}
                strokeWidth="1.5"
                strokeDasharray={dashed ? "5 4" : undefined}
                markerEnd="url(#arrow-fwd)"
              />
            </g>
          );
        })}
      </svg>
      <figcaption className="mt-2 text-center font-mono text-[11px] text-muted-2">
        {title}
      </figcaption>
    </figure>
  );
}

export function TokenFlowDiagram() {
  return (
    <Sequence
      title="The login and refresh cycle"
      left="your app"
      right="FastAuth"
      steps={[
        { dir: "right", label: "POST /token  ·  username + password" },
        { dir: "left", label: "access token (30 min)  +  refresh token (7 days)" },
        { dir: "right", label: "GET /protected  ·  Authorization: Bearer …" },
        { dir: "left", label: "200  ·  your route runs" },
        { dir: "right", label: "GET /protected  ·  same access token", muted: true },
        { dir: "left", label: "401  ·  token expired", muted: true, dashed: true },
        { dir: "right", label: "POST /token/refresh  ·  refresh token" },
        { dir: "left", label: "a fresh access token, no password needed" },
      ]}
      notes={[{ after: 3, label: "… 30 minutes pass …" }]}
    />
  );
}

export function ResetFlowDiagram() {
  return (
    <Sequence
      title="The password reset flow"
      left="user"
      right="FastAuth"
      steps={[
        { dir: "right", label: "POST /password/forgot  ·  email address" },
        { dir: "left", label: "200 always, so accounts cannot be discovered" },
        { dir: "left", label: "your on_password_reset hook emails the token", muted: true },
        { dir: "right", label: "POST /password/reset  ·  token + new password" },
        { dir: "left", label: "200  ·  password changed, token now dead" },
        { dir: "left", label: "every old session revoked automatically", muted: true },
      ]}
    />
  );
}
