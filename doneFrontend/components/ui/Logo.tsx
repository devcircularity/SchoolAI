"use client";
import Link from "next/link";
import { cva, type VariantProps } from "class-variance-authority";
import clsx from "clsx";

const logoVariants = cva(
  "flex items-center gap-3",
  {
    variants: {
      size: {
        sm: "", // Small - for navbar
        md: "", // Medium - for auth pages
        lg: "", // Large - for landing pages
      },
    },
    defaultVariants: {
      size: "sm",
    },
  }
);

const iconVariants = cva(
  "relative rounded-xl bg-gradient-to-br from-[#1f7daf] to-[#104f73] grid place-items-center text-white font-bold shadow-lg ring-2 ring-[#1f7daf]/20",
  {
    variants: {
      size: {
        sm: "h-9 w-9 text-lg",
        md: "h-12 w-12 text-xl",
        lg: "h-16 w-16 text-2xl",
      },
    },
    defaultVariants: {
      size: "sm",
    },
  }
);

const textVariants = cva(
  "font-semibold bg-gradient-to-r from-[#1f7daf] to-[#104f73] bg-clip-text text-transparent",
  {
    variants: {
      size: {
        sm: "text-xl",
        md: "text-2xl",
        lg: "text-3xl",
      },
    },
    defaultVariants: {
      size: "sm",
    },
  }
);

interface LogoProps extends VariantProps<typeof logoVariants> {
  href?: string;
  className?: string;
  showText?: boolean;
}

export default function Logo({ 
  size = "sm", 
  href = "/", 
  className,
  showText = true 
}: LogoProps) {
  const content = (
    <div className={clsx(logoVariants({ size }), className)}>
      <div className={iconVariants({ size })}>
        <span className="drop-shadow-sm">O</span>
      </div>
      {showText && (
        <span className={textVariants({ size })}>
          Olaji
        </span>
      )}
    </div>
  );

  if (href) {
    return (
      <Link href={href}>
        {content}
      </Link>
    );
  }

  return content;
}

// Convenience components for specific use cases
export function NavbarLogo({ className }: { className?: string }) {
  return <Logo size="sm" className={className} />;
}

export function AuthLogo({ className }: { className?: string }) {
  return <Logo size="md" className={className} />;
}

export function HeroLogo({ className }: { className?: string }) {
  return <Logo size="lg" className={className} />;
}

export function LogoIcon({ size = "sm", className }: { size?: "sm" | "md" | "lg"; className?: string }) {
  return <Logo size={size} showText={false} href={undefined} className={className} />;
}