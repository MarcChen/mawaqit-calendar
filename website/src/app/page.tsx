'use client';

import { MosqueMetadata } from '@/types/mosque';
import MosqueCard from '@/components/MosqueCard';
import { useState, useEffect, useMemo } from 'react';

export default function Home() {
  const [mosqueData, setMosqueData] = useState<Record<string, MosqueMetadata>>({});
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');

  // Load mosque data from public folder
  useEffect(() => {
    const loadMosqueData = async () => {
      try {
        const url = '/data/mosque_metadata.json';
        
        console.log('Attempting to fetch from:', url);
        console.log('NODE_ENV:', process.env.NODE_ENV);
        
        const response = await fetch(url);
        
        console.log('Response status:', response.status);
        console.log('Response ok:', response.ok);
        
        if (!response.ok) {
          throw new Error(`Failed to fetch mosque data: ${response.status} ${response.statusText}`);
        }
        
        const data = await response.json();
        console.log('Data loaded successfully:', Object.keys(data).length, 'mosques');
        setMosqueData(data);
      } catch (error) {
        console.error('Error loading mosque data:', error);
      } finally {
        setLoading(false);
      }
    };

    loadMosqueData();
  }, []);

  const filteredMosques = useMemo(() => {
    return Object.entries(mosqueData).filter(([key, mosque]) => {
      // Text search
      const matchesSearch = searchTerm === '' || 
        mosque.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
        mosque.association.toLowerCase().includes(searchTerm.toLowerCase()) ||
        key.toLowerCase().includes(searchTerm.toLowerCase());

      return matchesSearch;
    });
  }, [mosqueData, searchTerm]);

  if (loading) {
    return (
      <main className="min-h-screen bg-gradient-to-br from-green-50 to-blue-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-green-600 mx-auto mb-4"></div>
          <p className="text-xl text-gray-600">Loading mosque data...</p>
        </div>
      </main>
    );
  }

  return (
    <main className="min-h-screen bg-gradient-to-br from-green-50 to-blue-50">
      {/* Construction Notice Banner */}
      <div className="bg-orange-100 border-l-4 border-orange-500 text-orange-700 p-4">
        <div className="container mx-auto px-4">
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <svg className="h-5 w-5 text-orange-500" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor">
                <path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
              </svg>
            </div>
            <div className="ml-3">
                <p className="text-sm font-medium">
                🚧 This website is still under construction. Not all mosques are available yet. If you want to add a mosque, please visit our <a href="https://github.com/MarcChen/mawaqit-calendar/issues" target="_blank" rel="noopener noreferrer" className="underline text-orange-700 hover:text-orange-900">GitHub page</a> and create an issue.
                </p>
            </div>
          </div>
        </div>
      </div>

      <div className="container mx-auto px-4 py-8">
        <header className="text-center mb-12">
          <h1 className="text-4xl md:text-6xl font-bold text-gray-800 mb-4">
            🕌 Mawaqit Calendar
          </h1>
          <p className="text-xl text-gray-600 max-w-2xl mx-auto">
            Discover mosque information and stay connected with your local Islamic community
          </p>
        </header>

        {/* Search Bar */}
        <div className="max-w-4xl mx-auto mb-8 bg-white rounded-lg shadow-md p-6">
          <div className="mb-4">
            <label htmlFor="search" className="block text-sm font-medium text-gray-700 mb-2">
              Search mosques
            </label>
            <input
              type="text"
              id="search"
              placeholder="Search by name, association, or location..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent outline-none text-gray-800"
            />
          </div>

          {/* Results count */}
          <div className="text-sm text-gray-600">
            {filteredMosques.length} mosque{filteredMosques.length !== 1 ? 's' : ''} found
          </div>
        </div>
        
        {/* Mosque Cards */}
        <div className="max-w-4xl mx-auto space-y-8">
          {filteredMosques.length > 0 ? (
            filteredMosques.map(([mosqueKey, mosque]) => (
              <MosqueCard key={mosqueKey} mosque={mosque} />
            ))
          ) : (
            <div className="text-center py-12">
              <p className="text-xl text-gray-500">No mosques found matching your criteria</p>
              <button
                onClick={() => setSearchTerm('')}
                className="mt-4 px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors"
              >
                Clear search
              </button>
            </div>
          )}
        </div>
        
        <footer className="text-center mt-16 text-gray-500">
          <p className="mb-4">Data sourced from Mawaqit • {Object.keys(mosqueData).length} mosques available</p>
          <a
            href="https://github.com/MarcChen/mawaqit-calendar"
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center gap-2 px-4 py-2 bg-gray-800 text-white rounded-lg hover:bg-gray-700 transition-colors"
          >
            <svg
              className="w-5 h-5"
              fill="currentColor"
              viewBox="0 0 24 24"
              xmlns="http://www.w3.org/2000/svg"
            >
              <path d="M12 0c-6.626 0-12 5.373-12 12 0 5.302 3.438 9.8 8.207 11.387.599.111.793-.261.793-.577v-2.234c-3.338.726-4.033-1.416-4.033-1.416-.546-1.387-1.333-1.756-1.333-1.756-1.089-.745.083-.729.083-.729 1.205.084 1.839 1.237 1.839 1.237 1.07 1.834 2.807 1.304 3.492.997.107-.775.418-1.305.762-1.604-2.665-.305-5.467-1.334-5.467-5.931 0-1.311.469-2.381 1.236-3.221-.124-.303-.535-1.524.117-3.176 0 0 1.008-.322 3.301 1.23.957-.266 1.983-.399 3.003-.404 1.02.005 2.047.138 3.006.404 2.291-1.552 3.297-1.23 3.297-1.23.653 1.653.242 2.874.118 3.176.77.84 1.235 1.911 1.235 3.221 0 4.609-2.807 5.624-5.479 5.921.43.372.823 1.102.823 2.222v3.293c0 .319.192.694.801.576 4.765-1.589 8.199-6.086 8.199-11.386 0-6.627-5.373-12-12-12z"/>
            </svg>
            View on GitHub
          </a>
        </footer>
      </div>
    </main>
  );
}
