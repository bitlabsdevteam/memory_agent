'use client';

import React from 'react';
import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";
import LeftSidebar from './components/LeftSidebar';
import { ProviderProvider, useProvider } from './contexts/ProviderContext';
import { SessionProvider, useSession } from './contexts/SessionContext';

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

function LayoutContent({ children }: { children: React.ReactNode }) {
  const { currentProvider, setCurrentProvider } = useProvider();
  const { isSessionActive, handleNewSession } = useSession();
  
  return (
    <div className="flex h-screen">
      {/* Left Sidebar */}
      <LeftSidebar 
        onProviderChange={setCurrentProvider}
        currentProvider={currentProvider}
        isSessionActive={isSessionActive}
        onNewSession={handleNewSession}
      />
      
      {/* Main Content Area */}
      <main className="flex-1 overflow-auto bg-white">
        {children}
      </main>
    </div>
  );
}

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body
        className={`${geistSans.variable} ${geistMono.variable} antialiased bg-gray-50`}
      >
        <ProviderProvider>
          <SessionProvider>
            <LayoutContent>{children}</LayoutContent>
          </SessionProvider>
        </ProviderProvider>
      </body>
    </html>
  );
}
