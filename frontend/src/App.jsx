import { useState } from "react";
import Topbar from "./components/Topbar";
import Sidebar from "./components/Sidebar";
import ChatPage from "./pages/ChatPage";
import DashboardPage from "./pages/DashboardPage";
import { getAnalyticsOverview } from "./services/api";
import { useEffect } from "react";
import { ExternalLink, LayoutDashboard, MessageSquare } from "lucide-react";

const PUBLISHING_WORKSPACE_URL = "https://bookai-frontend-x1ty.onrender.com/";

function App() {
  const [activePage, setActivePage] = useState("chat");
  const [refreshKey, setRefreshKey] = useState(0);
  const [health, setHealth] = useState({ ai_active: true, db_connected: false, rag_enabled: true, escalation_monitoring_enabled: true });
  const [toasts, setToasts] = useState([]);

  const pushToast = (toast) => {
    const id = `${Date.now()}-${Math.random().toString(36).slice(2, 8)}`;
    setToasts((prev) => [...prev, { id, ...toast }]);
    setTimeout(() => {
      setToasts((prev) => prev.filter((t) => t.id !== id));
    }, 2800);
  };

  useEffect(() => {
    let mounted = true;
    getAnalyticsOverview()
      .then((res) => mounted && setHealth(res.health || health))
      .catch(() => mounted && setHealth((prev) => ({ ...prev, db_connected: false })));
    return () => {
      mounted = false;
    };
  }, [refreshKey]);

  return (
    <div className="min-h-screen text-slate-800">
      <Topbar health={health} />
      <div className="mx-auto flex w-full max-w-7xl gap-3 p-2.5 pb-20 md:gap-4 md:p-4 md:pb-4">
        <Sidebar activePage={activePage} onNavigate={setActivePage} />
        <main className="flex-1 min-w-0">
          {activePage === "chat" ? (
            <ChatPage onResolved={() => setRefreshKey((k) => k + 1)} pushToast={pushToast} health={health} />
          ) : (
            <DashboardPage refreshKey={refreshKey} onRefresh={() => setRefreshKey((k) => k + 1)} health={health} />
          )}
        </main>
      </div>
      <nav className="fixed inset-x-0 bottom-0 z-40 border-t border-slate-200 bg-white/95 px-3 py-2 backdrop-blur md:hidden">
        <div className="mx-auto grid max-w-md grid-cols-3 gap-2">
          <button
            type="button"
            onClick={() => setActivePage("chat")}
            className={`inline-flex items-center justify-center gap-2 rounded-xl px-3 py-2 text-sm font-semibold transition ${
              activePage === "chat" ? "bg-leaf-700 text-white" : "bg-slate-100 text-slate-700"
            }`}
          >
            <MessageSquare size={16} />
            Chat
          </button>
          <button
            type="button"
            onClick={() => setActivePage("dashboard")}
            className={`inline-flex items-center justify-center gap-2 rounded-xl px-3 py-2 text-sm font-semibold transition ${
              activePage === "dashboard" ? "bg-leaf-700 text-white" : "bg-slate-100 text-slate-700"
            }`}
          >
            <LayoutDashboard size={16} />
            Dashboard
          </button>
          <a
            href={PUBLISHING_WORKSPACE_URL}
            target="_blank"
            rel="noopener noreferrer"
            title="Advanced AI publishing workflow system"
            className="inline-flex items-center justify-center gap-1 rounded-xl bg-slate-100 px-2 py-2 text-xs font-semibold text-slate-700 transition hover:bg-slate-200"
          >
            <ExternalLink size={14} />
            Workspace
          </a>
        </div>
      </nav>
      <div className="fixed bottom-4 right-4 z-50 space-y-2">
        {toasts.map((toast) => (
          <div key={toast.id} className={`animate-in fade-in slide-in-from-bottom-2 rounded-lg px-3 py-2 text-sm shadow-lg ${toast.type === "error" ? "bg-rose-600 text-white" : toast.type === "warning" ? "bg-amber-500 text-white" : "bg-emerald-600 text-white"}`}>
            <p className="font-semibold">{toast.title}</p>
            <p>{toast.message}</p>
          </div>
        ))}
      </div>
    </div>
  );
}

export default App;



