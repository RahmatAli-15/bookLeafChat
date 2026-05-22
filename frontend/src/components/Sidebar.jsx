import { ExternalLink, LayoutDashboard, MessageSquare } from "lucide-react";

const navItems = [
  { id: "chat", label: "AI Support Chat", icon: MessageSquare },
  { id: "dashboard", label: "Admin Dashboard", icon: LayoutDashboard }
];

const PUBLISHING_WORKSPACE_URL = "https://bookai-frontend-x1ty.onrender.com/";

function Sidebar({ activePage, onNavigate }) {
  return (
    <aside className="hidden w-64 shrink-0 xl:block">
      <div className="surface-card sticky top-4 rounded-2xl p-4 backdrop-blur-xl">
        <p className="mb-3 text-xs font-semibold uppercase tracking-[0.14em] text-slate-500">Workspace</p>
        <nav className="space-y-2">
          {navItems.map((item) => (
            <button
              key={item.id}
              type="button"
              onClick={() => onNavigate(item.id)}
              className={`w-full rounded-xl px-3 py-2.5 text-left text-sm font-medium transition-all duration-200 ${
                activePage === item.id
                  ? "bg-leaf-700 text-white shadow-md shadow-leaf-700/25"
                  : "bg-slate-100 text-slate-700 hover:bg-slate-200 hover:text-slate-900"
              }`}
            >
              <span className="inline-flex items-center gap-2">
                <item.icon size={15} />
                {item.label}
              </span>
            </button>
          ))}
          <a
            href={PUBLISHING_WORKSPACE_URL}
            target="_blank"
            rel="noopener noreferrer"
            title="Advanced AI publishing workflow system"
            className="group block w-full rounded-xl bg-slate-100 px-3 py-2.5 text-left text-sm font-medium text-slate-700 transition-all duration-200 hover:bg-slate-200 hover:text-slate-900"
          >
            <span className="inline-flex items-center gap-2">
              <ExternalLink size={15} />
              Publishing Workspace
              <ExternalLink size={12} className="opacity-55 transition group-hover:opacity-90" />
            </span>
            <span className="mt-1 block text-[11px] text-slate-500">Advanced AI publishing workflow system</span>
          </a>
        </nav>
      </div>
    </aside>
  );
}

export default Sidebar;

