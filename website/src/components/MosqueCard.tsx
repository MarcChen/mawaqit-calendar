"use client";

import { MosqueMetadata } from '@/types/mosque';
import Image from 'next/image';
import { useEffect, useState } from 'react';
import CalendarSubscription from './CalendarSubscription';

interface MosqueCardProps {
  mosque: MosqueMetadata;
}

const FeatureIcon = ({ enabled, icon, label }: { enabled: boolean; icon: string; label: string }) => (
  <div className={`flex items-center space-x-2 px-3 py-2 rounded-lg ${enabled ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-600'}`}>
    <span className="text-lg">{icon}</span>
    <span className="text-sm font-medium">{label}</span>
  </div>
);

export default function MosqueCard({ mosque }: MosqueCardProps) {
  const [calendarEmbedUrl, setCalendarEmbedUrl] = useState<string>('');

  useEffect(() => {
    // Extract calendar ID from the calendarUrl
    const extractCalendarId = (url: string): string | null => {
      if (!url) return null;
      const match = url.match(/\/([^\/]+)\/public\/basic\.ics$/);
      return match ? match[1] : null;
    };

    // Get browser timezone
    const browserTimezone = Intl.DateTimeFormat().resolvedOptions().timeZone;

    // Build the embed URL
    const calendarId = extractCalendarId(mosque.calendarUrl);
    console.log('extracted calendarId:', calendarId);

    if (calendarId) {
      const embedUrl = `https://calendar.google.com/calendar/embed?src=${calendarId}&ctz=${encodeURIComponent(browserTimezone)}&mode=AGENDA`;
      setCalendarEmbedUrl(embedUrl);
    } else {
      console.log('No calendar ID found, calendarUrl might be missing or in wrong format');
      setCalendarEmbedUrl('');
    }
  }, [mosque.calendarUrl]);

  const features = [
    { key: 'parking', icon: '🚗', label: 'Parking' },
    { key: 'ablutions', icon: '🚿', label: 'Ablutions' },
    { key: 'womenSpace', icon: '👩', label: 'Women Space' },
    { key: 'handicapAccessibility', icon: '♿', label: 'Accessible' },
    { key: 'ramadanMeal', icon: '🍽️', label: 'Ramadan Meals' },
    { key: 'janazaPrayer', icon: '🤲', label: 'Janaza Prayer' },
    { key: 'aidPrayer', icon: '🌙', label: 'Eid Prayer' },
    { key: 'adultCourses', icon: '📚', label: 'Adult Courses' },
    { key: 'childrenCourses', icon: '👶', label: 'Children Courses' },
  ];

  return (
    <div className="bg-white rounded-2xl shadow-xl overflow-hidden">
      {/* Header with Image */}
      <div className="relative h-64 md:h-80">
        <Image
          src={mosque.image}
          alt={mosque.name}
          fill
          className="object-cover"
          priority
        />
        <div className="absolute inset-0 bg-gradient-to-t from-black/60 via-transparent to-transparent" />

        {/* Calendar Subscription Button - Top Right */}
        {mosque.calendarUrl && (
          <div className="absolute top-4 right-4">
            <CalendarSubscription
              calendarUrl={mosque.calendarUrl}
              mosqueName={mosque.name}
            />
          </div>
        )}

        <div className="absolute bottom-6 left-6 right-6">
          <h2 className="text-2xl md:text-3xl font-bold text-white mb-2">
            {mosque.name}
          </h2>
          <p className="text-gray-200 text-lg">{mosque.association}</p>
        </div>
      </div>

      {/* Prayer Times Calendar */}
      <div className="p-6 md:p-8 border-b border-gray-200">
        <h3 className="text-xl font-semibold text-gray-800 mb-4">🕐 Prayer Times Calendar</h3>
        <div className="w-full flex justify-center">
          {calendarEmbedUrl ? (
            <iframe
              src={calendarEmbedUrl}
              style={{ border: 0 }}
              width="100%"
              height="600"
              frameBorder="0"
              scrolling="no"
              className="rounded-lg shadow"
              allowFullScreen
              title="Mosque Google Calendar"
            />
          ) : (
            <div className="w-full h-96 bg-gray-100 rounded-lg flex items-center justify-center">
              <p className="text-gray-500">Loading calendar...</p>
            </div>
          )}
        </div>
      </div>

      {/* Content */}
      <div className="p-6 md:p-8">
        {/* Location & Contact */}
        <div className="grid md:grid-cols-2 gap-6 mb-8">
          <div className="space-y-4">
            <h3 className="text-xl font-semibold text-gray-800 mb-3">📍 Location</h3>
            <div className="space-y-2">
              <a
                href={`https://www.google.com/maps?q=${mosque.latitude},${mosque.longitude}`}
                target="_blank"
                rel="noopener noreferrer"
                className="block text-blue-600 hover:text-blue-800 underline"
              >
                🗺️ View on Google Maps
              </a>
            </div>
          </div>

          <div className="space-y-4">
            <h3 className="text-xl font-semibold text-gray-800 mb-3">🔗 Links</h3>
            <div className="space-y-2">
              <a
                href={mosque.url}
                target="_blank"
                rel="noopener noreferrer"
                className="block text-blue-600 hover:text-blue-800 underline"
              >
                🌐 Mawaqit Page
              </a>
              {mosque.paymentWebsite && (
                <a
                  href={mosque.paymentWebsite}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="block text-green-600 hover:text-green-800 underline"
                >
                  💳 Donation Page
                </a>
              )}
            </div>
          </div>
        </div>

        {/* Features */}
        <div className="mb-8">
          <h3 className="text-xl font-semibold text-gray-800 mb-4">🏛️ Facilities & Services</h3>
          <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
            {features.map(({ key, icon, label }) => (
              <FeatureIcon
                key={key}
                enabled={mosque[key as keyof MosqueMetadata] as boolean}
                icon={icon}
                label={label}
              />
            ))}
          </div>
        </div>

        {/* Gallery */}
        {(mosque.interiorPicture || mosque.exteriorPicture) && (
          <div className="mb-8">
            <h3 className="text-xl font-semibold text-gray-800 mb-4">📸 Gallery</h3>
            <div className="grid md:grid-cols-2 gap-4">
              {mosque.exteriorPicture && mosque.exteriorPicture !== mosque.image && (
                <div className="relative h-48 rounded-lg overflow-hidden">
                  <Image
                    src={mosque.exteriorPicture}
                    alt="Exterior view"
                    fill
                    className="object-cover"
                  />
                  <div className="absolute bottom-2 left-2 bg-black/70 text-white px-2 py-1 rounded text-sm">
                    Exterior
                  </div>
                </div>
              )}
              {mosque.interiorPicture && mosque.interiorPicture !== mosque.image && (
                <div className="relative h-48 rounded-lg overflow-hidden">
                  <Image
                    src={mosque.interiorPicture}
                    alt="Interior view"
                    fill
                    className="object-cover"
                  />
                  <div className="absolute bottom-2 left-2 bg-black/70 text-white px-2 py-1 rounded text-sm">
                    Interior
                  </div>
                </div>
              )}
            </div>
          </div>
        )}

        {/* Footer Info */}
        <div className="pt-6 border-t border-gray-200">
          <div className="flex flex-col md:flex-row md:items-center md:justify-between text-sm text-gray-500">
            <p>
              Data last updated: {new Date(mosque.scrapedAt).toLocaleDateString('en-US', {
                year: 'numeric',
                month: 'long',
                day: 'numeric',
                hour: '2-digit',
                minute: '2-digit'
              })}
            </p>
            <p className="mt-2 md:mt-0">
              Source: <span className="font-medium">Mawaqit.net</span>
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
