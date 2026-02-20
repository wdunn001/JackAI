import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import type { ChannelStatus } from "../api/client";
import { getChannels, connectChannel, disconnectChannel } from "../api/client";

export function Dashboard() {
  const [channels, setChannels] = useState<ChannelStatus[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = async () => {
    try {
      setError(null);
      const data = await getChannels();
      setChannels(data);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load channels");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
  }, []);

  const handleConnect = async (id: string) => {
    try {
      await connectChannel(id);
      await load();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Connect failed");
    }
  };

  const handleDisconnect = async (id: string) => {
    try {
      await disconnectChannel(id);
      await load();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Disconnect failed");
    }
  };

  if (loading) return <p>Loading...</p>;
  if (error) return <p className="error">{error}</p>;

  return (
    <div className="dashboard">
      <h1>JackAI Dashboard</h1>
      <p className="subtitle">Channel overview — connect and manage targets.</p>
      <nav>
        <Link to="/chat">Open Chat</Link>
      </nav>
      <section className="channel-overview">
        <h2>Channels</h2>
        <ul>
          {channels.map((ch) => (
            <li key={ch.id} className={ch.status}>
              <span className="name">{ch.id}</span>
              <span className="adapter">{ch.adapter_type}</span>
              {ch.widget_type && <span className="widget">({ch.widget_type})</span>}
              <span className="status">{ch.status}</span>
              {ch.status === "connected" ? (
                <button type="button" onClick={() => handleDisconnect(ch.id)}>Disconnect</button>
              ) : (
                <button type="button" onClick={() => handleConnect(ch.id)}>Connect</button>
              )}
            </li>
          ))}
        </ul>
        {channels.length === 0 && (
          <p>No targets. Add YAML configs to <code>config/targets/</code> or run a scan.</p>
        )}
      </section>
    </div>
  );
}
