import React from 'react';
import { DollarSign, Home, MapPin, Maximize2, Minimize2, Ruler, X } from 'lucide-react';

const reasons = [
  { id: 'price_too_high', label: 'Price is high', icon: DollarSign },
  { id: 'location', label: 'Location mismatch', icon: MapPin },
  { id: 'size_too_small', label: 'Too small', icon: Minimize2 },
  { id: 'size_too_large', label: 'Too large', icon: Maximize2 },
  { id: 'style', label: 'Style mismatch', icon: Home },
  { id: 'other', label: 'Other reason', icon: Ruler },
];

const FeedbackModal = ({ isOpen, onClose, onSubmit }) => {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-slate-950/70 z-50 flex items-end sm:items-center justify-center p-0 sm:p-4" onClick={onClose}>
      <section
        className="lyrio-feedback-modal w-full sm:max-w-md rounded-t-3xl sm:rounded-2xl p-6 animate-slide-up"
        onClick={(event) => event.stopPropagation()}
      >
        <div className="flex items-center justify-between mb-2">
          <h3 className="lyrio-heading text-xl text-slate-900">Improve your next matches</h3>
          <button
            onClick={onClose}
            className="lyrio-close-btn portal-action-btn lyrio-focus rounded-full p-2 border lyrio-border-default"
            aria-label="Close feedback modal"
          >
            <X size={18} />
          </button>
        </div>

        <p className="lyrio-text-muted text-sm mb-4">Tell us why this property missed the mark.</p>

        <div className="grid grid-cols-2 gap-3">
          {reasons.map(({ id, label, icon: Icon }) => (
            <button
              key={id}
              onClick={() => onSubmit(id)}
              className="lyrio-feedback-option lyrio-focus text-left rounded-xl p-3 border transition-all"
            >
              <Icon size={16} className="lyrio-text-primary" />
              <p className="mt-2 text-sm font-semibold text-slate-900">{label}</p>
            </button>
          ))}
        </div>

        <button
          onClick={() => onSubmit(null)}
          className="lyrio-focus mt-4 w-full text-sm font-semibold rounded-xl py-3 border lyrio-border-default lyrio-text-muted"
        >
          Skip for now
        </button>
      </section>
    </div>
  );
};

export default FeedbackModal;
