import { MosqueMetadata } from '@/types/mosque';
import MosqueCard from '@/components/MosqueCard';
import { Metadata } from 'next';

export const metadata: Metadata = {
  title: 'Mawaqit Calendar - Mosque Information',
  description: 'Display mosque information and prayer times from Mawaqit',
};

// Hardcoded mosque data for static generation
const mosqueData: MosqueMetadata = {
  latitude: 48.8174572,
  longitude: 2.3940178,
  name: "Mosquée ANNOUR - Ivry-Sur-Seine",
  url: "https://mawaqit.net/fr/annour-ivry-sur-seine",
  label: "Mosquée ANNOUR - Ivry-Sur-Seine",
  logo: null,
  site: null,
  association: "Association des musulmans d'ivry A M I",
  steamUrl: "",
  scrapedAt: "2025-09-05T11:21:16.493573+02:00",
  parking: true,
  ablutions: true,
  ramadanMeal: true,
  otherInfo: null,
  womenSpace: true,
  janazaPrayer: true,
  aidPrayer: true,
  adultCourses: true,
  childrenCourses: true,
  handicapAccessibility: true,
  paymentWebsite: "https://www.helloasso.com/associations/collectif-annour/collectes/centre-annour",
  countryCode: "FR",
  timezone: "Europe/Paris",
  image: "https://cdn.mawaqit.net/images/backend/mosque/643f114c-4c4c-4e4b-ab0a-7d6725756818/mosque/1eea8db7-31f5-6ba2-b224-066ed47a7584.jpg",
  interiorPicture: "https://cdn.mawaqit.net/images/backend/mosque/643f114c-4c4c-4e4b-ab0a-7d6725756818/mosque/1eea8db7-31f5-6ba2-b224-066ed47a7584.jpg",
  exteriorPicture: "https://cdn.mawaqit.net/images/backend/mosque/643f114c-4c4c-4e4b-ab0a-7d6725756818/mosque/1eea8db7-3711-687a-81f9-066ed47a7584.jpg",
  calendarUrl: "https://calendar.google.com/calendar/ical/614e8a4cb293fcfc093f481be59e9c588a6d507a49d1b341413f16f62741c5a4%40group.calendar.google.com/public/basic.ics"
};

export default function Home() {
  return (
    <main className="min-h-screen bg-gradient-to-br from-green-50 to-blue-50">
      <div className="container mx-auto px-4 py-8">
        <header className="text-center mb-12">
          <h1 className="text-4xl md:text-6xl font-bold text-gray-800 mb-4">
            🕌 Mawaqit Calendar
          </h1>
          <p className="text-xl text-gray-600 max-w-2xl mx-auto">
            Discover mosque information and stay connected with your local Islamic community
          </p>
        </header>
        
        <div className="max-w-4xl mx-auto">
          <MosqueCard mosque={mosqueData} />
        </div>
        
        <footer className="text-center mt-16 text-gray-500">
          <p>Data sourced from Mawaqit • Last updated: {new Date(mosqueData.scrapedAt).toLocaleDateString()}</p>
        </footer>
      </div>
    </main>
  );
}
