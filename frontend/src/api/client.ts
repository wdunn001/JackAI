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

// --- Scan API ---

export type WebWidgetSelectors = {
  input_selector: string;
  message_list_selector: string;
  send_selector?: string;
  widget_container_selector?: string;
  iframe_selector?: string;
};

export type IdentifiedInteraction = {
  url: string;
  widget_type: string;
  selectors: WebWidgetSelectors;
  confidence: number;
  frame?: string | null;
};

export type ContextWipeTestResult = {
  identified: IdentifiedInteraction;
  success: boolean;
  strategy_used: string;
  target_config: TargetConfig;
};

export type ScrapeResult = { urls: string[] };

export async function scanScrape(seeds: string[], crawlDepth = 0, useSitemap = false): Promise<ScrapeResult> {
  const r = await fetch(`${BASE}/api/scan/scrape`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ seeds, crawl_depth: crawlDepth, use_sitemap: useSitemap }),
  });
  if (!r.ok) throw new Error(await r.text());
  return r.json();
}

export async function scanIdentify(url?: string, urls?: string[]): Promise<IdentifiedInteraction[]> {
  const r = await fetch(`${BASE}/api/scan/identify`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(url !== undefined ? { url } : { urls: urls ?? [] }),
  });
  if (!r.ok) throw new Error(await r.text());
  return r.json();
}

export async function scanTestWipe(identified: IdentifiedInteraction): Promise<ContextWipeTestResult> {
  const r = await fetch(`${BASE}/api/scan/test-wipe`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(identified),
  });
  if (!r.ok) throw new Error(await r.text());
  return r.json();
}

export async function scanFull(seeds: string[], scrapeOptions?: { crawl_depth?: number; use_sitemap?: boolean }): Promise<{
  results: ContextWipeTestResult[];
  target_configs: TargetConfig[];
}> {
  const r = await fetch(`${BASE}/api/scan/full`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ seeds, scrape_options: scrapeOptions ?? {} }),
  });
  if (!r.ok) throw new Error(await r.text());
  return r.json();
}

export async function saveTarget(config: TargetConfig): Promise<{ saved: string; targets: TargetConfig[] }> {
  const r = await fetch(`${BASE}/api/scan/save-target`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(config),
  });
  if (!r.ok) throw new Error(await r.text());
  return r.json();
}

// --- Preset security tests ---

export type PresetCategory = {
  id: string;
  name: string;
  description: string;
  payload_count: number;
};

export type PresetTestResult = {
  category_id: string;
  category_name: string;
  description: string;
  payload: string;
  reply: string;
  error: string | null;
};

export async function getPresetCategories(): Promise<PresetCategory[]> {
  const r = await fetch(`${BASE}/api/scan/preset-categories`);
  if (!r.ok) throw new Error(await r.text());
  return r.json();
}

export async function runPresetTests(
  identified: IdentifiedInteraction,
  categories?: string[]
): Promise<{ results: PresetTestResult[] }> {
  const r = await fetch(`${BASE}/api/scan/preset-tests`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ identified, categories: categories ?? null }),
  });
  if (!r.ok) throw new Error(await r.text());
  return r.json();
}
