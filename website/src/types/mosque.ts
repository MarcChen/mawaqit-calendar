export interface MosqueMetadata {
  latitude: number;
  longitude: number;
  name: string;
  url: string;
  label: string;
  logo: string | null;
  site: string | null;
  association: string;
  steamUrl: string;
  scrapedAt: string;
  parking: boolean;
  ablutions: boolean;
  ramadanMeal: boolean;
  otherInfo: string | null;
  womenSpace: boolean;
  janazaPrayer: boolean;
  aidPrayer: boolean;
  adultCourses: boolean;
  childrenCourses: boolean;
  handicapAccessibility: boolean;
  paymentWebsite: string;
  countryCode: string;
  timezone: string;
  image: string;
  interiorPicture: string;
  exteriorPicture: string;
  calendarUrl: string;
}
