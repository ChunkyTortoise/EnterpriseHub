import React, { useEffect, useMemo, useRef, useState } from 'react';
import TinderCard from 'react-tinder-card';
import { CheckCircle2, Heart, Loader2, RefreshCw, X } from 'lucide-react';
import axios from 'axios';
import PropertyCard from './PropertyCard';
import FeedbackModal from './FeedbackModal';
import '../../styles/lyrio-theme.css';
import '../../styles/portal-animations.css';

const SwipeDeck = ({
  properties = [],
  leadId,
  locationId,
  contactId,
  apiBaseUrl = '/api',
  onComplete,
  onError,
}) => {
  const [deck, setDeck] = useState(Array.isArray(properties) ? properties : []);
  const [currentIndex, setCurrentIndex] = useState((Array.isArray(properties) ? properties.length : 0) - 1);
  const [showFeedbackModal, setShowFeedbackModal] = useState(false);
  const [currentPassProperty, setCurrentPassProperty] = useState(null);
  const [highIntentAlert, setHighIntentAlert] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  const [loading, setLoading] = useState(false);
  const [loadingError, setLoadingError] = useState(null);

  const cardStartTime = useRef(Date.now());
  const childRefs = useRef([]);

  const resolvedContactId = contactId || leadId;
  const total = deck.length;
  const reviewed = Math.max(total - (currentIndex + 1), 0);

  useEffect(() => {
    cardStartTime.current = Date.now();
  }, [currentIndex]);

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

    const fetchDeck = async () => {
      setLoading(true);
      setLoadingError(null);
      try {
        const response = await axios.get(`${apiBaseUrl}/portal/deck`, {
          params: {
            contact_id: resolvedContactId,
            lead_id: leadId,
            location_id: locationId,
          },
        });

        const incoming = response.data.deck || response.data.properties || [];
        setDeck(incoming);
        setCurrentIndex(incoming.length - 1);
      } catch (error) {
        setLoadingError('Could not load your property matches.');
        if (onError) {
          onError(error);
        }
      } finally {
        setLoading(false);
      }
    };

    fetchDeck();
  }, [apiBaseUrl, contactId, leadId, locationId, onError, properties, resolvedContactId]);

  useEffect(() => {
    childRefs.current = deck.map((_, index) => childRefs.current[index] || React.createRef());
  }, [deck]);

  useEffect(() => {
    if (currentIndex < 0 && total > 0 && onComplete) {
      onComplete();
    }
  }, [currentIndex, onComplete, total]);

  const getTimeOnCard = () => (Date.now() - cardStartTime.current) / 1000;

  const handleInteraction = async (property, action, feedbackCategory = null, timeOnCard = null) => {
    if (isProcessing || !property) {
      return;
    }

    setIsProcessing(true);

    try {
      const payload = {
        lead_id: leadId || resolvedContactId,
        contact_id: resolvedContactId,
        property_id: property.id || property.property_id,
        action,
        location_id: locationId,
        time_on_card: timeOnCard || getTimeOnCard(),
        feedback: feedbackCategory ? { category: feedbackCategory } : null,
      };

      const response = await axios.post(`${apiBaseUrl}/portal/swipe`, payload);
      if (response.data.trigger_sms || response.data.high_intent) {
        setHighIntentAlert(true);
        setTimeout(() => setHighIntentAlert(false), 4200);
      }
    } catch (error) {
      if (onError) {
        onError(error);
      }
    } finally {
      setIsProcessing(false);
    }
  };

  const onSwipe = (direction, propertyId) => {
    const property = deck.find((item) => (item.id || item.property_id) === propertyId);
    const timeOnCard = getTimeOnCard();

    if (direction === 'left') {
      setCurrentPassProperty({ ...property, timeOnCard });
      setShowFeedbackModal(true);
      return;
    }

    if (direction === 'right') {
      handleInteraction(property, 'like', null, timeOnCard);
    }
  };

  const onCardLeftScreen = () => {
    setCurrentIndex((prevIndex) => prevIndex - 1);
  };

  const onFeedbackSubmit = (feedbackCategory) => {
    if (currentPassProperty) {
      handleInteraction(currentPassProperty, 'pass', feedbackCategory, currentPassProperty.timeOnCard);
    }
    setShowFeedbackModal(false);
    setCurrentPassProperty(null);
  };

  const swipe = async (dir) => {
    if (currentIndex >= 0 && currentIndex < deck.length && childRefs.current[currentIndex]?.current) {
      await childRefs.current[currentIndex].current.swipe(dir);
    }
  };

  const stateCard = useMemo(() => {
    if (loading) {
      return {
        title: 'Curating your personalized deck',
        body: 'Analyzing preferences and market fit in real time.',
        action: null,
        icon: <Loader2 className="animate-spin" size={18} />,
      };
    }

    if (loadingError) {
      return {
        title: 'Deck unavailable',
        body: loadingError,
        action: (
          <button
            onClick={() => window.location.reload()}
            className="lyrio-focus rounded-xl px-4 py-2 text-sm font-semibold border lyrio-border-default"
          >
            <RefreshCw size={14} className="inline mr-2" />Retry
          </button>
        ),
        icon: <X size={18} />,
      };
    }

    return null;
  }, [loading, loadingError]);

  if (stateCard) {
    return (
      <section className="lyrio-portal-shell flex justify-center px-4 py-8">
        <div className="lyrio-card-shell max-w-md w-full rounded-2xl border p-5 animate-fade-in-soft">
          <div className="lyrio-text-primary flex items-center gap-2 mb-2">
            {stateCard.icon}
            <h3 className="lyrio-heading text-lg m-0">{stateCard.title}</h3>
          </div>
          <p className="lyrio-text-muted text-sm m-0">{stateCard.body}</p>
          {stateCard.action ? <div className="mt-4">{stateCard.action}</div> : null}
        </div>
      </section>
    );
  }

  const canSwipe = currentIndex >= 0;

  return (
    <section className="lyrio-portal-shell lyrio-shell-elevated w-full max-w-xl mx-auto rounded-[30px] border px-4 sm:px-6 py-6">
      {highIntentAlert ? (
        <div className="lyrio-high-intent mb-4 rounded-2xl px-4 py-3 animate-fade-in-soft" role="status" aria-live="polite">
          <div className="flex items-start gap-2">
            <CheckCircle2 size={18} className="lyrio-text-success" />
            <div>
              <p className="m-0 text-sm font-semibold">High intent detected</p>
              <p className="lyrio-text-muted m-0 text-xs">Your agent has been notified to follow up quickly.</p>
            </div>
          </div>
        </div>
      ) : null}

      <header className="mb-4 flex items-center justify-between gap-3">
        <div>
          <h2 className="lyrio-heading text-xl sm:text-2xl m-0">Your Daily Matches</h2>
          <p className="lyrio-text-muted m-0 text-sm">
            {reviewed} reviewed • {Math.max(total - reviewed, 0)} remaining
          </p>
        </div>
        <span className="lyrio-chip">{Math.max(currentIndex + 1, 0)} / {total}</span>
      </header>

      <div className="card-container w-full h-[620px] sm:h-[660px] relative">
        {deck.map((property, index) => (
          <TinderCard
            ref={childRefs.current[index]}
            className="absolute inset-0"
            key={property.id || property.property_id || index}
            onSwipe={(dir) => onSwipe(dir, property.id || property.property_id)}
            onCardLeftScreen={onCardLeftScreen}
            preventSwipe={['up', 'down']}
            swipeRequirementType="position"
            swipeThreshold={96}
          >
            <PropertyCard property={property} index={index + 1} total={total} />
          </TinderCard>
        ))}

        {!canSwipe ? (
          <div className="lyrio-empty-state absolute inset-0 rounded-3xl border flex items-center justify-center p-6">
            <div className="text-center">
              <h3 className="lyrio-heading text-2xl m-0">You are all caught up</h3>
              <p className="lyrio-text-muted mt-2 mb-4 text-sm">
                Fresh listings will appear automatically as the market updates.
              </p>
              <button
                className="lyrio-focus rounded-xl px-4 py-2 text-sm font-semibold border lyrio-border-default"
                onClick={() => window.location.reload()}
              >
                <RefreshCw size={14} className="inline mr-2" />Check for updates
              </button>
            </div>
          </div>
        ) : null}
      </div>

      {canSwipe ? (
        <div className="lyrio-deck-toolbar mt-4 rounded-2xl border px-4 py-3">
          <div className="flex items-center justify-between gap-3">
            <button
              onClick={() => swipe('left')}
              disabled={isProcessing}
              className="lyrio-action-btn lyrio-pass-btn portal-action-btn lyrio-focus rounded-full border inline-flex items-center justify-center"
              aria-label="Pass on this property"
            >
              <X size={24} />
            </button>

            <p className="lyrio-text-muted m-0 text-xs sm:text-sm font-semibold">
              Swipe or tap actions below
            </p>

            <button
              onClick={() => swipe('right')}
              disabled={isProcessing}
              className="lyrio-action-btn lyrio-like-btn portal-action-btn lyrio-focus rounded-full inline-flex items-center justify-center"
              aria-label="Like this property"
            >
              <Heart size={24} />
            </button>
          </div>
        </div>
      ) : null}

      <FeedbackModal
        isOpen={showFeedbackModal}
        onClose={() => {
          if (currentPassProperty) {
            handleInteraction(currentPassProperty, 'pass', null, currentPassProperty.timeOnCard);
          }
          setShowFeedbackModal(false);
          setCurrentPassProperty(null);
        }}
        onSubmit={onFeedbackSubmit}
      />
    </section>
  );
};

export default SwipeDeck;
