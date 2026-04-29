import Link from "next/link";

// Paris photo URLs (Unsplash — free to embed)
const PHOTO = {
  heroNight:
    "https://images.unsplash.com/photo-1502602898657-3e91760cbb34?auto=format&fit=crop&w=1920&q=85",
  aerialDay:
    "https://images.unsplash.com/photo-1499856871958-5b9627545d1a?auto=format&fit=crop&w=1920&q=85",
  neighborhood:
    "https://images.unsplash.com/photo-1431274172761-fca41d930114?auto=format&fit=crop&w=800&q=80",
  metro:
    "https://images.unsplash.com/photo-1589330694653-ded6df03f754?auto=format&fit=crop&w=800&q=80",
  park:
    "https://images.unsplash.com/photo-1560969184-10fe8719e047?auto=format&fit=crop&w=800&q=80",
  buildings:
    "https://images.unsplash.com/photo-1520939817895-060bdaf4fe1b?auto=format&fit=crop&w=800&q=80",
};

// Simplified Paris score grid (0=void, 1–10=score)
const PARIS_GRID = [
  [0, 0, 4, 5, 6, 7, 7, 6, 5, 4, 0, 0],
  [0, 3, 5, 7, 8, 9, 9, 8, 7, 6, 4, 0],
  [0, 4, 6, 8, 9, 10, 10, 9, 8, 7, 5, 0],
  [3, 5, 7, 9, 10, 10, 10, 9, 8, 7, 5, 3],
  [0, 4, 6, 8, 9, 10, 9, 8, 7, 6, 4, 0],
  [0, 3, 5, 7, 8, 8, 8, 7, 6, 5, 3, 0],
  [0, 0, 4, 5, 6, 7, 7, 6, 5, 4, 0, 0],
];

function scoreColor(s: number): string {
  if (s === 0) return "transparent";
  if (s >= 9) return "#007AFF";
  if (s >= 7) return "#30D158";
  if (s >= 5) return "#FF9F0A";
  return "#FF453A";
}

const TOP_ZONES = [
  { name: "Le Marais", arr: "3ème", score: "9.4" },
  { name: "Quartier Latin", arr: "5ème", score: "8.9" },
  { name: "Canal St-Martin", arr: "10ème", score: "8.3" },
  { name: "Montmartre", arr: "18ème", score: "7.8" },
  { name: "République", arr: "11ème", score: "7.5" },
];

const stats = [
  { value: "80+", label: "Paris zones" },
  { value: "4", label: "Main indicators" },
  { value: "8", label: "Liveability pillars" },
  { value: "100%", label: "Open data" },
];

