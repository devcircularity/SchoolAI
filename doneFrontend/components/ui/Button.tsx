// components/ui/Button.tsx - Updated with variants support
"use client";
import { ButtonHTMLAttributes } from "react";
import clsx from "clsx";

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'danger' | 'warning' | 'success' | 'outline';
  size?: 'sm' | 'md' | 'lg';
}

export default function Button({
  className, 
  children, 
  variant = 'primary',
  size = 'md',
  ...props
}: ButtonProps) {
  const variantClasses = {
    primary: 'btn-primary',
    secondary: 'btn-secondary',
    danger: 'btn-danger',
    warning: 'btn-warning',
    success: 'btn-success',
    outline: 'btn-outline'
  };

  const sizeClasses = {
    sm: 'btn-sm',
    md: '',
    lg: 'btn-lg'
  };

  return (
    <button
      className={clsx(
        "btn",
        variantClasses[variant],
        sizeClasses[size],
        className
      )}
      {...props}
    >
      {children}
    </button>
  );
}