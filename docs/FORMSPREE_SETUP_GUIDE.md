# Formspree Email Form Setup Guide

**Created**: 2026-02-15
**Repository**: chunkytortoise.github.io
**Status**: Production-ready

## Overview

Formspree provides email form handling for static sites without backend code. The portfolio site uses Formspree to capture contact form submissions.

## Current Configuration

- **Form ID**: `mqedpwlp`
- **Form URL**: https://formspree.io/f/mqedpwlp
- **Live Site**: https://chunkytortoise.github.io/
- **Status**: Active and validated (2026-02-15)

## Setup Instructions

### 1. Create Formspree Account

1. Go to https://formspree.io
2. Sign up with email: chunktort@gmail.com
3. Verify email address

### 2. Create New Form

1. Dashboard > Create New Form
2. Form name: "Portfolio Contact Form"
3. Email notifications: Configure where submissions should be sent
4. Copy the form ID (format: `abc123xyz`)

### 3. Add to HTML

In your `index.html` file:

```html
<form action="https://formspree.io/f/YOUR_FORM_ID" method="POST">
  <input type="text" name="name" placeholder="Your name" required>
  <input type="email" name="email" placeholder="Your email" required>
  <textarea name="message" placeholder="Your message" required></textarea>
  <button type="submit">Send</button>
</form>
```

Replace `YOUR_FORM_ID` with your actual form ID.

### 4. Test Form

1. Open your site locally or on GitHub Pages
2. Fill out the form with test data
3. Submit
4. Check Formspree dashboard for submission
5. Verify email notification received

## Validation

The form was validated on 2026-02-15:
- Form submits successfully (HTTP 200)
- Formspree API returns `{"ok": true}`
- Live deployment working

See: `docs/PORTFOLIO_VALIDATION_REPORT_2026-02-15.md`

## Configuration Options

### Email Notifications
- Formspree dashboard > Form settings > Email notifications
- Configure recipient emails
- Customize notification templates

### Spam Protection
- Enable reCAPTCHA in form settings
- Set submission rate limits
- Configure AJAX submissions for better UX

### Custom Success Page
```html
<form action="https://formspree.io/f/mqedpwlp" method="POST">
  <input type="hidden" name="_next" value="https://yoursite.com/thanks">
  <!-- rest of form -->
</form>
```

## Troubleshooting

### Form Not Submitting
- Check form action URL has correct form ID
- Verify form method is POST
- Check browser console for errors
- Test in incognito mode (clear cache)

### Not Receiving Emails
- Check Formspree dashboard for submissions
- Verify email notification settings
- Check spam folder
- Confirm email address is verified

### 401 Unauthorized
- Form ID may be incorrect
- Form may have been deleted
- Try creating new form

## References

- Formspree Documentation: https://help.formspree.io/
- Current form: https://formspree.io/forms/mqedpwlp/submissions

---

**Last Updated**: 2026-02-15
**Validated**: PASS
