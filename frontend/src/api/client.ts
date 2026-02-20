/** API client for JackAI backend (configurable base URL). */

const BASE = import.meta.env.VITE_API_URL || "http://127.0.0.1:8000";

export type TargetConfig = {
  name: string;
  adapter_type: string;
  url?: string;
  selectors?: unknown;
  recommended_context_strategy?: string;
  widget_type?: string;
};

export type ChannelStatus = {
  id: string;
  status: "connected" | "disconnected";
  adapter_type: string;
  widget_type?: string;
  url?: string;
};

export type Reply = { content: string; channel_id?: string };

export async function getTargets(): Promise<TargetConfig[]> {
  const r = await fetch(`${BASE}/api/targets`);
  if (!r.ok) throw new Error(await r.text());
  return r.json();
}

export async function getChannels(): Promise<ChannelStatus[]> {
  const r = await fetch(`${BASE}/api/channels`);
  if (!r.ok) throw new Error(await r.text());
  return r.json();
}

export async function connectChannel(channelId: string): Promise<void> {
  const r = await fetch(`${BASE}/api/channels/${encodeURIComponent(channelId)}/connect`, {
    method: "POST",
  });
  if (!r.ok) throw new Error(await r.text());
}

export async function disconnectChannel(channelId: string): Promise<void> {
  const r = await fetch(`${BASE}/api/channels/${encodeURIComponent(channelId)}/disconnect`, {
    method: "POST",
  });
  if (!r.ok) throw new Error(await r.text());
}

export async function chat(channelIds: string[], message: string): Promise<{ replies: Reply[] }> {
  const r = await fetch(`${BASE}/api/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ channel_ids: channelIds, message }),
  });
  if (!r.ok) throw new Error(await r.text());
  return r.json();
}

export async function clearContext(
  channelId: string,
  strategy: string = "new_session",
  payload?: string
): Promise<void> {
  const r = await fetch(`${BASE}/api/channels/${encodeURIComponent(channelId)}/clear-context`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ strategy, payload }),
  });
  if (!r.ok) throw new Error(await r.text());
}

export async function setContext(channelId: string, payload: string): Promise<void> {
  const r = await fetch(`${BASE}/api/channels/${encodeURIComponent(channelId)}/set-context`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ payload }),
  });
  if (!r.ok) throw new Error(await r.text());
}
