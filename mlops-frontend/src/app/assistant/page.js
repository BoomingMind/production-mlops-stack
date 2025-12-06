'use client';

import { useState, useEffect } from 'react';
import { RAGChat } from '@/components/rag/RAGChat';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/Card';
import { getRAGSources } from '@/lib/api';
import { MessageCircle, FileText, BookOpen, AlertCircle, CheckCircle2 } from 'lucide-react';

export default function AssistantPage() {
  const [sources, setSources] = useState(null);
  const [sourcesError, setSourcesError] = useState(null);

  useEffect(() => {
    async function fetchSources() {
      try {
        const response = await getRAGSources();
        if (response.success) {
          setSources(response);
        } else {
          setSourcesError(response.error);
        }
      } catch (err) {
        setSourcesError(err.message);
      }
    }
    fetchSources();
  }, []);

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-950">
      {/* Header */}
      <section className="bg-white dark:bg-gray-900 border-b border-gray-200 dark:border-gray-800">
        <div className="container mx-auto px-4 py-8">
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white flex items-center gap-3">
            <MessageCircle className="w-8 h-8 text-blue-600" />
            AI Assistant
          </h1>
          <p className="text-gray-600 dark:text-gray-400 mt-1">
            Ask questions about air quality, health precautions, and environmental guidance
          </p>
        </div>
      </section>

      <main className="container mx-auto px-4 py-8">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Chat Component */}
          <div className="lg:col-span-2">
            <RAGChat />
          </div>

          {/* Sidebar */}
          <div className="space-y-6">
            {/* Knowledge Sources */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2 text-lg">
                  <BookOpen className="w-5 h-5" />
                  Knowledge Sources
                </CardTitle>
                <CardDescription>
                  Documents indexed for AI assistance
                </CardDescription>
              </CardHeader>
              <CardContent>
                {sourcesError ? (
                  <div className="flex items-center gap-2 text-sm text-amber-600 dark:text-amber-400">
                    <AlertCircle className="w-4 h-4" />
                    <span>RAG system not available</span>
                  </div>
                ) : sources ? (
                  <div className="space-y-3">
                    <div className="flex items-center justify-between text-sm">
                      <span className="text-gray-600 dark:text-gray-400">Total documents:</span>
                      <span className="font-medium text-gray-900 dark:text-white">
                        {sources.document_count}
                      </span>
                    </div>
                    <div className="border-t border-gray-200 dark:border-gray-700 pt-3">
                      <p className="text-sm text-gray-500 dark:text-gray-400 mb-2">Sources:</p>
                      <div className="space-y-2">
                        {sources.sources?.map((source, index) => (
                          <div
                            key={index}
                            className="flex items-center gap-2 p-2 bg-gray-50 dark:bg-gray-800 rounded-lg"
                          >
                            <FileText className="w-4 h-4 text-blue-600" />
                            <span className="text-sm text-gray-700 dark:text-gray-300">
                              {source}
                            </span>
                          </div>
                        ))}
                      </div>
                    </div>
                  </div>
                ) : (
                  <div className="animate-pulse space-y-3">
                    <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded w-3/4" />
                    <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded w-1/2" />
                  </div>
                )}
              </CardContent>
            </Card>

            {/* Tips Card */}
            <Card>
              <CardHeader>
                <CardTitle className="text-lg">Tips for Better Answers</CardTitle>
              </CardHeader>
              <CardContent>
                <ul className="space-y-3 text-sm text-gray-600 dark:text-gray-400">
                  <li className="flex items-start gap-2">
                    <CheckCircle2 className="w-4 h-4 text-green-500 mt-0.5 flex-shrink-0" />
                    <span>Ask specific questions about AQI levels and their effects</span>
                  </li>
                  <li className="flex items-start gap-2">
                    <CheckCircle2 className="w-4 h-4 text-green-500 mt-0.5 flex-shrink-0" />
                    <span>Include AQI values when asking about precautions</span>
                  </li>
                  <li className="flex items-start gap-2">
                    <CheckCircle2 className="w-4 h-4 text-green-500 mt-0.5 flex-shrink-0" />
                    <span>Ask about specific pollutants like PM2.5, O3, or NO2</span>
                  </li>
                  <li className="flex items-start gap-2">
                    <CheckCircle2 className="w-4 h-4 text-green-500 mt-0.5 flex-shrink-0" />
                    <span>Inquire about health recommendations for different groups</span>
                  </li>
                </ul>
              </CardContent>
            </Card>

            {/* Example Questions */}
            <Card>
              <CardHeader>
                <CardTitle className="text-lg">Example Questions</CardTitle>
              </CardHeader>
              <CardContent>
                <ul className="space-y-2 text-sm">
                  <li className="p-2 bg-blue-50 dark:bg-blue-900/20 rounded-lg text-blue-700 dark:text-blue-300">
                    "What activities should I avoid when AQI is 150?"
                  </li>
                  <li className="p-2 bg-blue-50 dark:bg-blue-900/20 rounded-lg text-blue-700 dark:text-blue-300">
                    "How does PM2.5 affect health?"
                  </li>
                  <li className="p-2 bg-blue-50 dark:bg-blue-900/20 rounded-lg text-blue-700 dark:text-blue-300">
                    "What precautions should children take?"
                  </li>
                  <li className="p-2 bg-blue-50 dark:bg-blue-900/20 rounded-lg text-blue-700 dark:text-blue-300">
                    "Explain the different AQI categories"
                  </li>
                </ul>
              </CardContent>
            </Card>
          </div>
        </div>
      </main>
    </div>
  );
}
