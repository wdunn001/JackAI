import { useState } from "react";

type Props = {
  channelIds: string[];
  onClearContext: (channelId: string, strategy: string, payload?: string) => void;
  onSetContext: (channelId: string, payload: string) => void;
};

export function ContextActions({ channelIds, onClearContext, onSetContext }: Props) {
  const [strategy, setStrategy] = useState("new_session");
  const [injectPayload, setInjectPayload] = useState("");
  const [setPayload, setSetPayload] = useState("");

  if (channelIds.length === 0) return null;

  return (
    <div className="context-actions">
      <h4>Context</h4>
      <div className="clear-context">
        <select value={strategy} onChange={(e) => setStrategy(e.target.value)}>
          <option value="new_session">New session</option>
          <option value="inject">Inject</option>
          <option value="api">API</option>
        </select>
        {strategy === "inject" && (
          <input
            type="text"
            placeholder="Forget payload..."
            value={injectPayload}
            onChange={(e) => setInjectPayload(e.target.value)}
          />
        )}
        <button
          type="button"
          onClick={() => channelIds.forEach((id) => onClearContext(id, strategy, injectPayload || undefined))}
        >
          Clear context
        </button>
      </div>
      <div className="set-context">
        <input
          type="text"
          placeholder="Set context payload..."
          value={setPayload}
          onChange={(e) => setSetPayload(e.target.value)}
        />
        <button
          type="button"
          onClick={() => { setPayload && channelIds.forEach((id) => onSetContext(id, setPayload)); }}
          disabled={!setPayload.trim()}
        >
          Set context
        </button>
      </div>
    </div>
  );
}
