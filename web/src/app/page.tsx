import Link from "next/link";

/* ──────────────────────────────────────────────────────────────────────────
   Urban Data Explorer — landing page
   Design read: civic-tech / data-journalism, editorial-data language.
   Dials: VARIANCE 7 · MOTION 4 (CSS scroll-reveal, reduced-motion safe) · DENSITY 3.
   Brand accent #007AFF preserved (shared with the dashboard). One accent, locked.
   Radius rule: buttons = pill · cards/tiles = rounded-2xl · chips = rounded-lg.
   ────────────────────────────────────────────────────────────────────────── */

// Paris photography (Unsplash — open-license, embeddable).
const PHOTO = {
  heroNight:
    "https://images.unsplash.com/photo-1502602898657-3e91760cbb34?auto=format&fit=crop&w=1920&q=85",
  aerialDay:
    "https://images.unsplash.com/photo-1499856871958-5b9627545d1a?auto=format&fit=crop&w=1920&q=85",
  neighborhood:
    "https://images.unsplash.com/photo-1431274172761-fca41d930114?auto=format&fit=crop&w=1200&q=85",
};

const stats = [
  { value: "80+", label: "Paris zones" },
  { value: "4", label: "Core indicators" },
  { value: "8", label: "Liveability pillars" },
  { value: "100%", label: "Open data" },
];

// Three secondary lenses (the flagship, Vivabilité, gets its own tile above).
const lenses = [
  {
    label: "Transport access",
    description:
      "Metro, RER, tram, bus, and Vélib stops scored into a single connectivity index per zone.",
    icon: (
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.6} className="h-5 w-5">
        <path strokeLinecap="round" strokeLinejoin="round" d="M8.25 18.75a1.5 1.5 0 01-3 0m3 0a1.5 1.5 0 00-3 0m3 0h6m-9 0H3.375a1.125 1.125 0 01-1.125-1.125V14.25m17.25 4.5a1.5 1.5 0 01-3 0m3 0a1.5 1.5 0 00-3 0m3 0h1.125c.621 0 1.129-.504 1.09-1.124a17.902 17.902 0 00-3.213-9.193 2.056 2.056 0 00-1.58-.86H14.25M16.5 18.75h-2.25m0-11.177v-.958c0-.568-.422-1.048-.987-1.106a48.554 48.554 0 00-10.026 0 1.106 1.106 0 00-.987 1.106v7.635m12-6.677v6.677m0 4.5v-4.5m0 0h-12" />
      </svg>
    ),
  },
  {
    label: "Thermal comfort",
    description:
      "Urban heat-island exposure from vegetation density, tree cover, and surface albedo.",
    icon: (
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.6} className="h-5 w-5">
        <path strokeLinecap="round" strokeLinejoin="round" d="M15.362 5.214A8.252 8.252 0 0112 21 8.25 8.25 0 016.038 7.048 8.287 8.287 0 009 9.6a8.983 8.983 0 013.361-6.867 8.21 8.21 0 003 2.48z" />
        <path strokeLinecap="round" strokeLinejoin="round" d="M12 18a3.75 3.75 0 00.495-7.467 5.99 5.99 0 00-1.925 3.546 5.974 5.974 0 01-2.133-1A3.75 3.75 0 0012 18z" />
      </svg>
    ),
  },
  {
    label: "Housing affordability",
    description:
      "Median rent and sale prices per square metre, normalised against local income into a 0-10 score.",
    icon: (
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.6} className="h-5 w-5">
        <path strokeLinecap="round" strokeLinejoin="round" d="M2.25 21h19.5m-18-18v18m10.5-18v18m6-13.5V21M6.75 6.75h.75m-.75 3h.75m-.75 3h.75m3-6h.75m-.75 3h.75m-.75 3h.75M6.75 21v-3.375c0-.621.504-1.125 1.125-1.125h2.25c.621 0 1.125.504 1.125 1.125V21M3 3h12m-.75 4.5H21m-3.75 3.75h.008v.008h-.008v-.008zm0 3h.008v.008h-.008v-.008zm0 3h.008v.008h-.008v-.008z" />
      </svg>
    ),
  },
];

