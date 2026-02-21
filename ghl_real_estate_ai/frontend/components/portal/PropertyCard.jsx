import React from 'react';
import { Bath, Bed, MapPin, Square } from 'lucide-react';

const calculateMonthlyPayment = (price) => {
  const principal = (price || 0) * 0.8;
  const monthlyRate = 0.07 / 12;
  const numPayments = 30 * 12;
  if (!principal) return 0;
  const payment =
    (principal * (monthlyRate * Math.pow(1 + monthlyRate, numPayments))) /
    (Math.pow(1 + monthlyRate, numPayments) - 1);
  return Math.round(payment);
};

const getPropertyStats = (property) => ({
  beds: property.beds || property.bedrooms || 0,
  baths: property.baths || property.bathrooms || 0,
  sqft: property.sqft || property.square_feet || 0,
});

const PropertyCard = ({ property, index = 1, total = 1 }) => {
  const { beds, baths, sqft } = getPropertyStats(property);
  const price = property.price || 0;
  const payment = property.est_payment || calculateMonthlyPayment(price);

  return (
    <article
      className="lyrio-property-card relative w-full h-[620px] sm:h-[660px] rounded-[28px] overflow-hidden"
      aria-label={`Property ${index} of ${total}`}
    >
      <img
        src={property.image_url || property.photos?.[0] || '/placeholder-property.jpg'}
        alt={property.address || 'Property listing'}
        className="w-full h-full object-cover"
        loading={index <= 2 ? 'eager' : 'lazy'}
        decoding="async"
        draggable="false"
      />

      <div className="lyrio-property-overlay absolute inset-0" />

      <div className="absolute top-4 left-4 right-4 flex items-center justify-between gap-2">
        <span className="lyrio-chip lyrio-text-primary-strong">
          Match {index} of {total}
        </span>
        {property.status ? <span className="lyrio-chip">{property.status}</span> : null}
      </div>

      <div className="absolute bottom-0 left-0 right-0 p-6 text-white">
        <div className="flex items-end justify-between gap-4 mb-3">
          <div>
            <h2 className="lyrio-heading text-[34px] sm:text-[42px] leading-none font-bold">
              ${price.toLocaleString()}
            </h2>
            <p className="mt-2 text-sm text-emerald-300 font-semibold">~${payment.toLocaleString()}/mo estimated</p>
          </div>
          <div className="grid grid-cols-3 gap-2 text-xs sm:text-sm">
            <div className="rounded-xl bg-white/14 border border-white/20 px-2 py-2 text-center backdrop-blur-sm">
              <Bed size={14} className="mx-auto mb-1" />
              <p className="font-semibold">{beds}</p>
            </div>
            <div className="rounded-xl bg-white/14 border border-white/20 px-2 py-2 text-center backdrop-blur-sm">
              <Bath size={14} className="mx-auto mb-1" />
              <p className="font-semibold">{baths}</p>
            </div>
            <div className="rounded-xl bg-white/14 border border-white/20 px-2 py-2 text-center backdrop-blur-sm">
              <Square size={14} className="mx-auto mb-1" />
              <p className="font-semibold">{sqft.toLocaleString()}</p>
            </div>
          </div>
        </div>

        <div className="flex items-start gap-2 text-sm text-slate-100">
          <MapPin size={16} className="mt-0.5 shrink-0" />
          <p className="leading-snug">
            {property.address || 'Address unavailable'}
            {property.city ? `, ${property.city}` : ''}
            {property.state ? `, ${property.state}` : ''}
          </p>
        </div>

        {property.description ? (
          <p className="text-xs sm:text-sm text-slate-200 mt-3 line-clamp-2">{property.description}</p>
        ) : null}
      </div>
    </article>
  );
};

export default PropertyCard;
