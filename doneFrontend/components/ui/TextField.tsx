"use client";
import clsx from "clsx";

type Props = {
  id: string;
  label: string;
  type?: string;
  value: string;
  onChange: (e: React.ChangeEvent<HTMLInputElement>) => void;
  placeholder?: string;
  required?: boolean;
  error?: string | null;
  helperText?: string;
  autoComplete?: string;
};

export default function TextField({
  id, label, type = "text", value, onChange, placeholder, required,
  error, helperText, autoComplete
}: Props) {
  return (
    <div>
      <label htmlFor={id} className="label">{label}</label>
      <input
        id={id}
        type={type}
        value={value}
        onChange={onChange}
        placeholder={placeholder}
        autoComplete={autoComplete}
        required={required}
        aria-invalid={!!error}
        aria-describedby={error ? `${id}-error` : (helperText ? `${id}-help` : undefined)}
        className={clsx("input", error && "input-invalid")}
      />
      {error ? (
        <p id={`${id}-error`} role="alert" className="error-text mt-1">{error}</p>
      ) : helperText ? (
        <p id={`${id}-help`} className="helper mt-1">{helperText}</p>
      ) : null}
    </div>
  );
}