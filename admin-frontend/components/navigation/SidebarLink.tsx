"use client";
import Link from "next/link";
import { usePathname } from "next/navigation";

export default function SidebarLink({ href, label }: { href: string; label: string }) {
  const pathname = usePathname();
  const isActive = pathname.startsWith(href);
  return (
    <Link href={href} className={`block py-2 px-3 rounded ${isActive ? "bg-blue-500 text-white" : "hover:bg-neutral-200"}`}>
      {label}
    </Link>
  );
}
