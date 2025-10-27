"use client";
import { NavbarLogo } from "@/components/ui/Logo";

export default function AuthNavbar() {
  return (
    <nav className="w-full">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center h-16">
          {/* Logo - Centered on mobile, left-aligned on desktop */}
          <div className="w-full md:w-auto flex justify-center md:justify-start">
            <NavbarLogo />
          </div>
          
          {/* Optional: Add navigation items for desktop */}
          <div className="hidden md:flex items-center space-x-4 ml-auto">
            {/* You can add navigation items here if needed */}
          </div>
        </div>
      </div>
    </nav>
  );
}