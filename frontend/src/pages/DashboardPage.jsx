import { useEffect, useMemo, useState } from "react";
import {
  Activity,
  Bot,
  Clock3,
  Database,
  Fingerprint,
  Globe2,
  Languages,
  RefreshCcw,
  ShieldAlert,
  Sparkles
} from "lucide-react";
import { getAnalyticsOverview, getEscalations, getIdentityAmbiguityQueue, getRecentQueries } from "../services/api";

function SkeletonBlock({ rows = 3, height = "h-8" }) {
  return (
    <div className="space-y-2">
      {Array.from({ length: rows }).map((_, i) => (
        <div key={i} className={`${height} animate-pulse rounded-md bg-gradient-to-r from-slate-200/80 via-slate-100/90 to-slate-200/80`} />
      ))}
    </div>
  );
}

function ConfidenceBadge({ value }) {
  const v = Number.isFinite(value) ? value : 0;
  const style = v >= 85 ? "bg-emerald-100 text-emerald-700" : v >= 65 ? "bg-sky-100 text-sky-700" : "bg-rose-100 text-rose-700";
  return <span className={`rounded-full px-2 py-0.5 text-xs font-semibold ${style}`}>{Math.round(v)}%</span>;
}

function LatencyBadge({ ms }) {
  const value = Number(ms || 0);
  const style = value < 1500 ? "bg-emerald-100 text-emerald-700" : value <= 3000 ? "bg-sky-100 text-sky-700" : "bg-rose-100 text-rose-700";
  return <span className={`rounded-full px-2 py-0.5 text-xs font-semibold ${style}`}>{value}ms</span>;
}

function StatusBadge({ value }) {
  const normalized = String(value || "open").toLowerCase();
  const label = normalized.replaceAll("_", " ");
  const style =
    normalized === "resolved"
      ? "bg-emerald-100 text-emerald-700"
      : normalized === "in_progress"
        ? "bg-sky-100 text-sky-700"
        : "bg-rose-100 text-rose-700";
  return <span className={`rounded-full px-2 py-0.5 text-xs font-semibold capitalize ${style}`}>{label}</span>;
}

function KpiCard({ title, value, subtitle, tone = "slate" }) {
  const toneClass = {
    slate: "text-slate-900",
    green: "text-emerald-700",
    rose: "text-rose-700",
    amber: "text-amber-700",
    sky: "text-sky-700"
  }[tone];
  return (
    <article className="surface-card rounded-xl p-3.5 transition-all duration-200">
      <p className="text-[11px] uppercase tracking-[0.12em] text-slate-500">{title}</p>
      <p className={`mt-1 text-2xl font-semibold leading-tight ${toneClass}`}>{value}</p>
      {subtitle ? <p className="mt-1 text-xs text-slate-500">{subtitle}</p> : null}
    </article>
  );
}

function HealthItem({ icon: Icon, label, active }) {
  return (
    <div className={`rounded-lg border px-2.5 py-2 text-xs ${active ? "border-emerald-200 bg-emerald-50 text-emerald-800" : "border-slate-200 bg-slate-50 text-slate-600"}`}>
      <p className="inline-flex items-center gap-1 font-semibold">
        <Icon size={12} />
        {label}
      </p>
      <p className="mt-1">{active ? "Operational" : "Unavailable"}</p>
    </div>
  );
}

function buildActivityFeed(recentItems = []) {
  return recentItems.slice(0, 20).map((q) => {
    const lang = String(q.language || "english").toLowerCase();
    const normalized = Boolean(q.normalized_for_workflow);
    const severity = String(q.escalation_severity || "");
    let event = `${q.intent} query resolved`;
    if (severity === "Escalated" || q.escalated) event = "Escalation triggered";
    else if (severity === "Support Review Recommended") event = "Support review recommended";
    else if (q.intent === "DASHBOARD_ACCESS") event = "Dashboard issue auto-resolved";
    else if (q.intent === "ROYALTY") event = "Royalty query resolved";

    if (normalized && lang === "hinglish") event = "Hinglish query normalized";
    if (q.status === "support_review_recommended") event = "Identity ambiguity detected";

    return {
      id: q.id,
      event,
      detail: q.message,
      at: q.created_at,
      severity: severity || (q.escalated ? "Escalated" : "Auto Resolved"),
    };
  });
}

