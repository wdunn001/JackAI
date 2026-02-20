type Message = { role: "user" | "assistant"; content: string; channelId?: string };

type Props = { messages: Message[] };

export function MessageList({ messages }: Props) {
  return (
    <div className="message-list">
      {messages.map((m, i) => (
        <div key={i} className={`message ${m.role}`}>
          <span className="role">{m.role}</span>
          {m.channelId && <span className="channel-badge">{m.channelId}</span>}
          <div className="content">{m.content}</div>
        </div>
      ))}
      {messages.length === 0 && (
        <p className="empty">No messages yet. Select channel(s) and send a message.</p>
      )}
    </div>
  );
}
