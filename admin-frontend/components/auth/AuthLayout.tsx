"use client";
import { ReactNode } from "react";
import AuthNavbar from "./AuthNavbar";

export default function AuthLayout({ children, title, subtitle }: {
  children: ReactNode; title: string; subtitle?: string;
}) {
  return (
    <div className="min-h-screen">
      <div className="absolute top-0 left-0 right-0 z-10">
        <AuthNavbar />
      </div>
      <div className="min-h-screen flex items-center justify-center px-6 py-12">
        <div className="w-full max-w-md">
          <div className="mb-8 text-center">
            <h1 className="text-3xl font-semibold mb-2">{title}</h1>
            {subtitle && <p className="text-lg text-neutral-600 dark:text-neutral-400">{subtitle}</p>}
          </div>
          <div className="card p-6">
            {children}
          </div>
        </div>
      </div>
    </div>
  );
}