const features = [
  {
    photo: PHOTO.neighborhood,
    overlay: "from-blue-700/85 to-[#007AFF]/70",
    iconBg: "bg-blue-50 text-[#007AFF]",
    label: "Vivabilité Familiale",
    badge: "top score 9.4",
    description:
      "Composite liveability score across 8 pillars — schools, childcare, safety, healthcare, green spaces, and more — for every Paris neighbourhood.",
    icon: (
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.8} className="h-4 w-4">
        <path strokeLinecap="round" strokeLinejoin="round" d="M2.25 12l8.954-8.955c.44-.439 1.152-.439 1.591 0L21.75 12M4.5 9.75v10.125c0 .621.504 1.125 1.125 1.125H9.75v-4.875c0-.621.504-1.125 1.125-1.125h2.25c.621 0 1.125.504 1.125 1.125V21h4.125c.621 0 1.125-.504 1.125-1.125V9.75M8.25 21h8.25" />
      </svg>
    ),
  },
  {
    photo: PHOTO.metro,
    overlay: "from-orange-700/85 to-orange-500/70",
    iconBg: "bg-orange-50 text-orange-500",
    label: "Transport Accessibility",
    badge: "5 transit types",
    description:
      "Live positions of metro, RER, bus, tram, and Vélib stations overlaid on the map. See at a glance how connected each zone truly is.",
    icon: (
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.8} className="h-4 w-4">
        <path strokeLinecap="round" strokeLinejoin="round" d="M8.25 18.75a1.5 1.5 0 01-3 0m3 0a1.5 1.5 0 00-3 0m3 0h6m-9 0H3.375a1.125 1.125 0 01-1.125-1.125V14.25m17.25 4.5a1.5 1.5 0 01-3 0m3 0a1.5 1.5 0 00-3 0m3 0h1.125c.621 0 1.129-.504 1.09-1.124a17.902 17.902 0 00-3.213-9.193 2.056 2.056 0 00-1.58-.86H14.25M16.5 18.75h-2.25m0-11.177v-.958c0-.568-.422-1.048-.987-1.106a48.554 48.554 0 00-10.026 0 1.106 1.106 0 00-.987 1.106v7.635m12-6.677v6.677m0 4.5v-4.5m0 0h-12" />
      </svg>
    ),
  },
  {
    photo: PHOTO.park,
    overlay: "from-green-700/85 to-green-500/70",
    iconBg: "bg-green-50 text-green-600",
    label: "Thermal Comfort",
    badge: "heat island data",
    description:
      "Urban heat island analysis based on vegetation density, tree cover, and surface albedo. Identify the coolest zones in the city.",
    icon: (
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.8} className="h-4 w-4">
        <path strokeLinecap="round" strokeLinejoin="round" d="M15.362 5.214A8.252 8.252 0 0112 21 8.25 8.25 0 016.038 7.048 8.287 8.287 0 009 9.6a8.983 8.983 0 013.361-6.867 8.21 8.21 0 003 2.48z" />
        <path strokeLinecap="round" strokeLinejoin="round" d="M12 18a3.75 3.75 0 00.495-7.467 5.99 5.99 0 00-1.925 3.546 5.974 5.974 0 01-2.133-1A3.75 3.75 0 0012 18z" />
      </svg>
    ),
  },
  {
    photo: PHOTO.buildings,
    overlay: "from-purple-700/85 to-purple-500/70",
    iconBg: "bg-purple-50 text-purple-500",
    label: "Housing Affordability",
    badge: "avg 28 €/m²",
    description:
      "Median rent and sale prices per zone, normalised into a 0–10 affordability score. Find where families can realistically afford to live.",
    icon: (
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.8} className="h-4 w-4">
        <path strokeLinecap="round" strokeLinejoin="round" d="M2.25 21h19.5m-18-18v18m10.5-18v18m6-13.5V21M6.75 6.75h.75m-.75 3h.75m-.75 3h.75m3-6h.75m-.75 3h.75m-.75 3h.75M6.75 21v-3.375c0-.621.504-1.125 1.125-1.125h2.25c.621 0 1.125.504 1.125 1.125V21M3 3h12m-.75 4.5H21m-3.75 3.75h.008v.008h-.008v-.008zm0 3h.008v.008h-.008v-.008zm0 3h.008v.008h-.008v-.008z" />
      </svg>
    ),
  },
];