function DashboardPage({ refreshKey, onRefresh, health }) {
  const [loading, setLoading] = useState(true);
  const [overview, setOverview] = useState(null);
  const [recent, setRecent] = useState({ items: [], top_intents: [], confidence_trend: [] });
  const [escalations, setEscalations] = useState({ items: [] });
  const [ambiguityQueue, setAmbiguityQueue] = useState({ items: [] });
  const [error, setError] = useState("");
  const [lastUpdated, setLastUpdated] = useState("");

  useEffect(() => {
    let mounted = true;
    const load = async () => {
      setLoading(true);
      setError("");
      try {
        const [o, r, e, a] = await Promise.all([getAnalyticsOverview(), getRecentQueries(40), getEscalations(40), getIdentityAmbiguityQueue(40)]);
        if (!mounted) return;
        setOverview(o);
        setRecent(r);
        setEscalations(e);
        setAmbiguityQueue(a);
        setLastUpdated(new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit", second: "2-digit" }));
      } catch (err) {
        if (!mounted) return;
        setError(err.message || "Unable to load operations dashboard.");
      } finally {
        if (mounted) setLoading(false);
      }
    };
    load();
    return () => {
      mounted = false;
    };
  }, [refreshKey]);

  const metrics = useMemo(() => {
    const rows = recent.items || [];
    const total = overview?.total_queries ?? rows.length;
    const autoResolved = rows.filter((q) => (q.escalation_severity || "") === "Auto Resolved" || (q.status === "resolved" && !q.escalated)).length;
    const supportReviews = rows.filter((q) => (q.escalation_severity || "") === "Support Review Recommended" || q.status === "support_review_recommended").length;
    const escalatedCases = rows.filter((q) => (q.escalation_severity || "") === "Escalated" || q.escalated).length || (overview?.escalations ?? 0);
    const avgConfidence = rows.length ? rows.reduce((sum, q) => sum + Number(q.confidence || 0), 0) / rows.length : (overview?.avg_confidence ?? 0);

    const latencyValues = rows.map((q) => Number(q.latency_ms || 0)).filter((v) => Number.isFinite(v) && v > 0);
    const avgLatency = latencyValues.length ? Math.round(latencyValues.reduce((a, b) => a + b, 0) / latencyValues.length) : 0;
    const fastest = latencyValues.length ? Math.min(...latencyValues) : 0;
    const slowest = latencyValues.length ? Math.max(...latencyValues) : 0;

    const langs = { english: 0, hindi: 0, hinglish: 0 };
    rows.forEach((q) => {
      const k = String(q.language || "english").toLowerCase();
      if (k in langs) langs[k] += 1;
      else langs.english += 1;
    });

    return { total, autoResolved, supportReviews, escalatedCases, avgConfidence, avgLatency, fastest, slowest, langs };
  }, [overview, recent.items]);

  const activityFeed = useMemo(() => buildActivityFeed(recent.items), [recent.items]);

  return (
    <div className="space-y-3">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <div>
          <h2 className="text-xl font-semibold md:text-2xl">AI Operations Control Center</h2>
          <p className="text-xs text-slate-500 md:text-sm">Live publishing support monitoring across intent routing, identity matching, confidence, and escalation operations.</p>
        </div>
        <div className="flex items-center gap-2">
          <button
            type="button"
            onClick={onRefresh}
            className="inline-flex items-center gap-2 rounded-lg border border-slate-200 bg-white px-3 py-2 text-xs font-semibold text-slate-700 transition-all hover:-translate-y-0.5 hover:bg-slate-50 hover:shadow"
          >
            <RefreshCcw size={14} />
            Refresh
          </button>
          <span className="text-xs text-slate-500">Updated: {lastUpdated || "--:--:--"}</span>
        </div>
      </div>

      {error ? <div className="rounded-lg border border-amber-300 bg-amber-50 px-3 py-2 text-sm text-amber-800">Support dashboard is temporarily unavailable. {error}</div> : null}

      <section className="grid gap-2 sm:grid-cols-2 xl:grid-cols-3 2xl:grid-cols-6">
        {loading ? (
          <SkeletonBlock rows={6} />
        ) : (
          <>
            <KpiCard title="Total Queries" value={metrics.total} subtitle="Across all support channels" />
            <KpiCard title="Auto Resolved" value={metrics.autoResolved} subtitle="Resolved by AI workflow" tone="green" />
            <KpiCard title="Support Reviews" value={metrics.supportReviews} subtitle="Pending support validation" tone="amber" />
            <KpiCard title="Escalated Cases" value={metrics.escalatedCases} subtitle="Specialist intervention" tone="rose" />
            <KpiCard title="Avg Confidence" value={`${Math.round(metrics.avgConfidence)}%`} subtitle="Overall query confidence" tone="sky" />
            <KpiCard title="Avg Latency" value={`${metrics.avgLatency}ms`} subtitle="Workflow response speed" tone="slate" />
          </>
        )}
      </section>

      <section className="grid gap-3 xl:grid-cols-[1.3fr_1fr]">
        <article className="surface-card rounded-xl p-3.5">
          <h3 className="mb-2 text-[11px] font-semibold uppercase tracking-[0.12em] text-slate-500">Live Activity Feed</h3>
          {loading ? (
            <SkeletonBlock rows={6} />
          ) : activityFeed.length === 0 ? (
            <p className="text-sm text-slate-500">No activity yet. New support events will appear here in real time.</p>
          ) : (
            <div className="max-h-64 space-y-1.5 overflow-auto pr-1">
              {activityFeed.map((evt) => (
                <div key={evt.id} className="rounded-lg border border-slate-200 bg-slate-50 px-3 py-2 text-xs transition-all duration-300 hover:bg-white">
                  <div className="flex items-center justify-between gap-2">
                    <p className="font-semibold text-slate-800">{evt.event}</p>
                    <span className="text-slate-500">{new Date(evt.at).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}</span>
                  </div>
                  <p className="mt-1 line-clamp-1 text-slate-600">{evt.detail}</p>
                </div>
              ))}
            </div>
          )}
        </article>

        <article className="surface-card rounded-xl p-3.5">
          <h3 className="mb-2 text-[11px] font-semibold uppercase tracking-[0.12em] text-slate-500">AI Operational Health</h3>
          <div className="grid grid-cols-2 gap-2">
            <HealthItem icon={Bot} label="AI Engine" active={health?.ai_active ?? overview?.health?.ai_active} />
            <HealthItem icon={Database} label="PostgreSQL" active={health?.db_connected ?? overview?.health?.db_connected} />
            <HealthItem icon={Sparkles} label="RAG Retrieval" active={health?.rag_enabled ?? overview?.health?.rag_enabled ?? true} />
            <HealthItem icon={ShieldAlert} label="Escalation Monitoring" active={health?.escalation_monitoring_enabled ?? overview?.health?.escalation_monitoring_enabled} />
            <HealthItem icon={Languages} label="Query Normalizer" active={overview?.health?.query_normalizer_enabled ?? true} />
            <HealthItem icon={Fingerprint} label="Identity Resolution Engine" active={overview?.health?.identity_resolution_enabled ?? true} />
          </div>
        </article>
      </section>

      <section className="grid gap-3 xl:grid-cols-3">
        <article className="surface-card rounded-xl p-3.5">
          <h3 className="mb-2 text-[11px] font-semibold uppercase tracking-[0.12em] text-slate-500">Top Support Intents</h3>
          {loading ? <SkeletonBlock rows={5} height="h-6" /> : (
            <div className="space-y-1.5">
              {(recent.top_intents || []).slice(0, 5).map((item) => (
                <div key={item.intent} className="flex items-center justify-between rounded-md bg-slate-50 px-2.5 py-2 text-xs">
                  <span className="font-medium text-slate-700">{item.intent}</span>
                  <span className="font-semibold text-slate-900">{item.count}</span>
                </div>
              ))}
              {(recent.top_intents || []).length === 0 ? <p className="text-sm text-slate-500">Intent analytics will appear after live traffic starts.</p> : null}
            </div>
          )}
        </article>

        <article className="surface-card rounded-xl p-3.5">
          <h3 className="mb-2 text-[11px] font-semibold uppercase tracking-[0.12em] text-slate-500">Multilingual Analytics</h3>
          {loading ? <SkeletonBlock rows={3} height="h-7" /> : (
            <div className="space-y-1.5">
              <div className="flex items-center justify-between rounded-md bg-slate-50 px-2.5 py-2 text-xs"><span className="inline-flex items-center gap-1"><Globe2 size={12} /> English queries</span><span className="font-semibold">{metrics.langs.english}</span></div>
              <div className="flex items-center justify-between rounded-md bg-slate-50 px-2.5 py-2 text-xs"><span>Hindi queries</span><span className="font-semibold">{metrics.langs.hindi}</span></div>
              <div className="flex items-center justify-between rounded-md bg-slate-50 px-2.5 py-2 text-xs"><span>Hinglish queries</span><span className="font-semibold">{metrics.langs.hinglish}</span></div>
            </div>
          )}
        </article>

        <article className="surface-card rounded-xl p-3.5">
          <h3 className="mb-2 text-[11px] font-semibold uppercase tracking-[0.12em] text-slate-500">Latency Analytics</h3>
          {loading ? <SkeletonBlock rows={3} height="h-7" /> : (
            <div className="space-y-1.5 text-xs">
              <div className="flex items-center justify-between rounded-md bg-slate-50 px-2.5 py-2"><span>Average latency</span><LatencyBadge ms={metrics.avgLatency} /></div>
              <div className="flex items-center justify-between rounded-md bg-slate-50 px-2.5 py-2"><span>Fastest workflow</span><LatencyBadge ms={metrics.fastest} /></div>
              <div className="flex items-center justify-between rounded-md bg-slate-50 px-2.5 py-2"><span>Slowest workflow</span><LatencyBadge ms={metrics.slowest} /></div>
            </div>
          )}
        </article>
      </section>

      <section className="grid gap-3 xl:grid-cols-[1.2fr_1fr]">
        <article className="surface-card rounded-xl p-3.5">
          <h3 className="mb-2 text-[11px] font-semibold uppercase tracking-[0.12em] text-slate-500">Escalation Management</h3>
          {loading ? <SkeletonBlock rows={6} /> : escalations.items.length === 0 ? (
            <p className="text-sm text-slate-500">No active escalations. Queue is clear.</p>
          ) : (
            <div className="max-h-72 space-y-2 overflow-y-auto pr-1">
              {escalations.items.map((row) => (
                <div key={row.id} className="rounded-lg border border-slate-200 bg-slate-50 p-2.5 text-xs">
                  <div className="flex items-center justify-between gap-2">
                    <p className="truncate font-semibold text-slate-800">{row.customer_email || "unknown"}</p>
                    <StatusBadge value={row.status} />
                  </div>
                  <p className="mt-1 truncate text-slate-700">{row.intent || row.reason || "support_issue"}</p>
                  <div className="mt-1.5 grid grid-cols-2 gap-1 text-slate-600 sm:grid-cols-4">
                    <div className="inline-flex items-center gap-1">
                      <span>Confidence</span>
                      <ConfidenceBadge value={row.confidence || 0} />
                    </div>
                    <p>Level: {row.escalation_level || 1}</p>
                    <p className="capitalize">Priority: {row.priority || "medium"}</p>
                    <p>{new Date(row.created_at).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}</p>
                  </div>
                </div>
              ))}
            </div>
          )}
        </article>

        <article className="surface-card rounded-xl p-3.5">
          <h3 className="mb-2 text-[11px] font-semibold uppercase tracking-[0.12em] text-slate-500">Identity Ambiguity Queue</h3>
          {loading ? <SkeletonBlock rows={5} /> : ambiguityQueue.items.length === 0 ? (
            <p className="text-sm text-slate-500">No ambiguous identity matches pending verification.</p>
          ) : (
            <div className="max-h-72 space-y-2 overflow-auto pr-1">
              {ambiguityQueue.items.map((item) => (
                <div key={item.query_id} className="rounded-lg border border-slate-200 bg-slate-50 p-2.5 text-xs">
                  <p className="font-semibold text-slate-800">{item.customer_email || "unknown-user"}</p>
                  <p className="text-slate-500">Verification: {item.review_status}</p>
                  <p className="mt-1 text-slate-600">Confidence: {Math.round((Number(item.confidence || 0)) * 100)}% · Candidates: {item.candidate_count}</p>
                  <div className="mt-1.5 flex flex-wrap gap-1">
                    {(item.candidates || []).slice(0, 4).map((candidate) => (
                      <span key={`${item.query_id}-${candidate.id}`} className="rounded-full bg-white px-2 py-0.5 text-[11px] text-slate-700">
                        {candidate.name} ({Math.round((Number(candidate.confidence || 0)) * 100)}%)
                      </span>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          )}
        </article>
      </section>

      <section className="surface-card rounded-xl p-3.5">
        <h3 className="mb-2 text-[11px] font-semibold uppercase tracking-[0.12em] text-slate-500">Recent Queries</h3>
        {loading ? <SkeletonBlock rows={6} /> : recent.items.length === 0 ? (
          <p className="text-sm text-slate-500">No recent queries available yet.</p>
        ) : (
          <>
          <div className="space-y-2 md:hidden">
            {recent.items.slice(0, 12).map((q) => (
              <div key={`mobile-${q.id}`} className="rounded-lg border border-slate-200 bg-slate-50 p-2.5 text-xs">
                <div className="flex items-center justify-between">
                  <p className="font-semibold text-slate-800">{q.intent}</p>
                  <ConfidenceBadge value={q.confidence} />
                </div>
                <p className="mt-1 line-clamp-2 text-slate-600">{q.message}</p>
                <div className="mt-1.5 flex flex-wrap items-center gap-2 text-slate-500">
                  <span className="capitalize">{String(q.status || "unknown").replaceAll("_", " ")}</span>
                  <LatencyBadge ms={q.latency_ms || 0} />
                  <span>{new Date(q.created_at).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}</span>
                </div>
              </div>
            ))}
          </div>
          <div className="hidden max-h-72 overflow-auto md:block">
            <table className="w-full text-left text-xs">
              <thead className="sticky top-0 bg-white text-slate-500">
                <tr>
                  <th className="pb-2">Time</th>
                  <th>Intent</th>
                  <th>Status</th>
                  <th>Confidence</th>
                  <th>Latency</th>
                  <th>Language</th>
                  <th>Channel</th>
                </tr>
              </thead>
              <tbody>
                {recent.items.map((q) => (
                  <tr key={q.id} className="table-row-hover border-t border-slate-100 transition-colors">
                    <td className="py-2">{new Date(q.created_at).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}</td>
                    <td>{q.intent}</td>
                    <td className="capitalize">{String(q.status || "unknown").replaceAll("_", " ")}</td>
                    <td><ConfidenceBadge value={q.confidence} /></td>
                    <td><LatencyBadge ms={q.latency_ms || 0} /></td>
                    <td className="capitalize">{q.language || "english"}</td>
                    <td>{q.channel}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          </>
        )}
      </section>
    </div>
  );
}

export default DashboardPage;



