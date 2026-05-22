import { useEffect, useMemo, useRef, useState } from "react";
import { Activity, Database, ShieldAlert, Sparkles } from "lucide-react";
import ChatWindow from "../components/ChatWindow";
import WorkflowTracePanel from "../components/WorkflowTracePanel";
import { sendChatQuery } from "../services/api";

const CHANNELS = ["Email", "WhatsApp", "Instagram"];
const SUGGESTED = [
  "Check my royalty status",
  "Is my book live yet?",
  "Track my author copy",
  "Dashboard login help"
];
const STORAGE_KEY = "bookleaf_chat_histories_v2";

const channelIdentity = {
  // Use a seeded author identity so operational queries resolve against live DB records.
  Email: { email: "sara.johnson.0@bookleafauthors.com" },
  WhatsApp: { email: "sara.johnson.0@bookleafauthors.com", channel: "whatsapp" },
  Instagram: { email: "sara.johnson.0@bookleafauthors.com", channel: "instagram" }
};

function withId(message) {
  return { id: `${Date.now()}-${Math.random().toString(36).slice(2, 8)}`, ...message };
}

function normalizeRagStatus(rawStatus, retrievalSource) {
  const status = (rawStatus || "").toLowerCase();
  const source = (retrievalSource || "").toLowerCase();
  if (!rawStatus && !source.includes("knowledge")) return "Not Required";
  if (status.includes("matched")) return "Knowledge Base Matched";
  if (status.includes("guidance")) return "Support Guidance Retrieved";
  if (status.includes("not required")) return "Not Required";
  if (status.includes("no match") || status.includes("no relevant")) return "No Relevant Guidance Found";
  if (source.includes("knowledge")) return "Knowledge Base Matched";
  return rawStatus || "Not Required";
}

function initialHistories() {
  return Object.fromEntries(
    CHANNELS.map((channel) => [
      channel,
      [
        withId({
          role: "assistant",
          content: "BookLeaf support AI is active. I can help with royalties, publishing status, add-ons, and dashboard issues.",
          confidence: 99,
          intent: "SYSTEM",
          createdAt: new Date().toISOString()
        })
      ]
    ])
  );
}

async function streamText(fullText, onTick) {
  const text = (fullText || "").trim();
  if (!text) {
    onTick("");
    return;
  }

  // Keep streaming effect, but cap total animation time to feel snappy.
  const maxDurationMs = 800;
  const steps = Math.min(16, Math.max(5, Math.ceil(text.length / 40)));
  const intervalMs = Math.max(6, Math.floor(maxDurationMs / steps));
  const chunkSize = Math.max(8, Math.ceil(text.length / steps));

  let cursor = 0;
  while (cursor < text.length) {
    cursor += chunkSize;
    onTick(text.slice(0, cursor));
    await new Promise((resolve) => setTimeout(resolve, intervalMs));
  }
}

function StatusPill({ icon: Icon, label, active }) {
  return (
    <span className={`inline-flex items-center gap-1 rounded-lg px-2 py-1 text-xs font-semibold ${active ? "bg-emerald-100 text-emerald-700" : "bg-slate-200 text-slate-600"}`}>
      <Icon size={12} />
      {label}
    </span>
  );
}

