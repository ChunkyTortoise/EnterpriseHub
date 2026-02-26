import PortalClient from './PortalClient';

export default async function PortalPage({
  searchParams,
}: {
  searchParams: Promise<{
    lead_id?: string;
    contact_id?: string;
    location_id?: string;
    api_base?: string;
  }>;
}) {
  const params = await searchParams;

  return (
    <PortalClient
      leadId={params.lead_id}
      contactId={params.contact_id}
      locationId={params.location_id}
      apiBaseUrl={params.api_base || '/api'}
    />
  );
}
