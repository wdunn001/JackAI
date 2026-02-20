import { useState, FormEvent } from "react";

type Props = {
  onSend: (message: string) => void;
  disabled?: boolean;
  placeholder?: string;
};

export function InputArea({ onSend, disabled, placeholder = "Type a message..." }: Props) {
  const [value, setValue] = useState("");

  const handleSubmit = (e: FormEvent) => {
    e.preventDefault();
    const text = value.trim();
    if (text && !disabled) {
      onSend(text);
      setValue("");
    }
  };

  return (
    <form className="input-area" onSubmit={handleSubmit}>
      <input
        type="text"
        value={value}
        onChange={(e) => setValue(e.target.value)}
        placeholder={placeholder}
        disabled={disabled}
      />
      <button type="submit" disabled={disabled || !value.trim()}>Send</button>
    </form>
  );
}
