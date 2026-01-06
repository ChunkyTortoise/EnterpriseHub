"""
Smart Document Generator Demo - Agent 4: Automation Genius
Demo page for automated contract and document generation
"""

import streamlit as st
import sys
from pathlib import Path
from datetime import datetime
import pandas as pd

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from services.smart_document_generator import (
    SmartDocumentGenerator,
    DocumentType,
    DocumentStatus,
    SignatureProvider
)

# Page config
st.set_page_config(
    page_title="Smart Document Generator",
    page_icon="📄",
    layout="wide"
)

# Initialize service
if 'doc_service' not in st.session_state:
    st.session_state.doc_service = SmartDocumentGenerator()
if 'documents' not in st.session_state:
    st.session_state.documents = {}
if 'signature_requests' not in st.session_state:
    st.session_state.signature_requests = {}

# Header
st.title("📄 Smart Document Generator")
st.markdown("### Automated contract generation with e-signature integration")

# Metrics
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("Time Saved", "3-4 hrs/deal")
with col2:
    st.metric("Documents Created", len(st.session_state.documents))
with col3:
    st.metric("Revenue Impact", "+$20K-30K/yr")
with col4:
    st.metric("Completion Rate", "95%")

st.divider()

# Tabs
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📝 Generate Document",
    "📋 Disclosure Packets",
    "✍️ E-Signatures",
    "📚 Templates",
    "📊 Document History"
])

with tab1:
    st.subheader("Generate Document from Template")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**Document Type**")
        doc_type = st.selectbox(
            "Select Document Type",
            options=[d.value for d in DocumentType],
            format_func=lambda x: x.replace('_', ' ').title()
        )
        
        template_id = st.selectbox(
            "Template",
            [f"template_{doc_type}_standard", f"template_{doc_type}_premium", f"template_{doc_type}_custom"]
        )
        
        jurisdiction = st.selectbox(
            "Jurisdiction",
            ["TX", "CA", "FL", "NY", "Other"],
            help="State-specific legal requirements will be applied"
        )
    
    with col2:
        st.markdown("**Property Details**")
        property_address = st.text_input("Property Address", "123 Main St, Austin, TX 78701")
        purchase_price = st.number_input("Purchase/Sale Price", min_value=0, value=450000, step=5000)
        
        st.markdown("**Party Information**")
        buyer_name = st.text_input("Buyer Name", "John Doe")
        seller_name = st.text_input("Seller Name", "Jane Smith")
    
    st.divider()
    
    st.markdown("**Additional Details**")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        closing_date = st.date_input("Closing Date")
        earnest_money = st.number_input("Earnest Money", min_value=0, value=5000, step=500)
    
    with col2:
        inspection_period = st.number_input("Inspection Period (days)", min_value=0, value=10)
        option_fee = st.number_input("Option Fee", min_value=0, value=500, step=100)
    
    with col3:
        financing = st.selectbox("Financing", ["Cash", "Conventional", "FHA", "VA", "Other"])
        title_company = st.text_input("Title Company", "Austin Title Co.")
    
    # Advanced options
    with st.expander("⚙️ Advanced Options"):
        auto_populate = st.checkbox("Auto-populate common fields", value=True)
        apply_compliance = st.checkbox("Apply jurisdiction legal requirements", value=True)
        include_addendums = st.multiselect(
            "Include Standard Addendums",
            ["HOA Addendum", "Survey", "Lead-Based Paint", "Seller's Disclosure"],
            default=["Lead-Based Paint"]
        )
    
    col1, col2, col3 = st.columns(3)
    with col2:
        if st.button("📄 Generate Document", type="primary", use_container_width=True):
            with st.spinner("Generating document..."):
                # Prepare data
                document_data = {
                    "property_address": property_address,
                    "purchase_price": purchase_price,
                    "buyer_name": buyer_name,
                    "seller_name": seller_name,
                    "closing_date": closing_date.isoformat(),
                    "earnest_money": earnest_money,
                    "inspection_period": inspection_period,
                    "option_fee": option_fee,
                    "financing": financing,
                    "title_company": title_company,
                    "jurisdiction": jurisdiction,
                    "created_by": "Jorge Salas"
                }
                
                # Generate document
                document = st.session_state.doc_service.generate_document(
                    document_type=DocumentType[doc_type.upper()],
                    template_id=template_id,
                    data=document_data
                )
                
                st.session_state.documents[document['id']] = document
                
                st.success(f"✅ Document generated: {document['id']}")
                
                # Show preview
                st.markdown("**Document Preview:**")
                st.info(f"""
                **{doc_type.replace('_', ' ').title()}**
                
                Property: {property_address}
                Price: ${purchase_price:,}
                Buyer: {buyer_name}
                Seller: {seller_name}
                Closing: {closing_date}
                
                Status: {document['status']}
                Version: {document['versions'][0]['version']}
                """)
                
                st.balloons()

