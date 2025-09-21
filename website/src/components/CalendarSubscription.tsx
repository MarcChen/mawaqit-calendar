"use client";

import { useState, useRef, useEffect } from 'react';

interface CalendarSubscriptionProps {
  calendarUrl: string;
  mosqueName: string;
  dropdownAlign?: 'left' | 'center';
}

export default function CalendarSubscription({ calendarUrl, mosqueName, dropdownAlign = 'left' }: CalendarSubscriptionProps) {
  const [isDropdownOpen, setIsDropdownOpen] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);

  const handleCalendarSubscription = (provider: 'google' | 'outlook' | 'ios') => {
    if (!calendarUrl) return;

    const encodedCalendarUrl = encodeURIComponent(calendarUrl);
    const encodedMosqueName = encodeURIComponent(mosqueName);

    switch (provider) {
      case 'google':
        window.open(`https://calendar.google.com/calendar/render?cid=${encodedCalendarUrl}`, '_blank');
        break;
      case 'outlook':
        window.open(`https://outlook.live.com/calendar/0/addcalendar?url=${encodedCalendarUrl}&name=${encodedMosqueName}`, '_blank');
        break;
      case 'ios':
        // Create a temporary link element to trigger the download/subscription
        const webcalUrl = calendarUrl.replace('https://', 'webcal://').replace('http://', 'webcal://');
        const link = document.createElement('a');
        link.href = webcalUrl;
        link.style.display = 'none';
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        break;
    }

    // Close dropdown after selection
    setIsDropdownOpen(false);
  };

  const toggleDropdown = () => {
    setIsDropdownOpen(!isDropdownOpen);
  };

  // Handle click outside to close dropdown
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setIsDropdownOpen(false);
      }
    };

    if (isDropdownOpen) {
      document.addEventListener('mousedown', handleClickOutside);
    }

    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, [isDropdownOpen]);

  return (
    <div className="relative" ref={dropdownRef}>
      <button
        onClick={toggleDropdown}
        className="bg-white/90 hover:bg-white text-gray-800 px-4 py-2 rounded-lg shadow-lg backdrop-blur-sm transition-all duration-200 flex items-center space-x-2"
      >
        <span className="text-sm font-medium">📅 Subscribe</span>
        <svg
          className={`w-4 h-4 transition-transform duration-200 ${isDropdownOpen ? 'rotate-180' : ''}`}
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
        </svg>
      </button>

      {/* Dropdown Menu */}
      <div
        className={`absolute top-full mt-2 w-48 bg-white rounded-lg shadow-xl border transition-all duration-200 z-10 ${
          isDropdownOpen ? 'opacity-100 visible' : 'opacity-0 invisible'
        }`}
        style={
          dropdownAlign === 'center'
            ? { left: '50%', transform: 'translateX(-50%)' }
            : { right: 0 }
        }
      >
        <div className="py-2">
          <button
            onClick={() => handleCalendarSubscription('google')}
            className="w-full px-4 py-2 text-left text-sm text-gray-700 hover:bg-gray-100 flex items-center space-x-3"
          >
            <img src="/Google_Calendar_icon.svg" alt="Google Calendar" className="w-5 h-5" />
            <span>Google Calendar</span>
          </button>
          <button
            onClick={() => handleCalendarSubscription('outlook')}
            className="w-full px-4 py-2 text-left text-sm text-gray-700 hover:bg-gray-100 flex items-center space-x-3"
          >
            <img src="/outlook-calendar.svg" alt="Outlook Calendar" className="w-5 h-5" />
            <span>Outlook Calendar</span>
          </button>
          <button
            onClick={() => handleCalendarSubscription('ios')}
            className="w-full px-4 py-2 text-left text-sm text-gray-700 hover:bg-gray-100 flex items-center space-x-3"
          >
            <svg className="w-5 h-5" viewBox="0 0 24 24" fill="currentColor">
              <path d="M18.71 19.5c-.83 1.24-1.71 2.45-3.05 2.47-1.34.03-1.77-.79-3.29-.79-1.53 0-2 .77-3.27.82-1.31.05-2.3-1.32-3.14-2.53C4.25 17 2.94 12.45 4.7 9.39c.87-1.52 2.43-2.48 4.12-2.51 1.28-.02 2.5.87 3.29.87.78 0 2.26-1.07 3.81-.91.65.03 2.47.26 3.64 1.98-.09.06-2.17 1.28-2.15 3.81.03 3.02 2.65 4.03 2.68 4.04-.03.07-.42 1.44-1.38 2.83M13 3.5c.73-.83 1.94-1.46 2.94-1.5.13 1.17-.34 2.35-1.04 3.19-.69.85-1.83 1.51-2.95 1.42-.15-1.15.41-2.35 1.05-3.11z"/>
            </svg>
            <span>Apple Calendar (iOS)</span>
          </button>
        </div>
      </div>
    </div>
  );
}
