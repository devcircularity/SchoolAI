// components/ui/PasswordField.tsx - Enhanced with better error handling
"use client";
import { useState } from "react";
import { Eye, EyeOff } from "lucide-react";
import TextField from "./TextField";

type Props = Omit<React.ComponentProps<typeof TextField>, "type"> & { 
  minLength?: number;
};

export default function PasswordField(props: Props) {
  const [show, setShow] = useState(false);
  
  return (
    <div className="relative">
      <TextField {...props} type={show ? "text" : "password"} />
      <button
        type="button"
        onClick={() => setShow(s => !s)}
        aria-label={show ? "Hide password" : "Show password"}
        className="absolute right-3 text-neutral-500 hover:text-neutral-700 dark:text-neutral-400 dark:hover:text-neutral-200 transition-colors"
        style={{
          top: props.label ? "38px" : "12px" // Adjust position based on whether there's a label
        }}
      >
        {show ? <EyeOff size={18} /> : <Eye size={18} />}
      </button>
    </div>
  );
}