"use client";
import { ButtonHTMLAttributes } from "react";
import clsx from "clsx";

export default function Button({
  className, children, ...props
}: ButtonHTMLAttributes<HTMLButtonElement>) {
  return (
    <button
      className={clsx("btn-primary", className)}
      {...props}
    >
      {children}
    </button>
  );
}