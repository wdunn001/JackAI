import { useEffect, useState, useCallback } from "react";
import { Link } from "react-router-dom";
import type { ChannelStatus, Reply } from "../api/client";
import {
  getChannels,
  connectChannel,
  disconnectChannel,
  chat,
  clearContext,
  setContext,
} from "../api/client";
import { ChannelSelector } from "../components/ChannelSelector";
import { MessageList } from "../components/MessageList";
import { InputArea } from "../components/InputArea";
import { ContextActions } from "../components/ContextActions";

type Message = { role: "user" | "assistant"; content: string; channelId?: string };

export function Chat() {
  const [channels, setChannels] = useState<ChannelStatus[]>([]);
  const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set());
  const [messages, setMessages] = useState<Message[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const loadChannels = useCallback(async () => {
    try {
      setError(null);
      const data = await getChannels();
      setChannels(data);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load channels");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadChannels();
  }, [loadChannels]);

  const onToggle = (id: string) => {
    setSelectedIds((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  };

  const onConnect = async (id: string) => {
    try {
      await connectChannel(id);
      await loadChannels();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Connect failed");
    }
  };

  const onDisconnect = async (id: string) => {
    try {
      await disconnectChannel(id);
      await loadChannels();
      setSelectedIds((prev) => {
        const next = new Set(prev);
        next.delete(id);
        return next;
      });
    } catch (e) {
      setError(e instanceof Error ? e.message : "Disconnect failed");
    }
  };

  const onSend = async (content: string) => {
    const connectedIds = channels.filter((c) => c.status === "connected").map((c) => c.id);
    const ids = selectedIds.size > 0
      ? Array.from(selectedIds).filter((id) => connectedIds.includes(id))
      : connectedIds;
    if (ids.length === 0) {
      setError("Select at least one connected channel.");
      return;
    }
    setMessages((prev) => [...prev, { role: "user", content }]);
    setError(null);
    try {
      const { replies } = await chat(ids, content);
      replies.forEach((r: Reply) => {
        setMessages((prev) => [...prev, { role: "assistant", content: r.content, channelId: r.channel_id }]);
      });
    } catch (e) {
      setError(e instanceof Error ? e.message : "Send failed");
    }
  };

  const onClearContext = async (channelId: string, strategy: string, payload?: string) => {
    try {
      await clearContext(channelId, strategy, payload);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Clear context failed");
    }
  };

  const onSetContext = async (channelId: string, payload: string) => {
    try {
      await setContext(channelId, payload);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Set context failed");
    }
  };

  const connectedSelected = Array.from(selectedIds).filter((id) =>
    channels.some((c) => c.id === id && c.status === "connected")
  );

  if (loading) return <p>Loading...</p>;

  return (
    <div className="chat-page">
      <header>
        <h1>Chat</h1>
        <Link to="/">Dashboard</Link>
      </header>
      {error && <p className="error">{error}</p>}
      <div className="chat-layout">
        <ChannelSelector
          channels={channels}
          selectedIds={selectedIds}
          onToggle={onToggle}
          onConnect={onConnect}
          onDisconnect={onDisconnect}
        />
        <main className="chat-main">
          <MessageList messages={messages} />
          <ContextActions
            channelIds={connectedSelected}
            onClearContext={onClearContext}
            onSetContext={onSetContext}
          />
          <InputArea
            onSend={onSend}
            disabled={channels.filter((c) => c.status === "connected").length === 0}
          />
        </main>
      </div>
    </div>
  );
}
