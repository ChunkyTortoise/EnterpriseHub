# Stream B: Lead Bot PDF Enhancement
**Chat Purpose**: Complete Lead Bot day 14 email with CMA PDF attachment  
**Duration**: 1-2 hours  
**Priority**: HIGH  
**Status**: Ready to begin

---

## Your Mission

Complete the TODO at line 1717 of the Lead Bot: attach CMA PDF to the day 14 email. This is a high-impact user experience improvement - the CMA will now be delivered as a professional PDF instead of just text.

**Files You'll Work With**:
- `ghl_real_estate_ai/agents/lead_bot.py` (Line 1717 - main work)
- `ghl_real_estate_ai/services/cma_generator.py` (Already exists - use it)
- `ghl_real_estate_ai/services/email_service.py` (May need enhancement)
- `tests/agents/test_lead_bot.py` (Add 1-2 test cases)

---

## The TODO

**Location**: `lead_bot.py` line 1717  
**Current State**:
```python
async def send_day_14_email(lead_id: str, property_address: str):
    # Generate CMA
    cma_data = await self.cma_generator.generate_cma(property_address)
    
    # TODO: "Generate and attach CMA PDF"
    # Currently: CMA sent as text in email body
    # Target: CMA sent as professional PDF attachment
```

**What Needs to Happen**:
1. Generate CMA analysis (already working ✅)
2. **NEW**: Convert CMA to PDF format
3. **NEW**: Attach PDF to GHL email message
4. **NEW**: Validate delivery with attachment
5. **NEW**: Test PDF attachment + email delivery

---

## Implementation Details

### Step 1: PDF Generation Service

**Check if it exists**:
```bash
grep -r "pdf_generator\|PDFGenerator" ghl_real_estate_ai/services/
```

**If it doesn't exist, create it**:
```python
# File: ghl_real_estate_ai/services/pdf_generator.py
# Purpose: Convert CMA data to PDF

class PDFGenerator:
    async def generate_cma_pdf(self, cma_data: Dict) -> bytes:
        """
        Convert CMA data to professional PDF
        
        Args:
            cma_data: {
                "property_address": "123 Main St, RC, CA",
                "market_analysis": {...},
                "comparable_properties": [...],
                "price_recommendation": {...}
            }
        
        Returns:
            PDF bytes (binary)
        
        Performance: <200ms
        """
        # Use reportlab or weasyprint library
        # Layout:
        # - Header: Property address + date
        # - Section 1: Market Analysis summary
        # - Section 2: Comparable properties table
        # - Section 3: Price recommendation
        # - Footer: "Prepared by Jorge Real Estate" + watermark
        
        # Return PDF as bytes
        return pdf_bytes
```

### Step 2: Email with Attachment

**Target Email Format**:
```python
# Current (text only)
email_body = f"""
Hi {lead_name},

Your Comparative Market Analysis for {property_address}:

{cma_data['market_analysis']}
{cma_data['comparable_properties']}
{cma_data['price_recommendation']}

Best regards,
Jorge
"""

# NEW (with attachment)
email = EmailMessage(
    to=lead.email,
    subject="Your Comparative Market Analysis for {property_address}",
    body="See attached CMA PDF for detailed market analysis",
    html_body=render_day_14_email_template(),
    attachments=[
        Attachment(
            filename=f"CMA_{sanitize_filename(property_address)}_{date.today()}.pdf",
            content=pdf_bytes,
            mime_type="application/pdf",
            size_bytes=len(pdf_bytes)
        )
    ]
)

# Send via GHL
await ghl_client.send_email(email)
```

### Step 3: Email Template Enhancement

**Current Template** (`templates/emails/day_14_email.html`):
```html
<h1>Market Analysis: {{property_address}}</h1>
<p>Hi {{lead_name}},</p>
<p>We've analyzed the Rancho Cucamonga market for {{property_address}}...</p>
<!-- Static text version of CMA -->
```

**Enhanced Template**:
```html
<h1>Market Analysis: {{property_address}}</h1>
<p>Hi {{lead_name}},</p>
<p>We've completed your Comparative Market Analysis (CMA) for {{property_address}}.</p>
<p><strong>See attached PDF for detailed analysis including:</strong></p>
<ul>
    <li>Market conditions & trends</li>
    <li>Comparable properties analysis</li>
    <li>Price recommendations</li>
    <li>Market opportunity assessment</li>
</ul>
<p>Questions? Reply to this email or call our team directly.</p>
<p>Best regards,<br/>Jorge Real Estate</p>
```

---

## Implementation Plan

### Phase 1: Setup (15 minutes)
1. Check if `pdf_generator.py` exists in services/
2. If not, create it with basic PDF generation
3. Add PDF generator to dependency injection