function ChatPage({ onResolved, pushToast, health }) {
  const [activeChannel, setActiveChannel] = useState(CHANNELS[0]);
  const [draft, setDraft] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [escalationNotice, setEscalationNotice] = useState("");
  const [voiceState, setVoiceState] = useState("idle"); // idle | listening | processing | detected | unsupported | error
  const [voiceError, setVoiceError] = useState("");
  const [voiceFeedback, setVoiceFeedback] = useState("");
  const recognitionRef = useRef(null);
  const voiceDraftRef = useRef("");
  const [traceExpanded, setTraceExpanded] = useState(() => {
    if (typeof window === "undefined") return false;
    return window.innerWidth >= 1280;
  });
  const [trace, setTrace] = useState({
    intent: "SYSTEM",
    identityMatch: "N/A",
    dataSource: "PostgreSQL",
    confidence: "99%",
    severity: "Auto Resolved",
    escalation: "No",
    latency: "0ms",
    ragStatus: "Not Required",
    identity: null,
    queryLanguage: "English",
    workflowNormalization: "Not Required",
    timeline: [],
  });
  const [normalizationNotice, setNormalizationNotice] = useState("");
  const [histories, setHistories] = useState(() => {
    try {
      const raw = localStorage.getItem(STORAGE_KEY);
      if (raw) {
        const parsed = JSON.parse(raw);
        if (parsed && typeof parsed === "object") return parsed;
      }
      // Backward compatibility migration from old session storage key.
      const legacy = sessionStorage.getItem("bookleaf_chat_histories_v1");
      if (legacy) {
        const parsedLegacy = JSON.parse(legacy);
        if (parsedLegacy && typeof parsedLegacy === "object") return parsedLegacy;
      }
    } catch (_) {
      // Ignore invalid session cache.
    }
    return initialHistories();
  });

  useEffect(() => {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(histories));
  }, [histories]);

  useEffect(() => {
    const onResize = () => {
      if (window.innerWidth >= 1280) setTraceExpanded(true);
    };
    window.addEventListener("resize", onResize);
    return () => window.removeEventListener("resize", onResize);
  }, []);

  const messages = histories[activeChannel] || [];

  const replaceMessage = (channel, messageId, patch) => {
    setHistories((prev) => ({
      ...prev,
      [channel]: (prev[channel] || []).map((m) => (m.id === messageId ? { ...m, ...patch } : m))
    }));
  };

  const runQuery = async (text) => {
    const payload = { query: text, channel: activeChannel.toLowerCase(), ...channelIdentity[activeChannel] };
    const userMessage = withId({ role: "user", content: text, createdAt: new Date().toISOString() });
    const placeholder = withId({ role: "assistant", content: "", createdAt: new Date().toISOString() });

    setHistories((prev) => ({ ...prev, [activeChannel]: [...(prev[activeChannel] || []), userMessage, placeholder] }));
    setIsLoading(true);
    setEscalationNotice("");
    setNormalizationNotice("");
    setTrace((prev) => ({
      ...prev,
      intent: "PROCESSING",
      latency: "...",
      timeline: [
        { step: "Identity matched", status: "active" },
        { step: "Intent classified", status: "pending" },
        { step: "Database queried", status: "pending" },
        { step: "Response generated", status: "pending" },
        { step: "Confidence evaluated", status: "pending" },
      ],
    }));

    const timelineTimers = [
      setTimeout(() => setTrace((prev) => ({ ...prev, timeline: prev.timeline.map((t, i) => i === 0 ? { ...t, status: "completed" } : i === 1 ? { ...t, status: "active" } : t) })), 160),
      setTimeout(() => setTrace((prev) => ({ ...prev, timeline: prev.timeline.map((t, i) => i === 1 ? { ...t, status: "completed" } : i === 2 ? { ...t, status: "active" } : t) })), 320),
      setTimeout(() => setTrace((prev) => ({ ...prev, timeline: prev.timeline.map((t, i) => i === 2 ? { ...t, status: "completed" } : i === 3 ? { ...t, status: "active" } : t) })), 500),
    ];

    try {
      const res = await sendChatQuery(payload);
      await streamText(res.response || "", (partial) => replaceMessage(activeChannel, placeholder.id, { content: partial }));

      const signals = (res.confidence_breakdown || {}).signals || {};
      const identityPct = Math.round((signals.identity ?? (payload.email ? 1 : 0.3)) * 100);
      const confidencePct = Math.round((res.confidence || 0) * 100);
      const identity = res.identity_resolution || {};
      const identityConfidencePct = Math.round((identity.confidence || 0) * 100);
      const identityLabel = identityConfidencePct >= 90 ? "High confidence (Auto Resolved)" : identityConfidencePct >= 70 ? "Medium confidence (Support Review Recommended)" : "Low confidence (Manual Verification Required)";

      const workflow = {
        intent: res.intent,
        identityMatch: `${identityPct}%`,
        retrieval: res.retrieval_source || "PostgreSQL",
        escalation: res.escalation_severity || "Auto Resolved"
      };

      const languageLabel = (res.language_detected || "english").replace(/^\w/, (m) => m.toUpperCase());
      const normalizedFlag = Boolean(res.multilingual_detected || res.normalized_for_workflow);
      if (normalizedFlag) {
        setNormalizationNotice(
          res.normalized_for_workflow
            ? "Hindi/Hinglish query detected. Normalized for workflow processing."
            : "Hindi/Hinglish query detected. Processed with multilingual understanding."
        );
        setVoiceFeedback("Multilingual query normalized");
      }

      replaceMessage(activeChannel, placeholder.id, {
        confidence: confidencePct,
        escalated: res.escalated,
        intent: res.intent,
        content: res.response,
        authorName: payload.email || "Unknown author",
        workflow,
        createdAt: res.created_at
      });

      const isSmalltalk = res.intent === "SMALLTALK";
      const isConversationalIdentity = res.intent === "CONVERSATIONAL_IDENTITY";
      setTrace({
        intent: res.intent,
        identityMatch: (isSmalltalk || isConversationalIdentity) ? "Session Context" : `${identityPct}%`,
        dataSource: (isSmalltalk || isConversationalIdentity) ? (res.retrieval_source || "Session Context") : (res.retrieval_source || "PostgreSQL"),
        confidence: `${confidencePct}%`,
        severity: isConversationalIdentity ? "Session Identity Response" : (isSmalltalk ? "Conversational Response" : (res.escalation_severity || "Auto Resolved")),
        escalation: isConversationalIdentity ? "Session Identity Response" : (isSmalltalk ? "Conversational Response" : (res.escalation_severity || "Auto Resolved")),
        latency: `${res.latency_ms || 0}ms`,
        ragStatus: (isSmalltalk || isConversationalIdentity) ? "Not Required" : normalizeRagStatus(res.rag_status, res.retrieval_source),
        queryLanguage: languageLabel,
        workflowNormalization: res.normalized_for_workflow ? "Applied" : "Not Required",
        identity: (isSmalltalk || isConversationalIdentity) ? null : {
          authorName: identity.author?.name || payload.email || "Unknown",
          confidence: `${identityConfidencePct}% - ${identityLabel}`,
          verificationRequired: Boolean(identity.verification_required),
          platforms: identity.linked_platforms || ["Email", "WhatsApp", "Instagram", "Dashboard Profile"],
          signals: identity.matching_signals || identity.reasons || [],
        },
        timeline: isConversationalIdentity
          ? [
              { step: "Session identity detected", status: "completed" },
              { step: "Intent classified", status: "completed" },
              { step: "Identity response generated", status: "completed" },
            ]
          : isSmalltalk
          ? [
              { step: "Conversation detected", status: "completed" },
              { step: "Intent classified", status: "completed" },
              { step: "Response generated", status: "completed" },
            ]
          : [
              { step: "Identity matched", status: "completed" },
              { step: "Intent classified", status: "completed" },
              { step: "Database queried", status: "completed" },
              { step: "Response generated", status: "completed" },
              { step: "Confidence evaluated", status: "completed" },
            ],
      });

      if ((res.escalation_severity || "") === "Support Review Recommended") {
        const reason = res.escalation_reason || "Support review is recommended for this request.";
        setEscalationNotice(reason);
        pushToast?.({ type: "warning", title: "Support Review Recommended", message: reason });
      } else if ((res.escalation_severity || "") === "Escalated") {
        const reason = res.escalation_reason || "Your request has been routed to a specialist.";
        setEscalationNotice(reason);
        pushToast?.({ type: "warning", title: "Escalation triggered", message: reason });
      } else {
        pushToast?.({ type: "success", title: "Resolution successful", message: `Intent ${res.intent} resolved.` });
      }
      onResolved?.();
    } catch (error) {
      const raw = (error.message || "").toLowerCase();
      const friendly =
        raw.includes("failed to fetch") || raw.includes("network")
          ? "We are experiencing a temporary connection issue while contacting support services."
          : "We could not complete this request right now. Please retry, and our team will continue assisting you.";
      replaceMessage(activeChannel, placeholder.id, {
        content: "I am unable to complete this request right now.",
        error: friendly,
        canRetry: true,
        retryPayload: text,
        confidence: 0,
        escalated: true,
        intent: "FAILED"
      });
      setTrace((prev) => ({
        ...prev,
        intent: "FAILED",
        escalation: "Support Review Recommended",
        confidence: "0%",
        queryLanguage: "Unknown",
        workflowNormalization: "Unknown",
        timeline: prev.timeline.map((t, idx) => (idx < 2 ? { ...t, status: "completed" } : { ...t, status: "failed" })),
      }));
      setEscalationNotice("Support review is recommended while service connectivity stabilizes.");
      pushToast?.({ type: "warning", title: "Support Review Recommended", message: friendly });
    } finally {
      timelineTimers.forEach((t) => clearTimeout(t));
      setIsLoading(false);
    }
  };

  const handleSend = async (e) => {
    e.preventDefault();
    const text = draft.trim();
    if (!text || isLoading) return;
    setDraft("");
    await runQuery(text);
  };

  const handleRetry = async (text) => {
    if (!text || isLoading) return;
    await runQuery(text);
  };

  const startVoiceRecognition = () => {
    if (isLoading || voiceState === "listening") return;
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRecognition) {
      setVoiceState("unsupported");
      setVoiceError("Voice input is not supported in this browser. Please use Chrome or Edge.");
      pushToast?.({ type: "warning", title: "Voice not supported", message: "This browser does not support speech recognition." });
      return;
    }

    setVoiceError("");
    setVoiceState("listening");
    const recognition = new SpeechRecognition();
    recognitionRef.current = recognition;
    recognition.continuous = false;
    recognition.interimResults = true;
    recognition.maxAlternatives = 1;
    recognition.lang = "en-IN";

    recognition.onstart = () => {
      setVoiceState("listening");
    };

    recognition.onresult = (event) => {
      let finalText = "";
      let interimText = "";
      for (let i = event.resultIndex; i < event.results.length; i += 1) {
        const t = event.results[i]?.[0]?.transcript || "";
        if (event.results[i].isFinal) finalText += `${t} `;
        else interimText += `${t} `;
      }
      if (finalText.trim()) {
        voiceDraftRef.current = `${voiceDraftRef.current} ${finalText}`.trim();
      }
      const combined = `${voiceDraftRef.current} ${interimText}`.trim();
      voiceDraftRef.current = combined;
      if (!combined) {
        setVoiceState("error");
        setVoiceError("No speech was detected. Please try again.");
        return;
      }
      setDraft(combined);
      setVoiceState("detected");
      const lowered = combined.toLowerCase();
      const isHindiScript = /[\u0900-\u097F]/.test(combined);
      const isHinglish = ["meri", "mujhe", "kab", "kaise", "nahi", "milegi", "batao", "kar raha"].some((h) => lowered.includes(h));
      setVoiceFeedback(isHindiScript || isHinglish ? "Hindi/Hinglish voice detected" : "Voice detected...");
    };

    recognition.onerror = (event) => {
      const code = event?.error || "unknown";
      let message = "Voice recognition failed. Please try again.";
      if (code === "not-allowed" || code === "service-not-allowed") {
        message = "Microphone access was denied. Please allow microphone permission and retry.";
      } else if (code === "no-speech" || code === "audio-capture") {
        message = "No speech input detected. Please speak clearly and retry.";
      } else if (code === "network") {
        message = "Speech service is temporarily unavailable. Please retry in a moment.";
      } else if (code === "aborted") {
        message = "Voice capture was stopped.";
      }
      setVoiceState("error");
      setVoiceError(message);
      pushToast?.({ type: "warning", title: "Voice input issue", message });
    };

    recognition.onend = async () => {
      const captured = voiceDraftRef.current.trim();
      if (captured) {
        setVoiceState("processing");
        setVoiceFeedback("Processing query...");
        if (!isLoading) {
          setDraft("");
          await runQuery(captured);
        }
      } else if (voiceState !== "error") {
        setVoiceState("idle");
        setVoiceFeedback("");
      }
      voiceDraftRef.current = "";
      setTimeout(() => {
        setVoiceState((prev) => (prev === "processing" || prev === "detected" ? "idle" : prev));
        setVoiceFeedback((prev) => (prev === "Processing query..." ? "" : prev));
      }, 500);
    };

    try {
      recognition.start();
    } catch (_) {
      setVoiceState("error");
      setVoiceError("Could not start voice capture. Please retry.");
    }
  };

  const stopVoiceRecognition = () => {
    try {
      recognitionRef.current?.stop();
    } catch (_) {
      // ignore stop errors
    }
  };

  const multiTurnHint = useMemo(() => `Channel mode: ${activeChannel} | session history persisted`, [activeChannel]);

  return (
    <div className="space-y-3">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <div>
          <h2 className="text-2xl font-semibold">AI Support Command Center</h2>
          <p className="text-sm text-slate-500">{multiTurnHint}</p>
        </div>
        <div className="flex flex-wrap gap-1.5">
          <StatusPill icon={Sparkles} label="AI Active" active={health?.ai_active ?? true} />
          <StatusPill icon={Database} label="DB Connected" active={health?.db_connected ?? false} />
          <StatusPill icon={Activity} label="RAG Enabled" active={health?.rag_enabled ?? true} />
          <StatusPill icon={ShieldAlert} label="Escalation Monitoring" active={health?.escalation_monitoring_enabled ?? true} />
        </div>
      </div>

      {escalationNotice && (
        <div className="rounded-lg border border-amber-200 bg-amber-50 px-3 py-2 text-sm text-amber-800">
          <p className="font-semibold">{trace.severity === "Escalated" ? "Escalated Case" : "Support Review Note"}</p>
          <p>{escalationNotice}</p>
        </div>
      )}
      {normalizationNotice && (
        <div className="rounded-lg border border-sky-200 bg-sky-50 px-3 py-2 text-sm text-sky-800">
          <p className="font-semibold">Multilingual Processing</p>
          <p>{normalizationNotice}</p>
        </div>
      )}

      <div className="grid gap-3 xl:grid-cols-[minmax(0,1fr)_320px]">
        <ChatWindow
          channels={CHANNELS}
          activeChannel={activeChannel}
          setActiveChannel={setActiveChannel}
          messages={messages}
          draft={draft}
          setDraft={setDraft}
          isLoading={isLoading}
          onSend={handleSend}
          onRetry={handleRetry}
          escalationNotice=""
          suggestions={SUGGESTED}
          onUseSuggestion={(text) => {
            if (isLoading) return;
            setDraft(text);
            runQuery(text);
          }}
          voiceState={voiceState}
          voiceError={voiceError}
          voiceFeedback={voiceFeedback}
          onVoiceStart={startVoiceRecognition}
          onVoiceStop={stopVoiceRecognition}
        />
        <div className="xl:block">
          <WorkflowTracePanel trace={trace} expanded={traceExpanded} onToggle={() => setTraceExpanded((v) => !v)} />
        </div>
      </div>
    </div>
  );
}

export default ChatPage;




