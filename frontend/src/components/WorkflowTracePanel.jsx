import { CheckCircle2, ChevronDown, ChevronUp, Clock3, Database, Dot, FileSearch, LoaderCircle, XCircle } from "lucide-react";

function SourceIcon({ source }) {
  if ((source || "").includes("Knowledge Base")) return <FileSearch size={13} />;
  return <Database size={13} />;
}

function TraceItem({ label, value }) {
  return (
    <div className="flex items-center justify-between rounded-md bg-slate-50 px-2.5 py-2 text-xs">
      <span className="text-slate-500">{label}</span>
      <span className="font-semibold text-slate-800">{value}</span>
    </div>
  );
}

function TimelineItem({ step, status }) {
  const tone =
    status === "completed"
      ? "text-emerald-700"
      : status === "active"
        ? "text-sky-700"
        : status === "failed"
          ? "text-rose-700"
          : "text-slate-400";

  return (
    <div className="flex items-center gap-1.5 text-[11px]">
      {status === "completed" ? <CheckCircle2 size={12} className="text-emerald-600" /> : null}
      {status === "active" ? <LoaderCircle size={12} className="animate-spin text-sky-600" /> : null}
      {status === "failed" ? <XCircle size={12} className="text-rose-600" /> : null}
      {status === "pending" ? <Dot size={14} className="text-slate-400" /> : null}
      <span className={`font-medium ${tone}`}>{step}</span>
    </div>
  );
}

function WorkflowTracePanel({ trace, expanded, onToggle }) {
  const ragTone =
    trace.ragStatus === "Support Guidance Retrieved"
      ? "text-slate-600 bg-slate-100"
      : trace.ragStatus === "Knowledge Base Matched"
        ? "text-emerald-700 bg-emerald-100"
        : "text-amber-700 bg-amber-100";
  const latencyMs = Number(String(trace.latency || "").replace("ms", ""));
  const latencyTone = !Number.isFinite(latencyMs)
    ? "text-slate-700 bg-slate-100"
    : latencyMs < 1500
      ? "text-emerald-700 bg-emerald-100"
      : latencyMs <= 3000
        ? "text-amber-700 bg-amber-100"
        : "text-rose-700 bg-rose-100";
  const severityTone =
    trace.severity === "Session Identity Response"
      ? "text-indigo-700 bg-indigo-100"
      : trace.severity === "Conversational Response"
      ? "text-sky-700 bg-sky-100"
      : trace.severity === "Auto Resolved"
      ? "text-emerald-700 bg-emerald-100"
      : trace.severity === "Support Review Recommended"
        ? "text-amber-700 bg-amber-100"
        : "text-rose-700 bg-rose-100";

  return (
    <aside className="surface-card rounded-2xl p-3">
      <button type="button" onClick={onToggle} className="flex w-full items-center justify-between">
        <div>
          <h3 className="text-xs font-semibold uppercase tracking-[0.12em] text-slate-500">AI Workflow Trace</h3>
          <p className="text-xs text-slate-500">Operational orchestration summary</p>
        </div>
        <span className="rounded-md bg-slate-100 p-1 text-slate-600">{expanded ? <ChevronUp size={16} /> : <ChevronDown size={16} />}</span>
      </button>

      {expanded && (
        <div className="mt-2.5 space-y-2 xl:max-h-none xl:overflow-visible">
          <div className="grid gap-1.5">
            <TraceItem label="Intent" value={trace.intent || "UNKNOWN"} />
            <div className="flex items-center justify-between rounded-md bg-slate-50 px-2.5 py-2 text-xs">
              <span className="text-slate-500">Resolution Status</span>
              <span className={`rounded-full px-2 py-0.5 font-semibold ${severityTone}`}>{trace.escalation || "Auto Resolved"}</span>
            </div>
            <TraceItem label="Confidence" value={trace.confidence || "N/A"} />
            <TraceItem label="Query Language" value={trace.queryLanguage || "English"} />
            <TraceItem label="Normalization" value={trace.workflowNormalization || "Not Required"} />
          </div>

          {Boolean(trace.timeline?.length) && (
            <div className="rounded-md border border-slate-200 bg-white px-2.5 py-2">
              <p className="mb-1.5 text-[11px] font-semibold uppercase tracking-[0.08em] text-slate-500">AI Reasoning Timeline</p>
              <div className="space-y-1">
                {trace.timeline.map((item) => (
                  <TimelineItem key={item.step} step={item.step} status={item.status} />
                ))}
              </div>
            </div>
          )}

          {trace.identity && (
            <div className="rounded-md border border-slate-200 bg-white p-2 text-xs">
              <p className="font-semibold text-slate-800">Identity Resolution</p>
              <p className="mt-1 text-slate-700">Matched Author: {trace.identity.authorName || "Unknown"}</p>
              <p className="text-slate-600">Confidence: {trace.identity.confidence || "N/A"}</p>
              <p className="text-slate-600">Verification: {trace.identity.verificationRequired ? "Required" : "Not Required"}</p>
              <div className="mt-1 flex flex-wrap gap-1">
                {(trace.identity.platforms || []).map((p) => (
                  <span key={p} className="rounded-full bg-slate-100 px-2 py-0.5 text-[11px] text-slate-700">{p}</span>
                ))}
              </div>
              <div className="mt-1">
                {(trace.identity.signals || []).slice(0, 3).map((s) => (
                  <p key={s} className="text-[11px] text-slate-500">• {s}</p>
                ))}
              </div>
            </div>
          )}
          <TraceItem label="Identity Match" value={trace.identityMatch || "N/A"} />
          <div className="flex items-center justify-between rounded-md bg-slate-50 px-2.5 py-2 text-xs">
            <span className="text-slate-500">Data Source</span>
            <span className="inline-flex items-center gap-1 font-semibold text-slate-800"><SourceIcon source={trace.dataSource} /> {trace.dataSource || "PostgreSQL"}</span>
          </div>
          <div className="flex items-center justify-between rounded-md bg-slate-50 px-2.5 py-2 text-xs">
            <span className="text-slate-500">RAG Status</span>
            <span className={`rounded-full px-2 py-0.5 font-semibold ${ragTone}`}>{trace.ragStatus || "Not Required"}</span>
          </div>
          <div className="flex items-center justify-between rounded-md bg-slate-50 px-2.5 py-2 text-xs">
            <span className="inline-flex items-center gap-1 text-slate-500"><Clock3 size={12} /> Latency</span>
            <span className={`rounded-full px-2 py-0.5 font-semibold ${latencyTone}`}>{trace.latency || "0ms"}</span>
          </div>
        </div>
      )}
    </aside>
  );
}

export default WorkflowTracePanel;



