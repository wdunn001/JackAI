import type { ChannelStatus } from "../api/client";

type Props = {
  channels: ChannelStatus[];
  selectedIds: Set<string>;
  onToggle: (id: string) => void;
  onConnect: (id: string) => void;
  onDisconnect: (id: string) => void;
};

export function ChannelSelector({ channels, selectedIds, onToggle, onConnect, onDisconnect }: Props) {
  return (
    <aside className="channel-selector">
      <h3>Channels</h3>
      <ul>
        {channels.map((ch) => (
          <li key={ch.id} className={ch.status}>
            <label>
              <input
                type="checkbox"
                checked={selectedIds.has(ch.id)}
                onChange={() => onToggle(ch.id)}
                disabled={ch.status !== "connected"}
              />
              <span className="name">{ch.id}</span>
              {ch.widget_type && <span className="widget-type">({ch.widget_type})</span>}
            </label>
            {ch.status === "connected" ? (
              <button type="button" onClick={() => onDisconnect(ch.id)}>Disconnect</button>
            ) : (
              <button type="button" onClick={() => onConnect(ch.id)}>Connect</button>
            )}
          </li>
        ))}
      </ul>
      {channels.length === 0 && <p>No targets. Add configs to config/targets/ or run a scan.</p>}
    </aside>
  );
}