export default function LandingPage() {
  return (
    <div className="min-h-screen bg-white text-[#1d1d1f]">
      {/* ── Navbar ── */}
      <header className="fixed inset-x-0 top-0 z-50 border-b border-white/10 bg-black/30 backdrop-blur-xl">
        <div className="mx-auto flex max-w-6xl items-center justify-between px-6 py-3.5">
          <div className="flex items-center gap-2.5">
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-[#007AFF]">
              <svg viewBox="0 0 24 24" fill="currentColor" className="h-4 w-4 text-white">
                <path fillRule="evenodd" d="M11.54 22.351l.07.04.028.016a.76.76 0 00.723 0l.028-.015.071-.041a16.975 16.975 0 001.144-.742 19.58 19.58 0 002.683-2.282c1.944-2.003 3.5-4.697 3.5-8.318a6.5 6.5 0 00-13 0c0 3.621 1.555 6.315 3.5 8.318a19.58 19.58 0 002.682 2.282 16.975 16.975 0 001.145.742zM12 13.5a3 3 0 100-6 3 3 0 000 6z" clipRule="evenodd" />
              </svg>
            </div>
            <span className="text-sm font-semibold tracking-tight text-white">Urban Data Explorer</span>
          </div>
          <nav className="flex items-center gap-1">
            <Link href="/login" className="rounded-full px-4 py-2 text-sm font-medium text-white/80 transition hover:text-white">
              Sign in
            </Link>
            <Link href="/register" className="rounded-full bg-[#007AFF] px-4 py-2 text-sm font-medium text-white transition hover:bg-[#0071E3]">
              Get started
            </Link>
          </nav>
        </div>
      </header>

      {/* ── Hero — Paris photo background ── */}
      <section
        className="relative flex min-h-screen items-center justify-center overflow-hidden px-6 pt-16"
        style={{
          backgroundImage: `url('${PHOTO.heroNight}')`,
          backgroundSize: "cover",
          backgroundPosition: "center 40%",
        }}
      >
        {/* Gradient overlay for readability */}
        <div className="absolute inset-0 bg-gradient-to-b from-black/55 via-black/45 to-black/75" />

        {/* Subtle vignette edges */}
        <div className="absolute inset-0"
          style={{ background: "radial-gradient(ellipse at center, transparent 50%, rgba(0,0,0,0.4) 100%)" }}
        />

        <div className="relative mx-auto max-w-4xl text-center">
          <div className="mb-6 inline-flex items-center gap-2 rounded-full border border-white/20 bg-white/10 px-4 py-1.5 text-sm font-medium text-white backdrop-blur-sm">
            <span className="h-1.5 w-1.5 rounded-full bg-[#007AFF]" />
            EFREI Paris · Urban Intelligence Project
          </div>

          <h1 className="mb-6 text-6xl font-bold leading-[1.05] tracking-tight text-white md:text-[80px]">
            Discover Paris{" "}
            <span className="bg-gradient-to-r from-[#007AFF] to-[#5AC8FA] bg-clip-text text-transparent">
              like never before
            </span>
          </h1>

          <p className="mx-auto mb-10 max-w-2xl text-lg leading-relaxed text-white/75">
            Explore every neighbourhood through real data — liveability, transport, heat, and housing.
            An interactive map built for families, researchers, and urban planners.
          </p>

          <div className="flex flex-col items-center gap-3 sm:flex-row sm:justify-center">
            <Link
              href="/register"
              className="inline-flex items-center gap-2 rounded-full bg-[#007AFF] px-7 py-3.5 text-sm font-semibold text-white shadow-lg shadow-[#007AFF]/30 transition hover:bg-[#0071E3]"
            >
              Start exploring for free
              <svg viewBox="0 0 20 20" fill="currentColor" className="h-4 w-4">
                <path fillRule="evenodd" d="M3 10a.75.75 0 01.75-.75h10.638L10.23 5.29a.75.75 0 111.04-1.08l5.5 5.25a.75.75 0 010 1.08l-5.5 5.25a.75.75 0 11-1.04-1.08l4.158-3.96H3.75A.75.75 0 013 10z" clipRule="evenodd" />
              </svg>
            </Link>
            <Link
              href="/login"
              className="inline-flex items-center gap-2 rounded-full border border-white/30 bg-white/10 px-7 py-3.5 text-sm font-semibold text-white backdrop-blur-sm transition hover:bg-white/20"
            >
              Sign in
            </Link>
          </div>

          {/* Scroll cue */}
          <div className="mt-20 flex justify-center animate-bounce text-white/40">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2} className="h-6 w-6">
              <path strokeLinecap="round" strokeLinejoin="round" d="M19 9l-7 7-7-7" />
            </svg>
          </div>
        </div>
      </section>

      {/* ── App Preview ── */}
      <section className="bg-white px-6 pb-24 pt-20">
        <div className="mx-auto max-w-5xl">
          <div className="mb-10 text-center">
            <p className="mb-2 text-sm font-semibold uppercase tracking-widest text-[#007AFF]">The platform</p>
            <h2 className="text-3xl font-bold text-[#1d1d1f] md:text-4xl">Everything in one view</h2>
          </div>

          <div
            className="overflow-hidden rounded-2xl"
            style={{ boxShadow: "0 50px 100px rgba(0,0,0,0.18), 0 20px 40px rgba(0,0,0,0.1), 0 0 0 1px rgba(0,0,0,0.07)" }}
          >
            {/* macOS window chrome */}
            <div className="flex items-center gap-2 bg-[#1C1C1E] px-4 py-3">
              <span className="h-3 w-3 rounded-full bg-[#FF5F56]" />
              <span className="h-3 w-3 rounded-full bg-[#FFBD2E]" />
              <span className="h-3 w-3 rounded-full bg-[#27C93F]" />
              <div className="mx-auto w-64 rounded-md bg-white/10 px-3 py-1 text-center text-[11px] text-white/50">
                Urban Data Explorer · Paris
              </div>
            </div>

            <div className="flex" style={{ height: "420px" }}>
              {/* Left rail */}
              <div className="flex w-14 shrink-0 flex-col items-center gap-2.5 border-r border-white/[0.06] bg-[#1d1d1f] pt-4">
                <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-[#007AFF]">
                  <svg className="h-4 w-4 text-white" fill="none" stroke="currentColor" strokeWidth={2} viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" d="M2.25 12l8.954-8.955c.44-.439 1.152-.439 1.591 0L21.75 12M4.5 9.75v10.125c0 .621.504 1.125 1.125 1.125H9.75v-4.875c0-.621.504-1.125 1.125-1.125h2.25c.621 0 1.125.504 1.125 1.125V21h4.125c.621 0 1.125-.504 1.125-1.125V9.75M8.25 21h8.25" />
                  </svg>
                </div>
                {[
                  <path key="t" strokeLinecap="round" strokeLinejoin="round" d="M8.25 18.75a1.5 1.5 0 01-3 0m3 0a1.5 1.5 0 00-3 0m3 0h6m-9 0H3.375a1.125 1.125 0 01-1.125-1.125V14.25m17.25 4.5a1.5 1.5 0 01-3 0m3 0a1.5 1.5 0 00-3 0m3 0h1.125c.621 0 1.129-.504 1.09-1.124a17.902 17.902 0 00-3.213-9.193 2.056 2.056 0 00-1.58-.86H14.25M16.5 18.75h-2.25m0-11.177v-.958c0-.568-.422-1.048-.987-1.106a48.554 48.554 0 00-10.026 0 1.106 1.106 0 00-.987 1.106v7.635m12-6.677v6.677m0 4.5v-4.5m0 0h-12" />,
                  <path key="th" strokeLinecap="round" strokeLinejoin="round" d="M15.362 5.214A8.252 8.252 0 0112 21 8.25 8.25 0 016.038 7.048 8.287 8.287 0 009 9.6a8.983 8.983 0 013.361-6.867 8.21 8.21 0 003 2.48z" />,
                  <path key="h" strokeLinecap="round" strokeLinejoin="round" d="M2.25 21h19.5m-18-18v18m10.5-18v18m6-13.5V21M6.75 6.75h.75m-.75 3h.75m-.75 3h.75m3-6h.75m-.75 3h.75m-.75 3h.75" />,
                ].map((path, i) => (
                  <div key={i} className="flex h-9 w-9 items-center justify-center rounded-xl bg-white/[0.06]">
                    <svg className="h-4 w-4 text-white/40" fill="none" stroke="currentColor" strokeWidth={1.8} viewBox="0 0 24 24">{path}</svg>
                  </div>
                ))}
              </div>

              {/* Map area */}
              <div className="relative flex-1 overflow-hidden bg-[#dde3ea]">
                <div
                  className="absolute inset-0 p-3"
                  style={{ display: "grid", gridTemplateColumns: "repeat(12, 1fr)", gridTemplateRows: "repeat(7, 1fr)", gap: "3px" }}
                >
                  {PARIS_GRID.flatMap((row, r) =>
                    row.map((score, c) => (
                      <div key={`${r}-${c}`} className="rounded-sm"
                        style={{ backgroundColor: scoreColor(score), opacity: score === 0 ? 0 : 0.82 }}
                      />
                    ))
                  )}
                </div>
                <div className="absolute left-3 top-3 rounded-xl bg-white/95 p-2.5 backdrop-blur-sm"
                  style={{ boxShadow: "0 4px 16px rgba(0,0,0,0.12)" }}>
                  <p className="text-[8px] font-semibold uppercase tracking-widest text-[#007AFF]">Best match</p>
                  <p className="mt-0.5 text-[22px] font-bold leading-none text-[#1d1d1f]">9.4</p>
                  <p className="mt-0.5 text-[9px] text-[rgba(60,60,67,0.6)]">Le Marais · 3ème</p>
                </div>
                <div className="absolute bottom-3 left-3 flex items-center gap-1.5 rounded-lg bg-white/90 px-2.5 py-1.5 backdrop-blur-sm">
                  {["#FF453A", "#FF9F0A", "#30D158", "#007AFF"].map((c) => (
                    <span key={c} className="h-2 w-5 rounded-full" style={{ backgroundColor: c }} />
                  ))}
                  <span className="ml-1 text-[8px] text-[rgba(60,60,67,0.6)]">Score 0 → 10</span>
                </div>
              </div>

              {/* Right panel */}
              <div className="w-52 shrink-0 overflow-hidden border-l border-white/[0.06] bg-[#1d1d1f]">
                <div className="p-3">
                  <p className="mb-2.5 text-[9px] font-semibold uppercase tracking-widest text-[#007AFF]">Top Zones</p>
                  <div className="space-y-1">
                    {TOP_ZONES.map((z, i) => (
                      <div key={z.name}
                        className={`flex items-center justify-between rounded-lg px-2.5 py-2 ${i === 0 ? "bg-[#007AFF]/20" : "bg-white/[0.04]"}`}
                      >
                        <div className="min-w-0">
                          <p className="truncate text-[10px] font-medium text-white">{z.name}</p>
                          <p className="text-[8px] text-white/40">{z.arr}</p>
                        </div>
                        <span className={`ml-2 shrink-0 text-[11px] font-semibold ${i === 0 ? "text-[#007AFF]" : "text-white/60"}`}>{z.score}</span>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* ── Features — cards with Paris photo headers ── */}
      <section id="features" className="bg-[#F2F2F7] px-6 py-24">
        <div className="mx-auto max-w-6xl">
          <div className="mb-14 text-center">
            <p className="mb-3 text-sm font-semibold uppercase tracking-widest text-[#007AFF]">What you can explore</p>
            <h2 className="text-3xl font-bold text-[#1d1d1f] md:text-4xl">Four lenses on the city</h2>
            <p className="mt-4 text-[rgba(60,60,67,0.6)]">
              Every indicator is computed from open public datasets and scored 0–10 for easy comparison.
            </p>
          </div>

          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            {features.map((f) => (
              <div
                key={f.label}
                className="overflow-hidden rounded-[18px] bg-white"
                style={{ boxShadow: "0 2px 8px rgba(0,0,0,0.08), 0 0 1px rgba(0,0,0,0.06)" }}
              >
                {/* Photo header with gradient overlay */}
                <div className="relative h-44 overflow-hidden">
                  <img
                    src={f.photo}
                    alt={f.label}
                    className="absolute inset-0 h-full w-full object-cover"
                    loading="lazy"
                  />
                  <div className={`absolute inset-0 bg-gradient-to-br ${f.overlay}`} />
                  {/* Badge */}
                  <div className="absolute right-3 top-3 rounded-full border border-white/25 bg-white/15 px-2.5 py-1 backdrop-blur-sm">
                    <p className="text-[10px] font-semibold text-white">{f.badge}</p>
                  </div>
                  {/* Label at bottom */}
                  <div className="absolute bottom-0 left-0 right-0 bg-gradient-to-t from-black/40 to-transparent px-4 pb-3 pt-6">
                    <p className="text-base font-semibold text-white">{f.label}</p>
                  </div>
                </div>

                {/* Text section */}
                <div className="p-5">
                  <div className={`mb-3 inline-flex h-8 w-8 items-center justify-center rounded-lg ${f.iconBg}`}>
                    {f.icon}
                  </div>
                  <p className="text-sm leading-relaxed text-[rgba(60,60,67,0.6)]">{f.description}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── Paris panoramic photo band ── */}
      <section
        className="relative overflow-hidden py-32 px-6"
        style={{
          backgroundImage: `url('${PHOTO.aerialDay}')`,
          backgroundSize: "cover",
          backgroundPosition: "center 60%",
          backgroundAttachment: "fixed",
        }}
      >
        <div className="absolute inset-0 bg-gradient-to-r from-black/70 via-black/50 to-transparent" />
        <div className="relative mx-auto max-w-6xl">
          <div className="max-w-lg">
            <p className="mb-3 text-sm font-semibold uppercase tracking-widest text-[#007AFF]">Open data</p>
            <h2 className="mb-4 text-4xl font-bold leading-tight text-white md:text-5xl">
              Paris from a<br />new perspective
            </h2>
            <p className="mb-8 text-lg leading-relaxed text-white/70">
              80+ neighbourhoods. 4 indicators. Built entirely on publicly available data from Paris Open Data, INSEE, and RATP.
            </p>
            <Link
              href="/register"
              className="inline-flex items-center gap-2 rounded-full bg-[#007AFF] px-7 py-3.5 text-sm font-semibold text-white shadow-lg shadow-[#007AFF]/30 transition hover:bg-[#0071E3]"
            >
              Explore the map
              <svg viewBox="0 0 20 20" fill="currentColor" className="h-4 w-4">
                <path fillRule="evenodd" d="M3 10a.75.75 0 01.75-.75h10.638L10.23 5.29a.75.75 0 111.04-1.08l5.5 5.25a.75.75 0 010 1.08l-5.5 5.25a.75.75 0 11-1.04-1.08l4.158-3.96H3.75A.75.75 0 013 10z" clipRule="evenodd" />
              </svg>
            </Link>
          </div>
        </div>
      </section>

      {/* ── Stats strip ── */}
      <section className="border-y border-[rgba(60,60,67,0.12)] bg-white px-6 py-14">
        <div className="mx-auto grid max-w-4xl grid-cols-2 gap-10 md:grid-cols-4">
          {stats.map((s) => (
            <div key={s.label} className="text-center">
              <p className="text-4xl font-bold text-[#007AFF]">{s.value}</p>
              <p className="mt-1 text-sm text-[rgba(60,60,67,0.6)]">{s.label}</p>
            </div>
          ))}
        </div>
      </section>

      {/* ── CTA ── */}
      <section className="bg-[#F2F2F7] px-6 py-24">
        <div
          className="mx-auto max-w-2xl overflow-hidden rounded-[18px] bg-white p-12 text-center"
          style={{ boxShadow: "0 2px 8px rgba(0,0,0,0.08), 0 0 1px rgba(0,0,0,0.06)" }}
        >
          <div className="mx-auto mb-6 flex h-16 w-16 items-center justify-center rounded-2xl bg-[#007AFF]">
            <svg viewBox="0 0 24 24" fill="currentColor" className="h-8 w-8 text-white">
              <path fillRule="evenodd" d="M11.54 22.351l.07.04.028.016a.76.76 0 00.723 0l.028-.015.071-.041a16.975 16.975 0 001.144-.742 19.58 19.58 0 002.683-2.282c1.944-2.003 3.5-4.697 3.5-8.318a6.5 6.5 0 00-13 0c0 3.621 1.555 6.315 3.5 8.318a19.58 19.58 0 002.682 2.282 16.975 16.975 0 001.145.742zM12 13.5a3 3 0 100-6 3 3 0 000 6z" clipRule="evenodd" />
            </svg>
          </div>
          <h2 className="mb-4 text-3xl font-bold text-[#1d1d1f]">Ready to explore Paris?</h2>
          <p className="mb-8 text-[rgba(60,60,67,0.6)]">
            Create a free account and start discovering which neighbourhoods fit your needs.
          </p>
          <Link
            href="/register"
            className="inline-flex items-center gap-2 rounded-full bg-[#007AFF] px-8 py-3.5 text-sm font-semibold text-white transition hover:bg-[#0071E3]"
          >
            Get started — it&apos;s free
            <svg viewBox="0 0 20 20" fill="currentColor" className="h-4 w-4">
              <path fillRule="evenodd" d="M3 10a.75.75 0 01.75-.75h10.638L10.23 5.29a.75.75 0 111.04-1.08l5.5 5.25a.75.75 0 010 1.08l-5.5 5.25a.75.75 0 11-1.04-1.08l4.158-3.96H3.75A.75.75 0 013 10z" clipRule="evenodd" />
            </svg>
          </Link>
        </div>
      </section>

      {/* ── Footer ── */}
      <footer className="border-t border-[rgba(60,60,67,0.12)] bg-white px-6 py-8">
        <div className="mx-auto flex max-w-6xl flex-col items-center justify-between gap-4 text-sm text-[rgba(60,60,67,0.6)] md:flex-row">
          <div className="flex items-center gap-2">
            <div className="flex h-6 w-6 items-center justify-center rounded-md bg-[#007AFF]">
              <svg viewBox="0 0 24 24" fill="currentColor" className="h-3 w-3 text-white">
                <path fillRule="evenodd" d="M11.54 22.351l.07.04.028.016a.76.76 0 00.723 0l.028-.015.071-.041a16.975 16.975 0 001.144-.742 19.58 19.58 0 002.683-2.282c1.944-2.003 3.5-4.697 3.5-8.318a6.5 6.5 0 00-13 0c0 3.621 1.555 6.315 3.5 8.318a19.58 19.58 0 002.682 2.282 16.975 16.975 0 001.145.742zM12 13.5a3 3 0 100-6 3 3 0 000 6z" clipRule="evenodd" />
              </svg>
            </div>
            <span className="font-medium text-[#1d1d1f]">Urban Data Explorer</span>
          </div>
          <p>EFREI Paris — M1 Group Project · {new Date().getFullYear()}</p>
        </div>
      </footer>
    </div>
  );
}
