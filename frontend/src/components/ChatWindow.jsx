import { Info, LoaderCircle, Mic, MicOff, Send } from "lucide-react";
import { useEffect, useRef } from "react";
import MessageBubble from "./MessageBubble";

function TypingIndicator() {
  return (
    <div className="flex justify-start">
      <div className="inline-flex items-center gap-2 rounded-2xl bg-slate-100 px-4 py-2 text-xs text-slate-600">
        <LoaderCircle className="animate-spin" size={14} /> AI is typing...
      </div>
    </div>
  );
}

function ChannelPill({ channel, activeChannel, setActiveChannel }) {
  const active = channel === activeChannel;
  return (
    <button
      type="button"
      onClick={() => setActiveChannel(channel)}
      className={`rounded-full px-3 py-1.5 text-xs font-semibold transition ${
        active ? "bg-leaf-700 text-white" : "bg-slate-100 text-slate-600 hover:bg-slate-200"
      }`}
    >
      {channel}
    </button>
  );
}

function ChatWindow({
  channels,
  activeChannel,
  setActiveChannel,
  messages,
  draft,
  setDraft,
  isLoading,
  onSend,
  onRetry,
  escalationNotice,
  suggestions,
  onUseSuggestion,
  voiceState,
  voiceError,
  voiceFeedback,
  onVoiceStart,
  onVoiceStop
}) {
  const feedRef = useRef(null);
  const isListening = voiceState === "listening";
  const isVoiceBusy = isListening || voiceState === "processing";

  useEffect(() => {
    if (!feedRef.current) return;
    const behavior = window.innerWidth >= 1024 ? "auto" : "smooth";
    feedRef.current.scrollTo({ top: feedRef.current.scrollHeight, behavior });
  }, [messages, isLoading]);

  return (
    <section className="surface-card rounded-2xl p-2.5 backdrop-blur-xl sm:p-3.5 md:p-4">
      <div className="mb-2.5 flex flex-wrap items-center justify-between gap-2">
        <div className="flex items-center gap-2">
          {channels.map((channel) => (
            <ChannelPill
              key={channel}
              channel={channel}
              activeChannel={activeChannel}
              setActiveChannel={setActiveChannel}
            />
          ))}
        </div>
        {isLoading && <span className="text-xs font-medium text-slate-500">Fetching response...</span>}
      </div>

      {escalationNotice && (
        <div className="mb-3 flex items-start gap-2 rounded-xl border border-amber-200 bg-amber-50 px-3 py-2 text-xs text-amber-800">
          <Info size={14} className="mt-0.5" />
          <p>{escalationNotice}</p>
        </div>
      )}
      {Boolean(suggestions?.length) && (
        <div className="mb-3 -mx-1 overflow-x-auto px-1">
          <div className="flex w-max gap-2">
          {suggestions.map((suggestion) => (
            <button
              key={suggestion}
              type="button"
              onClick={() => onUseSuggestion?.(suggestion)}
              disabled={isLoading}
              className="whitespace-nowrap rounded-full border border-slate-200 bg-white px-3 py-1 text-xs font-medium text-slate-700 hover:bg-slate-100 disabled:opacity-60"
            >
              {suggestion}
            </button>
          ))}
          </div>
        </div>
      )}

      <div className="mb-2 text-xs text-slate-500">
        {voiceState === "listening" && <p>Listening...</p>}
        {voiceState === "detected" && <p>Voice detected...</p>}
        {voiceState === "processing" && <p>Processing query...</p>}
        {voiceState === "unsupported" && <p>Voice input is unavailable in this browser.</p>}
        {voiceFeedback && <p>{voiceFeedback}</p>}
        {voiceError && <p className="text-rose-700">{voiceError}</p>}
      </div>

      <div ref={feedRef} className="mb-2.5 h-[54vh] min-h-[320px] space-y-2 overflow-y-auto rounded-xl bg-slate-50 p-2 md:h-[460px] md:p-3">
        {messages.map((message) => (
          <MessageBubble key={message.id} message={message} onRetry={onRetry} />
        ))}
        {isLoading && <TypingIndicator />}
      </div>

      <form onSubmit={onSend} autoComplete="off" className="sticky bottom-0 z-10 flex items-center gap-2 rounded-xl bg-white/95 p-1 backdrop-blur">
        <button
          type="button"
          onClick={isListening ? onVoiceStop : onVoiceStart}
          disabled={isLoading}
          className={`inline-flex h-10 w-10 items-center justify-center rounded-xl border transition ${
            isListening
              ? "border-rose-300 bg-rose-50 text-rose-700 shadow-[0_0_0_6px_rgba(244,63,94,0.15)] animate-pulse"
              : "border-slate-200 bg-white text-slate-700 hover:bg-slate-50"
          }`}
          title={isListening ? "Stop listening" : "Start voice input"}
        >
          {isListening ? <MicOff size={16} /> : <Mic size={16} />}
        </button>
        <input
          name="support-reply-input"
          value={draft}
          onChange={(e) => setDraft(e.target.value)}
          placeholder={`Reply as ${activeChannel} support...`}
          autoComplete="off"
          className="flex-1 rounded-xl border border-slate-200 px-3.5 py-2 text-sm outline-none transition-all ring-leaf-500 placeholder:text-slate-400 focus:ring"
          disabled={isLoading}
        />
        <button
          type="submit"
          disabled={isLoading || isVoiceBusy}
          className="inline-flex items-center gap-2 rounded-xl bg-leaf-700 px-4 py-2 text-sm font-semibold text-white hover:bg-leaf-900 disabled:cursor-not-allowed disabled:opacity-60"
        >
          <Send size={14} /> Send
        </button>
      </form>
      <button
        type="button"
        onClick={isListening ? onVoiceStop : onVoiceStart}
        disabled={isLoading}
        className={`fixed bottom-24 right-4 z-30 inline-flex h-12 w-12 items-center justify-center rounded-full border shadow-lg transition md:hidden ${
          isListening
            ? "border-rose-300 bg-rose-50 text-rose-700 shadow-[0_0_0_8px_rgba(244,63,94,0.12)] animate-pulse"
            : "border-slate-200 bg-white text-slate-700"
        }`}
        title={isListening ? "Stop listening" : "Start voice input"}
      >
        {isListening ? <MicOff size={18} /> : <Mic size={18} />}
      </button>
    </section>
  );
}

export default ChatWindow;