with tab2:
    st.subheader("Generate Disclosure Packet")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**Property Information**")
        packet_address = st.text_input("Address", "456 Oak Ave, Austin, TX 78701", key="packet_addr")
        packet_jurisdiction = st.selectbox("State", ["TX", "CA", "FL", "NY"], key="packet_juris")
        year_built = st.number_input("Year Built", min_value=1800, max_value=2026, value=2015)
        
        st.markdown("**Property Characteristics**")
        has_pool = st.checkbox("Has Pool")
        has_septic = st.checkbox("Has Septic System")
        in_hoa = st.checkbox("In HOA")
        in_flood_zone = st.checkbox("In Flood Zone")
    
    with col2:
        st.markdown("**Required Disclosures Preview**")
        
        required_docs = {
            "TX": ["Lead-Based Paint", "Seller's Disclosure", "Addendum for Residential"],
            "CA": ["Lead-Based Paint", "Natural Hazards", "Mello-Roos", "Earthquake"],
            "FL": ["Lead-Based Paint", "Property Condition", "Radon"],
            "NY": ["Lead-Based Paint", "Property Condition", "Disclosure Statement"]
        }
        
        docs_list = required_docs.get(packet_jurisdiction, ["Lead-Based Paint"])
        
        st.info(f"**{len(docs_list)} Required Documents:**")
        for doc in docs_list:
            st.write(f"✅ {doc}")
        
        if has_pool:
            st.write(f"➕ Pool Safety Disclosure")
        if in_hoa:
            st.write(f"➕ HOA Documents")
    
    col1, col2, col3 = st.columns(3)
    with col2:
        if st.button("📋 Generate Complete Packet", type="primary", use_container_width=True):
            with st.spinner("Generating disclosure packet..."):
                property_data = {
                    "address": packet_address,
                    "jurisdiction": packet_jurisdiction,
                    "year_built": year_built,
                    "has_pool": has_pool,
                    "has_septic": has_septic,
                    "in_hoa": in_hoa,
                    "in_flood_zone": in_flood_zone
                }
                
                packet = st.session_state.doc_service.generate_disclosure_packet(
                    property_data,
                    packet_jurisdiction
                )
                
                st.success(f"✅ Disclosure packet generated with {len(packet['documents'])} documents!")
                
                # Show packet details
                st.markdown("**Packet Contents:**")
                for doc in packet['documents']:
                    required_badge = "🔴 Required" if doc['required'] else "⚪ Optional"
                    st.write(f"{required_badge} {doc['type'].replace('_', ' ').title()} - {doc['status']}")

with tab3:
    st.subheader("Send Documents for E-Signature")
    
    if not st.session_state.documents:
        st.warning("⚠️ Generate a document first to send for signature")
    else:
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**Select Document**")
            
            doc_options = {
                f"{doc['type']} - {doc['id'][:8]}": doc_id 
                for doc_id, doc in st.session_state.documents.items()
            }
            
            selected_doc_name = st.selectbox("Document", options=list(doc_options.keys()))
            selected_doc_id = doc_options[selected_doc_name]
            selected_doc = st.session_state.documents[selected_doc_id]
            
            st.info(f"**Document Details:**\n- Type: {selected_doc['type']}\n- Status: {selected_doc['status']}")
            
            provider = st.selectbox(
                "E-Signature Provider",
                options=[p.value for p in SignatureProvider],
                format_func=lambda x: x.replace('_', ' ').title()
            )
        
        with col2:
            st.markdown("**Signing Options**")
            signing_order = st.radio("Signing Order", ["Sequential", "Parallel"])
            send_reminders = st.checkbox("Send Automatic Reminders", value=True)
            expiration_days = st.number_input("Expiration (days)", min_value=1, max_value=90, value=30)
        
        st.divider()
        
        st.markdown("**Add Signers**")
        
        num_signers = st.number_input("Number of Signers", min_value=1, max_value=10, value=3)
        
        signers = []
        for i in range(num_signers):
            col1, col2, col3 = st.columns([2, 2, 1])
            
            with col1:
                name = st.text_input(f"Signer {i+1} Name", f"Signer {i+1}", key=f"signer_name_{i}")
            with col2:
                email = st.text_input(f"Email", f"signer{i+1}@example.com", key=f"signer_email_{i}")
            with col3:
                role = st.selectbox(f"Role", ["Buyer", "Seller", "Agent", "Attorney"], key=f"signer_role_{i}")
            
            signers.append({"name": name, "email": email, "role": role.lower()})
        
        col1, col2, col3 = st.columns(3)
        with col2:
            if st.button("✍️ Send for Signature", type="primary", use_container_width=True):
                with st.spinner("Sending for signature..."):
                    sig_request = st.session_state.doc_service.send_for_signature(
                        document_id=selected_doc_id,
                        signers=signers,
                        provider=SignatureProvider[provider.upper()],
                        options={
                            "signing_order": signing_order.lower(),
                            "send_reminders": send_reminders,
                            "expiration_days": expiration_days
                        }
                    )
                    
                    st.session_state.signature_requests[sig_request['id']] = sig_request
                    
                    st.success(f"✅ Sent to {len(signers)} signers via {provider}!")
                    
                    # Show signing URLs
                    st.markdown("**Signing URLs:**")
                    for email, url in sig_request['signature_urls'].items():
                        st.code(f"{email}: {url}")
    
    # Track signature status
    if st.session_state.signature_requests:
        st.divider()
        st.markdown("**Active Signature Requests**")
        
        for sig_id, sig_req in st.session_state.signature_requests.items():
            with st.expander(f"📝 Document: {sig_req['document_id'][:8]}... - {sig_req['status'].upper()}"):
                status = st.session_state.doc_service.check_signature_status(sig_id)
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Signed", status['completion']['signed'])
                with col2:
                    st.metric("Pending", status['completion']['pending'])
                with col3:
                    st.metric("Progress", f"{status['completion']['percentage']:.0%}")
                
                st.markdown("**Signer Status:**")
                for signer in status['signers']:
                    status_icon = "✅" if signer['status'] == 'signed' else "⏳"
                    st.write(f"{status_icon} {signer['email']}: {signer['status']}")