### Phase 2: Implement PDF Attachment (45 minutes)
1. Enhance `send_day_14_email()` method:
   ```python
   async def send_day_14_email(lead_id: str, property_address: str) -> Dict:
       # 1. Generate CMA data
       cma_data = await self.cma_generator.generate_cma(property_address)
       
       # 2. Convert to PDF (NEW)
       pdf_bytes = await self.pdf_generator.generate_cma_pdf(cma_data)
       
       # 3. Create email with attachment (NEW)
       email = EmailMessage(
           to=lead.email,
           subject=f"Your Comparative Market Analysis for {property_address}",
           body=self._render_day_14_email(lead, cma_data),
           attachments=[
               Attachment(
                   filename=f"CMA_{self._sanitize_filename(property_address)}_{date.today()}.pdf",
                   content=pdf_bytes,
                   mime_type="application/pdf"
               )
           ]
       )
       
       # 4. Send via GHL
       result = await self.ghl_client.send_email(email)
       
       # 5. Log + return
       logger.info(f"Day 14 email sent with PDF for lead {lead_id}")
       return result
   ```

2. Verify email service supports attachments
3. Add error handling for PDF generation failure
4. Fallback: If PDF fails, send email without attachment

### Phase 3: Testing (30 minutes)
1. Write test: PDF generates <200ms
2. Write test: Email sends with attachment
3. Write test: Attachment is valid PDF (can open)
4. Integration test: Full day 14 flow with PDF
5. Run all tests: `pytest tests/agents/test_lead_bot.py -v`

### Phase 4: Validation (15 minutes)
1. Verify no regression: All 9 existing lead bot tests passing
2. Performance test: Day 14 email <500ms total
3. Manual test: Open PDF in email client
4. GHL validation: Verify attachment appears in CRM

---

## Technical Specifications

### PDF Generation Performance
- **Target**: <200ms for PDF generation
- **Size limit**: <2MB per PDF
- **Format**: Standard PDF (viewable in all clients)
- **Content**: Professional, branded layout

### Email Attachment Specifications
- **Filename format**: `CMA_123_Main_St_2026-02-02.pdf`
- **MIME type**: `application/pdf`
- **Content-Disposition**: `attachment`
- **Size**: <2MB
- **Delivery**: Via GHL Email API

### Fallback Strategy
```
PRIMARY: Send email with PDF attachment
  ↓ (if PDF generation fails)
FALLBACK 1: Send email with CMA as text
  ↓ (if email fails)
FALLBACK 2: Queue for retry + notify support
```

---

## Key Libraries

### PDF Generation Options
1. **ReportLab** (recommended)
   - Pure Python, lightweight
   - Good for structured data
   - <100ms generation time
   - Already in requirements? Check:
     ```bash
     grep -i "reportlab\|weasyprint\|fpdf" requirements.txt
     ```

2. **WeasyPrint**
   - HTML → PDF
   - Beautiful layouts
   - Slower (100-200ms)

3. **fpdf2**
   - Lightweight
   - Simple API
   - Good for basic layouts

### Choice
Use **ReportLab** if available (check requirements.txt), otherwise add it.

---

## Test Cases to Write

```python
# Add to tests/agents/test_lead_bot.py

async def test_send_day_14_email_generates_pdf():
    """Verify PDF is generated for CMA data"""
    lead_bot = create_test_lead_bot()
    result = await lead_bot.send_day_14_email(
        lead_id="test-lead-123",
        property_address="123 Main St, Rancho Cucamonga, CA 91730"
    )
    assert result['success'] == True
    assert result['has_attachment'] == True
    assert result['attachment_type'] == 'application/pdf'

async def test_day_14_email_pdf_is_valid():
    """Verify generated PDF is valid and readable"""
    lead_bot = create_test_lead_bot()
    email_result = await lead_bot.send_day_14_email(...)
    
    # Verify PDF is valid
    from PyPDF2 import PdfReader
    pdf = PdfReader(io.BytesIO(email_result['pdf_bytes']))
    assert len(pdf.pages) >= 1
    assert "Market Analysis" in pdf.pages[0].extract_text()

async def test_day_14_email_performance():
    """Verify day 14 email generation is <500ms"""
    lead_bot = create_test_lead_bot()
    start = time.time()
    await lead_bot.send_day_14_email(...)
    duration = time.time() - start
    assert duration < 0.5  # 500ms

async def test_day_14_email_with_attachment_via_ghl():
    """Verify email actually sends via GHL with attachment"""
    mock_ghl = MockGHLClient()
    lead_bot = create_test_lead_bot(ghl_client=mock_ghl)
    
    await lead_bot.send_day_14_email(...)
    
    # Verify GHL received email with attachment
    assert mock_ghl.send_email.called
    email = mock_ghl.send_email.call_args[0][0]
    assert len(email.attachments) == 1
    assert email.attachments[0].filename.endswith('.pdf')

async def test_day_14_email_fallback_if_pdf_fails():
    """Verify email still sends if PDF generation fails"""
    lead_bot = create_test_lead_bot()
    # Mock PDF generator to fail
    lead_bot.pdf_generator.generate_cma_pdf = Mock(side_effect=Exception("PDF fail"))
    
    result = await lead_bot.send_day_14_email(...)
    
    # Should still send email (without attachment)
    assert result['success'] == True
    assert result['has_attachment'] == False
```

