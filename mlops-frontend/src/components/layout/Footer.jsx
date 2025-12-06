'use client';

import { Wind, Github, ExternalLink } from 'lucide-react';

export function Footer() {
  return (
    <footer className="border-t border-gray-200 bg-white dark:border-gray-800 dark:bg-gray-900">
      <div className="container mx-auto px-4 py-8">
        <div className="flex flex-col md:flex-row items-center justify-between gap-4">
          {/* Logo and Copyright */}
          <div className="flex items-center gap-2">
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-blue-600">
              <Wind className="h-4 w-4 text-white" />
            </div>
            <div>
              <span className="text-sm font-semibold text-gray-900 dark:text-white">
                AQI Predict
              </span>
              <p className="text-xs text-gray-500 dark:text-gray-400">
                © 2024 MLOps Project
              </p>
            </div>
          </div>

          {/* Links */}
          <div className="flex items-center gap-6">
            <a
              href="https://github.com/AbdullahIqbal26904/MLOPS_Project"
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center gap-1 text-sm text-gray-600 hover:text-gray-900 dark:text-gray-400 dark:hover:text-white transition-colors"
            >
              <Github className="w-4 h-4" />
              GitHub
            </a>
            <a
              href="/api-docs"
              className="flex items-center gap-1 text-sm text-gray-600 hover:text-gray-900 dark:text-gray-400 dark:hover:text-white transition-colors"
            >
              <ExternalLink className="w-4 h-4" />
              API Docs
            </a>
          </div>

          {/* Tech Stack */}
          <div className="flex items-center gap-2 text-xs text-gray-500 dark:text-gray-400">
            <span>Built with</span>
            <span className="px-2 py-0.5 bg-gray-100 dark:bg-gray-800 rounded">Next.js</span>
            <span className="px-2 py-0.5 bg-gray-100 dark:bg-gray-800 rounded">Flask</span>
            <span className="px-2 py-0.5 bg-gray-100 dark:bg-gray-800 rounded">ML</span>
          </div>
        </div>
      </div>
    </footer>
  );
}
