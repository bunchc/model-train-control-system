import React from 'react';
import { Header } from './Header';
import { Footer } from './Footer';

export interface PageLayoutProps {
  children: React.ReactNode;
}

/**
 * Main page layout with header and footer
 */
export const PageLayout: React.FC<PageLayoutProps> = ({ children }) => {
  return (
    <div className="flex min-h-screen flex-col">
      <Header />
      <main className="flex-1 bg-gray-50 dark:bg-gray-900">
        <div className="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8">{children}</div>
      </main>
      <Footer />
    </div>
  );
};
