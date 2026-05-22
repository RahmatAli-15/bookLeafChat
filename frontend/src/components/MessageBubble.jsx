import { AlertTriangle, RotateCcw } from "lucide-react";

function ConfidencePill({ confidence }) {
  if (confidence === null || confidence === undefined) return null;

  const tone = confidence >= 80 ? "bg-emerald-100 text-emerald-700" : confidence >= 60 ? "bg-sky-100 text-sky-700" : "bg-rose-100 text-rose-700";

  return <span className={`rounded-full px-2 py-0.5 text-xs font-semibold ${tone}`}>Confidence {Math.round(confidence)}%</span>;
}

function MessageBubble({ message, onRetry }) {
  const mine = message.role === "user";
  const timestamp = message.createdAt ? new Date(message.createdAt).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }) : "";
  const resolutionStatus = message.workflow?.escalation || (message.escalated ? "Escalated" : "Resolved");
  const resolutionTone =
    resolutionStatus === "Escalated"
      ? "bg-rose-100 text-rose-700"
      : resolutionStatus === "Support Review Recommended"
        ? "bg-amber-100 text-amber-700"
        : resolutionStatus === "Conversational Response"
          ? "bg-sky-100 text-sky-700"
          : "bg-emerald-100 text-emerald-700";

  const formattedContent = (message.content || "").replace(/\b(\d{4})-(\d{2})-(\d{2})\b/g, (_, y, m, d) => {
    const dt = new Date(Number(y), Number(m) - 1, Number(d));
    return dt.toLocaleDateString([], { year: "numeric", month: "long", day: "numeric" });
  });

  return (
    <div className={`flex animate-in fade-in duration-300 ${mine ? "justify-end" : "justify-start"}`}>
      <div className={`max-w-[90%] rounded-2xl px-4 py-3 text-sm shadow-sm md:max-w-[80%] ${mine ? "bg-leaf-700 text-white" : "bg-slate-100 text-slate-800"}`}>
        <p className="whitespace-pre-wrap">{formattedContent}</p>

        {!mine && (
          <div className="mt-2 flex flex-wrap items-center gap-2 text-xs">
            <ConfidencePill confidence={message.confidence} />
            <span className={`inline-flex items-center gap-1 rounded-full px-2 py-0.5 font-semibold ${resolutionTone}`}>
              {resolutionStatus === "Escalated" ? <AlertTriangle size={12} /> : null}
              {resolutionStatus}
            </span>
            {timestamp && <span className="text-slate-500">{timestamp}</span>}
          </div>
        )}

        {message.error && (
          <div className="mt-2 rounded-lg border border-amber-200 bg-amber-50 px-3 py-2 text-xs text-amber-800">
            We are temporarily unable to reach support services. Please retry now or in a moment.
            {message.canRetry && (
              <button
                type="button"
                onClick={() => onRetry?.(message.retryPayload)}
                className="ml-2 inline-flex items-center gap-1 font-semibold underline decoration-1"
              >
                <RotateCcw size={12} /> Retry
              </button>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

export default MessageBubble;