with tab4:
    st.subheader("Document Templates")
    
    st.markdown("**Create New Template**")
    
    col1, col2 = st.columns(2)
    
    with col1:
        template_name = st.text_input("Template Name", "My Custom Purchase Agreement")
        template_type = st.selectbox(
            "Document Type",
            options=[d.value for d in DocumentType],
            format_func=lambda x: x.replace('_', ' ').title(),
            key="template_type"
        )
        template_jurisdiction = st.selectbox("Jurisdiction (optional)", ["None", "TX", "CA", "FL", "NY"])
    
    with col2:
        st.markdown("**Template Fields**")
        st.info("""
        Use merge fields in your template:
        - {{property_address}}
        - {{purchase_price}}
        - {{buyer_name}}
        - {{seller_name}}
        - {{closing_date}}
        - {{agent_name}}
        """)
    
    template_content = st.text_area(
        "Template Content",
        value="""PURCHASE AGREEMENT

Property Address: {{property_address}}
Purchase Price: ${{purchase_price}}

Buyer: {{buyer_name}}
Seller: {{seller_name}}

Closing Date: {{closing_date}}

Agent: {{agent_name}}
""",
        height=300
    )
    
    if st.button("💾 Save Template"):
        st.success("✅ Template saved!")
    
    st.divider()
    
    st.markdown("**Available Templates**")
    
    templates = [
        {"name": "Standard Purchase Agreement - TX", "type": "purchase_agreement", "uses": 45},
        {"name": "Listing Agreement - Standard", "type": "listing_agreement", "uses": 32},
        {"name": "Buyer Representation Agreement", "type": "buyer_representation", "uses": 28},
        {"name": "Lease Agreement - Residential", "type": "lease_agreement", "uses": 19},
    ]
    
    for template in templates:
        col1, col2, col3, col4 = st.columns([3, 1, 1, 1])
        with col1:
            st.write(template['name'])
        with col2:
            st.write(f"📄 {template['type']}")
        with col3:
            st.write(f"🔢 {template['uses']} uses")
        with col4:
            st.button("Use", key=f"use_{template['name']}")

with tab5:
    st.subheader("Document History & Audit Trail")
    
    if not st.session_state.documents:
        st.info("👆 Generate documents to see history")
    else:
        doc_options = {
            f"{doc['type']} - {doc['id'][:8]}": doc_id 
            for doc_id, doc in st.session_state.documents.items()
        }
        
        selected_doc_name = st.selectbox(
            "Select Document",
            options=list(doc_options.keys()),
            key="history_doc"
        )
        selected_doc_id = doc_options[selected_doc_name]
        
        # Get history
        history = st.session_state.doc_service.get_document_history(selected_doc_id)
        
        # Document info
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Versions", len(history['versions']))
        with col2:
            st.metric("Access Count", len(history['access_log']))
        with col3:
            st.metric("Modifications", len(history['modifications']))
        
        st.divider()
        
        # Version history
        st.markdown("**📜 Version History**")
        for version in history['versions']:
            st.write(f"**Version {version['version']}** - {version['created_at'][:10]}")
            st.write(f"  Changes: {version['changes']}")
            st.write(f"  By: {version.get('created_by', 'system')}")
        
        st.divider()
        
        # Signature events
        if history['signature_events']:
            st.markdown("**✍️ Signature Events**")
            for event in history['signature_events']:
                st.write(f"- {event}")
        
        # Actions
        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button("📥 Download PDF"):
                st.success("Downloaded!")
        with col2:
            if st.button("📧 Email Copy"):
                st.success("Email sent!")
        with col3:
            if st.button("🗑️ Void Document", type="secondary"):
                reason = st.text_input("Reason for voiding")
                if reason:
                    result = st.session_state.doc_service.void_document(selected_doc_id, reason)
                    st.warning(f"Document voided: {reason}")

# Footer
st.divider()
st.markdown("""
**💡 Pro Tips:**
- Use templates to save time and ensure consistency
- Always apply jurisdiction-specific requirements
- Track signature status regularly
- Keep audit trails for compliance
- Integrate with your CRM for automation
""")