export default function LandingPage() {
  return (
    <div className="min-h-screen bg-white text-[#1d1d1f]">
      {/* ── Nav ── */}
      <header className="fixed inset-x-0 top-0 z-50 border-b border-white/10 bg-black/30 backdrop-blur-xl">
        <div className="mx-auto flex h-16 max-w-6xl items-center justify-between px-6">
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
              Start exploring
            </Link>
          </nav>
        </div>
      </header>

      {/* ── Hero — left-aligned over Paris at night ── */}
      <section
        className="relative flex min-h-[100dvh] items-center overflow-hidden px-6 pt-16"
        style={{
          backgroundImage: `url('${PHOTO.heroNight}')`,
          backgroundSize: "cover",
          backgroundPosition: "center 40%",
        }}
      >
        <div className="absolute inset-0 bg-gradient-to-r from-black/80 via-black/55 to-black/35" />

        <div className="relative mx-auto w-full max-w-6xl">
          <div className="max-w-2xl">
            <p className="mb-6 inline-flex items-center gap-2 rounded-full border border-white/20 bg-white/10 px-4 py-1.5 text-xs font-medium tracking-wide text-white backdrop-blur-sm">
              <span className="h-1.5 w-1.5 rounded-full bg-[#007AFF]" />
              EFREI Paris · Urban Intelligence Project
            </p>

            <h1 className="text-balance text-5xl font-bold leading-[1.04] tracking-[-0.02em] text-white sm:text-6xl md:text-7xl">
              Every Paris neighbourhood, <span className="text-[#5AC8FA]">measured</span>.
            </h1>

            <p className="mt-6 max-w-xl text-lg leading-relaxed text-white/80">
              Liveability, transport, heat, and housing: eight pillars of open data on one
              interactive map.
            </p>

            <div className="mt-9 flex flex-col gap-3 sm:flex-row">
              <Link
                href="/register"
                className="inline-flex items-center justify-center gap-2 rounded-full bg-[#007AFF] px-7 py-3.5 text-sm font-semibold text-white transition hover:bg-[#0071E3] active:translate-y-px"
              >
                Start exploring
                <svg viewBox="0 0 20 20" fill="currentColor" className="h-4 w-4">
                  <path fillRule="evenodd" d="M3 10a.75.75 0 01.75-.75h10.638L10.23 5.29a.75.75 0 111.04-1.08l5.5 5.25a.75.75 0 010 1.08l-5.5 5.25a.75.75 0 11-1.04-1.08l4.158-3.96H3.75A.75.75 0 013 10z" clipRule="evenodd" />
                </svg>
              </Link>
              <Link
                href="/login"
                className="inline-flex items-center justify-center rounded-full border border-white/30 bg-white/10 px-7 py-3.5 text-sm font-semibold text-white backdrop-blur-sm transition hover:bg-white/20"
              >
                Sign in
              </Link>
            </div>
          </div>
        </div>
      </section>

      {/* ── Product showcase — real full-UI dashboard screenshot ── */}
      <section className="bg-white px-6 py-24 md:py-28">
        <div className="mx-auto max-w-6xl">
          <div className="reveal mx-auto max-w-2xl text-center">
            <p className="text-xs font-semibold uppercase tracking-[0.18em] text-[#007AFF]">The platform</p>
            <h2 className="mt-3 text-3xl font-bold tracking-[-0.02em] text-[#1d1d1f] md:text-[40px] md:leading-[1.1]">
              Everything in one view
            </h2>
            <p className="mx-auto mt-4 max-w-lg text-[15px] leading-relaxed text-[rgba(60,60,67,0.7)]">
              Pick an indicator, read every neighbourhood off the map, and open any zone for its full
              breakdown. Scores normalised to 0-10, so comparing two arrondissements takes a second.
            </p>
          </div>

          <figure className="reveal mt-12">
            <div className="overflow-hidden rounded-2xl border border-[rgba(0,0,0,0.08)] shadow-[0_30px_60px_rgba(0,0,0,0.12),0_8px_20px_rgba(0,0,0,0.06)]">
              <img
                src="/ude-dashboard.jpg"
                alt="The Urban Data Explorer dashboard: a Paris choropleth coloured by family-liveability score, with an indicator sidebar and a per-zone detail panel"
                className="block h-auto w-full"
                width={2880}
                height={1640}
                loading="lazy"
              />
            </div>
            <figcaption className="mt-4 text-center text-[12px] leading-relaxed text-[rgba(60,60,67,0.55)]">
              The live dashboard: family-liveability scores across every Paris IRIS zone.
            </figcaption>
          </figure>
        </div>
      </section>

      {/* ── Four lenses — flagship tile + a divided trio ── */}
      <section id="features" className="bg-[#f5f5f7] px-6 py-24 md:py-28">
        <div className="mx-auto max-w-6xl">
          <div className="reveal max-w-2xl">
            <p className="text-xs font-semibold uppercase tracking-[0.18em] text-[#007AFF]">What you can explore</p>
            <h2 className="mt-3 text-3xl font-bold tracking-[-0.02em] text-[#1d1d1f] md:text-[40px] md:leading-[1.1]">
              Four lenses on the city
            </h2>
          </div>

          {/* Flagship — Vivabilité (wide split tile) */}
          <div className="reveal mt-12 grid overflow-hidden rounded-2xl bg-white shadow-[var(--apple-shadow-card)] md:grid-cols-2">
            <div className="relative min-h-[240px] overflow-hidden md:min-h-[320px]">
              <img
                src={PHOTO.neighborhood}
                alt="A residential street in central Paris"
                className="absolute inset-0 h-full w-full object-cover"
                loading="lazy"
              />
              <div className="absolute inset-0 bg-gradient-to-t from-black/45 via-black/10 to-transparent" />
            </div>
            <div className="flex flex-col justify-center gap-4 p-8 md:p-10">
              <div className="inline-flex h-9 w-9 items-center justify-center rounded-lg bg-[#007AFF]/10 text-[#007AFF]">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.6} className="h-5 w-5">
                  <path strokeLinecap="round" strokeLinejoin="round" d="M2.25 12l8.954-8.955c.44-.439 1.152-.439 1.591 0L21.75 12M4.5 9.75v10.125c0 .621.504 1.125 1.125 1.125H9.75v-4.875c0-.621.504-1.125 1.125-1.125h2.25c.621 0 1.125.504 1.125 1.125V21h4.125c.621 0 1.125-.504 1.125-1.125V9.75M8.25 21h8.25" />
                </svg>
              </div>
              <h3 className="text-2xl font-semibold tracking-[-0.01em] text-[#1d1d1f]">Vivabilité familiale</h3>
              <p className="max-w-md text-[15px] leading-relaxed text-[rgba(60,60,67,0.7)]">
                The flagship composite. Eight weighted pillars (schools, childcare, safety, healthcare,
                green space, transport, daily services, and environment) folded into one
                family-liveability score per neighbourhood.
              </p>
            </div>
          </div>

          {/* Trio — grouped by hairlines, not boxed cards */}
          <div className="reveal mt-4 grid overflow-hidden rounded-2xl bg-white shadow-[var(--apple-shadow-card)] md:grid-cols-3 md:divide-x md:divide-[rgba(0,0,0,0.07)]">
            {lenses.map((lens) => (
              <div key={lens.label} className="flex flex-col gap-3 p-8">
                <div className="inline-flex h-9 w-9 items-center justify-center rounded-lg bg-[#007AFF]/10 text-[#007AFF]">
                  {lens.icon}
                </div>
                <h3 className="text-[17px] font-semibold text-[#1d1d1f]">{lens.label}</h3>
                <p className="text-[14px] leading-relaxed text-[rgba(60,60,67,0.7)]">{lens.description}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── Open-data band ── */}
      <section
        className="relative overflow-hidden px-6 py-32"
        style={{
          backgroundImage: `url('${PHOTO.aerialDay}')`,
          backgroundSize: "cover",
          backgroundPosition: "center 60%",
        }}
      >
        <div className="absolute inset-0 bg-gradient-to-r from-black/80 via-black/55 to-transparent" />
        <div className="relative mx-auto max-w-6xl">
          <div className="max-w-lg">
            <h2 className="text-4xl font-bold leading-[1.1] tracking-[-0.02em] text-white md:text-5xl">
              Paris, from a new perspective
            </h2>
            <p className="mt-5 max-w-md text-lg leading-relaxed text-white/75">
              Eighty-plus neighbourhoods and four indicators, built entirely on public data from Paris
              Open Data, INSEE, and RATP.
            </p>
            <Link
              href="/register"
              className="mt-8 inline-flex items-center gap-2 rounded-full bg-[#007AFF] px-7 py-3.5 text-sm font-semibold text-white transition hover:bg-[#0071E3] active:translate-y-px"
            >
              Start exploring
              <svg viewBox="0 0 20 20" fill="currentColor" className="h-4 w-4">
                <path fillRule="evenodd" d="M3 10a.75.75 0 01.75-.75h10.638L10.23 5.29a.75.75 0 111.04-1.08l5.5 5.25a.75.75 0 010 1.08l-5.5 5.25a.75.75 0 11-1.04-1.08l4.158-3.96H3.75A.75.75 0 013 10z" clipRule="evenodd" />
              </svg>
            </Link>
          </div>
        </div>
      </section>

      {/* ── Stats ── */}
      <section className="border-y border-[rgba(0,0,0,0.08)] bg-white px-6 py-16">
        <div className="mx-auto grid max-w-4xl grid-cols-2 gap-10 md:grid-cols-4">
          {stats.map((s) => (
            <div key={s.label} className="text-center">
              <p className="text-4xl font-bold tracking-[-0.02em] text-[#007AFF] md:text-5xl">{s.value}</p>
              <p className="mt-2 text-sm text-[rgba(60,60,67,0.6)]">{s.label}</p>
            </div>
          ))}
        </div>
      </section>

      {/* ── Closing CTA ── */}
      <section className="bg-[#f5f5f7] px-6 py-24 md:py-28">
        <div className="reveal mx-auto max-w-3xl text-center">
          <h2 className="text-3xl font-bold tracking-[-0.02em] text-[#1d1d1f] md:text-4xl">
            Find the neighbourhood that fits
          </h2>
          <p className="mx-auto mt-4 max-w-md text-[15px] leading-relaxed text-[rgba(60,60,67,0.7)]">
            Create a free account and compare any two arrondissements across all eight pillars.
          </p>
          <Link
            href="/register"
            className="mt-8 inline-flex items-center gap-2 rounded-full bg-[#007AFF] px-8 py-3.5 text-sm font-semibold text-white transition hover:bg-[#0071E3] active:translate-y-px"
          >
            Start exploring
            <svg viewBox="0 0 20 20" fill="currentColor" className="h-4 w-4">
              <path fillRule="evenodd" d="M3 10a.75.75 0 01.75-.75h10.638L10.23 5.29a.75.75 0 111.04-1.08l5.5 5.25a.75.75 0 010 1.08l-5.5 5.25a.75.75 0 11-1.04-1.08l4.158-3.96H3.75A.75.75 0 013 10z" clipRule="evenodd" />
            </svg>
          </Link>
        </div>
      </section>

      {/* ── Footer ── */}
      <footer className="border-t border-[rgba(0,0,0,0.08)] bg-white px-6 py-8">
        <div className="mx-auto flex max-w-6xl flex-col items-center justify-between gap-4 text-sm text-[rgba(60,60,67,0.6)] md:flex-row">
          <div className="flex items-center gap-2">
            <div className="flex h-6 w-6 items-center justify-center rounded-md bg-[#007AFF]">
              <svg viewBox="0 0 24 24" fill="currentColor" className="h-3 w-3 text-white">
                <path fillRule="evenodd" d="M11.54 22.351l.07.04.028.016a.76.76 0 00.723 0l.028-.015.071-.041a16.975 16.975 0 001.144-.742 19.58 19.58 0 002.683-2.282c1.944-2.003 3.5-4.697 3.5-8.318a6.5 6.5 0 00-13 0c0 3.621 1.555 6.315 3.5 8.318a19.58 19.58 0 002.682 2.282 16.975 16.975 0 001.145.742zM12 13.5a3 3 0 100-6 3 3 0 000 6z" clipRule="evenodd" />
              </svg>
            </div>
            <span className="font-medium text-[#1d1d1f]">Urban Data Explorer</span>
          </div>
          <p>EFREI Paris - M1 Group Project · {new Date().getFullYear()}</p>
        </div>
      </footer>
    </div>
  );
}
