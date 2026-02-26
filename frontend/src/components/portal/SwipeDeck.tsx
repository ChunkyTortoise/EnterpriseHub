'use client';

import { useEffect, useMemo, useState } from 'react';
import { Check, Loader2, RefreshCw, X } from 'lucide-react';
import { Button } from '../ui/Button';
import styles from './swipe-deck.module.css';

type PropertyRecord = {
  id?: string;
  property_id?: string;
  price?: number;
  address?: string;
  city?: string;
  state?: string;
  beds?: number;
  bedrooms?: number;
  baths?: number;
  bathrooms?: number;
  sqft?: number;
  square_feet?: number;
  image_url?: string;
  photos?: string[];
};

export interface SwipeDeckProps {
  properties?: PropertyRecord[];
  leadId?: string;
  contactId?: string;
  locationId?: string;
  apiBaseUrl?: string;
  onComplete?: () => void;
  onError?: (error: unknown) => void;
}

function readPropId(property: PropertyRecord) {
  return property.id || property.property_id;
}

export function SwipeDeck({
  properties,
  leadId,
  contactId,
  locationId,
  apiBaseUrl = '/api',
  onComplete,
  onError,
}: SwipeDeckProps) {
  const [deck, setDeck] = useState<PropertyRecord[]>(Array.isArray(properties) ? properties : []);
  const [currentIndex, setCurrentIndex] = useState((Array.isArray(properties) ? properties.length : 0) - 1);
  const [loading, setLoading] = useState(false);
  const [loadingError, setLoadingError] = useState<string | null>(null);
  const [submitError, setSubmitError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [exitDirection, setExitDirection] = useState<'left' | 'right' | null>(null);

  const resolvedContactId = contactId || leadId;

  useEffect(() => {
    if (Array.isArray(properties) && properties.length > 0) {
      setDeck(properties);
      setCurrentIndex(properties.length - 1);
    }
  }, [properties]);

  useEffect(() => {
    const shouldFetch = (!Array.isArray(properties) || properties.length === 0) && resolvedContactId;
    if (!shouldFetch) {
      return;
    }

    let ignore = false;

    const fetchDeck = async () => {
      setLoading(true);
      setLoadingError(null);

      try {
        const params = new URLSearchParams();
        if (resolvedContactId) params.set('contact_id', resolvedContactId);
        if (leadId) params.set('lead_id', leadId);
        if (locationId) params.set('location_id', locationId);

        const response = await fetch(`${apiBaseUrl}/portal/deck?${params.toString()}`);
        if (!response.ok) {
          throw new Error(`Deck request failed: ${response.status}`);
        }

        const payload = await response.json();
        const incoming = (payload.deck || payload.properties || []) as PropertyRecord[];
        if (!ignore) {
          setDeck(incoming);
          setCurrentIndex(incoming.length - 1);
        }
      } catch (error) {
        if (!ignore) {
          setLoadingError('Could not load your property matches.');
        }
        onError?.(error);
      } finally {
        if (!ignore) {
          setLoading(false);
        }
      }
    };

    fetchDeck();

    return () => {
      ignore = true;
    };
  }, [apiBaseUrl, contactId, leadId, locationId, onError, properties, resolvedContactId]);

  useEffect(() => {
    if (deck.length > 0 && currentIndex < 0) {
      onComplete?.();
    }
  }, [currentIndex, deck.length, onComplete]);

  const reviewed = useMemo(() => Math.max(deck.length - (currentIndex + 1), 0), [deck.length, currentIndex]);
  const currentProperty = currentIndex >= 0 ? deck[currentIndex] : null;

  const submitSwipe = async (action: 'like' | 'pass') => {
    if (!currentProperty || isSubmitting) {
      return;
    }

    setSubmitError(null);
    setIsSubmitting(true);
    setExitDirection(action === 'like' ? 'right' : 'left');

    // Demo mode: no backend, just animate and advance
    if (!resolvedContactId) {
      setTimeout(() => {
        setCurrentIndex((prev) => prev - 1);
        setExitDirection(null);
        setIsSubmitting(false);
      }, 350);
      return;
    }

    try {
      const body = {
        lead_id: leadId || resolvedContactId,
        contact_id: resolvedContactId,
        property_id: readPropId(currentProperty),
        action,
        location_id: locationId,
      };

      const response = await fetch(`${apiBaseUrl}/portal/swipe`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
      });

      if (!response.ok) {
        throw new Error(`Swipe request failed: ${response.status}`);
      }

      setTimeout(() => {
        setCurrentIndex((prev) => prev - 1);
        setExitDirection(null);
        setIsSubmitting(false);
      }, 350);
    } catch (error) {
      setSubmitError('Could not submit your choice. Please retry.');
      setExitDirection(null);
      setIsSubmitting(false);
      onError?.(error);
    }
  };

  if (loading) {
    return (
      <section className={styles.deckShell}>
        <div className={styles.stateCard}>
          <h2 className={styles.deckTitle}><Loader2 size={16} className="inline animate-spin" /> Curating your matches</h2>
          <p className={styles.stateBody}>Analyzing preferences and market fit in real time.</p>
        </div>
      </section>
    );
  }

  if (loadingError) {
    return (
      <section className={styles.deckShell}>
        <div className={styles.stateCard}>
          <h2 className={styles.deckTitle}>Deck unavailable</h2>
          <p className={styles.stateBody}>{loadingError}</p>
          <Button variant="secondary" onClick={() => window.location.reload()} icon={<RefreshCw size={16} />}>
            Retry
          </Button>
        </div>
      </section>
    );
  }

  const cardClass = [
    styles.propertyCard,
    exitDirection === 'left' ? styles.propertyCardExiting : '',
    exitDirection === 'right' ? styles.propertyCardExitingRight : '',
  ].filter(Boolean).join(' ');

  return (
    <section className={styles.deckShell}>
      <header className={styles.deckHeader}>
        <div>
          <h2 className={styles.deckTitle}>Your Daily Matches</h2>
          <p className={styles.deckMeta}>{reviewed} reviewed • {Math.max(deck.length - reviewed, 0)} remaining</p>
        </div>
        <span className={styles.progressPill}>{Math.max(currentIndex + 1, 0)} / {deck.length}</span>
      </header>

      {currentProperty ? (
        <article className={cardClass} aria-label={`Property ${currentIndex + 1} of ${deck.length}`}>
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img
            className={styles.propertyImage}
            src={currentProperty.image_url || currentProperty.photos?.[0] || '/placeholder-property.jpg'}
            alt={currentProperty.address || 'Property listing'}
            loading="eager"
          />
          <div className={styles.propertyContent}>
            <h3 className={styles.propertyPrice}>${(currentProperty.price || 0).toLocaleString()}</h3>
            <p className={styles.propertyAddress}>
              {currentProperty.address || 'Address unavailable'}
              {currentProperty.city ? `, ${currentProperty.city}` : ''}
              {currentProperty.state ? `, ${currentProperty.state}` : ''}
            </p>
            <div className={styles.statRow}>
              <span className={styles.statChip}>{currentProperty.beds || currentProperty.bedrooms || 0} bd</span>
              <span className={styles.statChip}>{currentProperty.baths || currentProperty.bathrooms || 0} ba</span>
              <span className={styles.statChip}>{(currentProperty.sqft || currentProperty.square_feet || 0).toLocaleString()} sqft</span>
            </div>
          </div>
        </article>
      ) : (
        <div className={styles.stateCard}>
          <h3 className={styles.deckTitle}>You&apos;re all caught up!</h3>
          <p className={styles.stateBody}>Jorge will follow up on your liked properties within 24 hours.</p>
        </div>
      )}

      {submitError ? <p className={styles.error}>{submitError}</p> : null}

      {currentProperty ? (
        <footer className={styles.actionDock}>
          <Button
            variant="secondary"
            className={styles.passButton}
            onClick={() => submitSwipe('pass')}
            disabled={isSubmitting}
            aria-label="Pass on this property"
            icon={<X size={18} />}
          >
            Pass
          </Button>
          <p className={styles.actionHint}>Choose to train your next matches</p>
          <Button
            variant="primary"
            className={styles.likeButton}
            onClick={() => submitSwipe('like')}
            disabled={isSubmitting}
            aria-label="Like this property"
            icon={<Check size={18} />}
          >
            Like
          </Button>
        </footer>
      ) : null}
    </section>
  );
}