---

## Performance Targets

| Operation | Target | Notes |
|-----------|--------|-------|
| CMA generation | <100ms | Existing (verify) |
| PDF generation | <200ms | NEW |
| Email send | <200ms | Existing (GHL API) |
| **Total day 14 flow** | **<500ms** | Maintained |

---

## Success Criteria Checklist

- [ ] PDF generator implemented/configured
- [ ] Day 14 email includes PDF attachment
- [ ] Email template enhanced for PDF delivery
- [ ] PDF generation <200ms (verified)
- [ ] Email with attachment sends successfully via GHL
- [ ] All 9 existing lead bot tests still passing (no regression)
- [ ] 3+ new tests passing (PDF generation, attachment, performance)
- [ ] Manual verification: PDF opens in email client
- [ ] Code review approved
- [ ] No performance degradation (<500ms total)

---

## Files Reference

### Main Implementation
- `ghl_real_estate_ai/agents/lead_bot.py` (line 1717)
  - Method: `send_day_14_email()`
  - Read lines 1700-1750 for full context

### Services to Use
- `ghl_real_estate_ai/services/cma_generator.py` (already generates CMA)
- `ghl_real_estate_ai/services/pdf_generator.py` (create if needed)
- `ghl_real_estate_ai/services/enhanced_ghl_client.py` (email sending)

### Templates
- `ghl_real_estate_ai/templates/emails/day_14_email.html` (enhance)

### Tests
- `tests/agents/test_lead_bot.py` (add 3+ test cases)

### Models
- Check if `Attachment` model exists in `models/`
- If not, create it in `models/email.py`

---

## Commands to Run

```bash
# Check if PDF library is available
grep -i "reportlab\|weasyprint\|fpdf" requirements.txt

# Find the send_day_14_email method
grep -n "send_day_14_email" ghl_real_estate_ai/agents/lead_bot.py

# Find existing email attachment handling
grep -rn "Attachment\|attachment" ghl_real_estate_ai/services/

# Run lead bot tests
pytest tests/agents/test_lead_bot.py -v

# Run with performance timing
pytest tests/agents/test_lead_bot.py -v -s

# Check test coverage
pytest tests/agents/test_lead_bot.py --cov=ghl_real_estate_ai.agents.lead_bot
```

---

## Gotchas to Watch For

1. **PDF Library Not in Requirements**
   - Action: Add `reportlab` to requirements.txt + pip install

2. **Email Service Doesn't Support Attachments**
   - Action: Check `enhanced_ghl_client.py` for attachment support
   - If not: Enhance the email sending method to support attachments

3. **Large PDF Size**
   - Action: Implement compression or smaller layout
   - Target: <2MB per file

4. **GHL API Doesn't Accept PDF Attachments**
   - Action: Check GHL documentation
   - Fallback: Store PDF in S3 + send link instead

5. **Email Character Encoding**
   - Action: Ensure UTF-8 encoding for PDF metadata
   - Test: Various email clients

---

## Reference: Similar Implementation in Codebase

**Look at how other services handle file attachments**:
```bash
grep -rn "attachment\|file.*send\|binary.*email" ghl_real_estate_ai/services/
```

If no existing attachment handling, use as reference:
```python
class Attachment:
    filename: str
    content: bytes  # PDF binary
    mime_type: str = "application/pdf"
    size_bytes: int = 0

class EmailMessage:
    to: str
    subject: str
    body: str
    html_body: Optional[str] = None
    attachments: List[Attachment] = []
```

---

## Questions to Consider

1. Should PDF include broker contact info or just analysis?
2. What should PDF filename be? (Property address + date?)
3. Should there be fallback if PDF generation fails?
4. How long to cache generated PDFs?
5. Should PDF be sent to seller too, or lead only?

---

**Ready to start? Check if PDF library exists, then implement the enhancement!**

**Estimated completion**: 1-2 hours  
**Due by**: End of today  
**Can run in parallel with Stream A**
