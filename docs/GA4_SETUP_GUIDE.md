# Google Analytics 4 (GA4) Setup Guide

**Created**: 2026-02-15
**Repository**: chunkytortoise.github.io
**Status**: Production-ready

## Overview

Google Analytics 4 provides web analytics and insights for the portfolio site. Tracking is enabled on all 9 pages.

## Current Configuration

- **Measurement ID**: `G-QNBBCMHX7Q`
- **Property**: ChunkyTortoise Portfolio
- **Coverage**: 9/9 pages (100%)
- **Status**: Active and validated (2026-02-15)

## Pages Instrumented

1. index.html
2. about.html
3. projects.html
4. services.html
5. blog.html
6. blog/multi-agent-orchestration.html
7. benchmarks.html
8. case-studies.html
9. certifications.html

## Setup Instructions

### 1. Create GA4 Property

1. Go to https://analytics.google.com
2. Sign in with Google account (chunktort@gmail.com)
3. Admin > Create Property
4. Property name: "ChunkyTortoise Portfolio"
5. Timezone: Pacific Time (US)
6. Currency: USD

### 2. Create Data Stream

1. Property > Data Streams > Add stream
2. Platform: Web
3. Website URL: https://chunkytortoise.github.io
4. Stream name: "Portfolio Website"
5. Copy the **Measurement ID** (G-XXXXXXXXXX)

### 3. Add Tracking Code

Add this code to the `<head>` section of ALL HTML pages:

```html
<!-- Google tag (gtag.js) -->
<script async src="https://www.googletagmanager.com/gtag/js?id=G-XXXXXXXXXX"></script>
<script>
  window.dataLayer = window.dataLayer || [];
  function gtag(){dataLayer.push(arguments);}
  gtag('js', new Date());
  gtag('config', 'G-XXXXXXXXXX');
</script>
```

Replace `G-XXXXXXXXXX` with your actual Measurement ID.

### 4. Enable Enhanced Measurement

In GA4 property:
1. Admin > Data Streams > Select your stream
2. Enhanced measurement > Configure
3. Enable all options:
   - Page views (automatic)
   - Scrolls
   - Outbound clicks
   - Site search
   - Video engagement
   - File downloads

### 5. Verify Installation

1. GA4 > Reports > Realtime
2. Visit your website in incognito mode
3. Navigate through pages
4. Confirm real-time users appear in dashboard
5. Check "Event count by Event name" shows page_view events

## Validation

The tracking was validated on 2026-02-15:
- Tracking code present on 9/9 pages (100%)
- gtag.js loads successfully (HTTP 200)
- Live deployment verified

See: `docs/PORTFOLIO_VALIDATION_REPORT_2026-02-15.md`

## Key Events to Configure

### 1. Form Submissions (Formspree)
Since Formspree handles form submissions, track via custom event:

```html
<form action="..." onsubmit="gtag('event', 'form_submit', {'form_name': 'contact'});">
```

### 2. Outbound Links (GitHub, LinkedIn, etc.)
Automatically tracked if "Outbound clicks" enabled in Enhanced Measurement.

### 3. File Downloads (Resume, PDFs)
Automatically tracked if "File downloads" enabled.

### 4. Custom Events
```javascript
gtag('event', 'custom_event_name', {
  'parameter_1': 'value_1',
  'parameter_2': 'value_2'
});
```

## Reports to Monitor

### Realtime
- Active users right now
- Page views by page
- Event count by event name

### Engagement
- Pages and screens (most viewed pages)
- Events (all tracked events)
- Conversions (after setting up)

### Acquisition
- Traffic sources
- User acquisition channels

### Demographics
- User location
- Device category
- Browser

## Troubleshooting

### No Data in Reports
- Check Measurement ID is correct
- Verify tracking code in `<head>` section
- Test in incognito mode (adblockers may interfere)
- Wait 24-48 hours for non-realtime reports

### Tracking Code Not Loading
- Check browser console for errors
- Verify gtag.js URL is correct
- Test with browser dev tools > Network tab

### Multiple Measurement IDs
- Ensure only ONE tracking code per page
- Remove any old UA (Universal Analytics) code

## References

- GA4 Documentation: https://support.google.com/analytics/answer/9304153
- Property ID: `G-QNBBCMHX7Q`
- Enhanced Measurement: https://support.google.com/analytics/answer/9216061

---

**Last Updated**: 2026-02-15
**Validated**: PASS
**Coverage**: 9/9 pages (100%)
