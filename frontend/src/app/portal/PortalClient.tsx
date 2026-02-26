'use client';

import { ArrowLeft } from 'lucide-react';
import Link from 'next/link';
import { Badge } from '../../components/ui/Badge';
import { Button } from '../../components/ui/Button';
import { TopNav } from '../../components/ui/TopNav';
import { SwipeDeck } from '../../components/portal/SwipeDeck';
import styles from './page.module.css';

const sampleProperties = [
  {
    id: 'demo-1',
    price: 769000,
    beds: 4,
    baths: 3,
    sqft: 2410,
    address: '1248 Cypress Ridge Ln',
    city: 'Rancho Cucamonga',
    state: 'CA',
    image_url: 'https://images.unsplash.com/photo-1600585154340-be6161a56a0c?auto=format&fit=crop&w=1600&q=80',
  },
  {
    id: 'demo-2',
    price: 689000,
    beds: 3,
    baths: 2,
    sqft: 1980,
    address: '8821 Amberview Dr',
    city: 'Ontario',
    state: 'CA',
    image_url: 'https://images.unsplash.com/photo-1512917774080-9991f1c4c750?auto=format&fit=crop&w=1600&q=80',
  },
  {
    id: 'demo-3',
    price: 849000,
    beds: 5,
    baths: 3,
    sqft: 2890,
    address: '4417 Alta Crest Dr',
    city: 'Rancho Cucamonga',
    state: 'CA',
    image_url: 'https://images.unsplash.com/photo-1580587771525-78b9dba3b914?auto=format&fit=crop&w=1600&q=80',
  },
  {
    id: 'demo-4',
    price: 629000,
    beds: 3,
    baths: 2,
    sqft: 1750,
    address: '7753 Etiwanda Ave',
    city: 'Rancho Cucamonga',
    state: 'CA',
    image_url: 'https://images.unsplash.com/photo-1564013799919-ab600027ffc6?auto=format&fit=crop&w=1600&q=80',
  },
  {
    id: 'demo-5',
    price: 715000,
    beds: 4,
    baths: 3,
    sqft: 2240,
    address: '2209 Vineyard Ave',
    city: 'Ontario',
    state: 'CA',
    image_url: 'https://images.unsplash.com/photo-1568605114967-8130f3a36994?auto=format&fit=crop&w=1600&q=80',
  },
  {
    id: 'demo-6',
    price: 599000,
    beds: 3,
    baths: 2,
    sqft: 1620,
    address: '9104 Baseline Rd',
    city: 'Rancho Cucamonga',
    state: 'CA',
    image_url: 'https://images.unsplash.com/photo-1605276374104-dee2a0ed3cd6?auto=format&fit=crop&w=1600&q=80',
  },
];

export default function PortalClient({
  leadId,
  contactId,
  locationId,
  apiBaseUrl = '/api',
}: {
  leadId?: string;
  contactId?: string;
  locationId?: string;
  apiBaseUrl?: string;
}) {
  const resolvedContactId = contactId || leadId;
  const properties = resolvedContactId ? [] : sampleProperties;

  return (
    <main className={styles.page}>
      <TopNav
        left={
          <div className={styles.portalNavBrand}>
            <Link href="/">
              <Button variant="ghost" icon={<ArrowLeft size={16} />}>
                Dashboard
              </Button>
            </Link>
            <div className={styles.portalBrandText}>
              <h1 className={styles.portalTitle}>Lyrio Buyer Portal</h1>
              <p className={styles.portalSubtitle}>AI-curated property matches</p>
            </div>
          </div>
        }
        right={<Badge variant="primary">AI-Matched</Badge>}
      />
      <div className={styles.container}>
        <SwipeDeck
          properties={properties}
          leadId={leadId}
          contactId={contactId}
          locationId={locationId}
          apiBaseUrl={apiBaseUrl}
        />
      </div>
    </main>
  );
}
