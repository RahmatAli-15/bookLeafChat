import { Activity, DatabaseZap, ShieldCheck, Sparkles } from "lucide-react";

function StatusPill({ icon: Icon, label, active }) {
  return (
    <span className={`inline-flex items-center gap-1.5 rounded-lg px-2.5 py-1 text-xs font-semibold ${active ? "bg-emerald-100 text-emerald-700" : "bg-slate-200 text-slate-600"}`}>
      <Icon size={12} />
      {label}
    </span>
  );
}

function Topbar({ health }) {
  return (
    <header className="border-b border-white/60 bg-white/75 backdrop-blur-xl">
      <div className="mx-auto flex w-full max-w-7xl items-center justify-between px-3 py-2.5 md:px-5 md:py-3">
        <div className="flex items-center gap-3">
          <div className="rounded-xl bg-leaf-700 p-2 shadow-md shadow-leaf-700/30">
            <img src="/favicon.svg" alt="BookLeaf" className="h-5 w-5" />
          </div>
          <div>
            <p className="text-xs uppercase tracking-[0.12em] text-slate-500">BookLeaf AI Support Automation Platform</p>
            <h1 className="text-base font-semibold leading-tight text-slate-900 md:text-lg">Support Command Center</h1>
          </div>
        </div>
        <div className="hidden items-center gap-2 rounded-xl bg-emerald-50 px-3 py-2 text-xs font-medium text-emerald-700 xl:flex">
          <ShieldCheck size={14} />
          AI + Human Escalation Ready
        </div>
        <div className="hidden items-center gap-2 2xl:flex">
          <StatusPill icon={Sparkles} label="AI Active" active={health?.ai_active} />
          <StatusPill icon={DatabaseZap} label="DB Connected" active={health?.db_connected} />
          <StatusPill icon={Activity} label="RAG Enabled" active={health?.rag_enabled} />
          <StatusPill icon={ShieldCheck} label="Escalation Monitoring Enabled" active={health?.escalation_monitoring_enabled} />
        </div>
      </div>
    </header>
  );
}

export default Topbar;



