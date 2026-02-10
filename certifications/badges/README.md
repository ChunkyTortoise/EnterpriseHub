# Certification Badges & Logos

This directory contains official provider logos and certification badges for visual representation in the showcase.

## Provider Logos

### Required Logos (8 Providers)
1. **Google** - Google Cloud, Google Analytics, Google Digital Marketing
2. **Microsoft** - Microsoft Learn, Azure, Power BI
3. **IBM** - IBM Skills Network, IBM BI
4. **Vanderbilt University** - Vanderbilt logo
5. **DeepLearning.AI** - DeepLearning.AI logo
6. **Meta** - Meta Platforms logo
7. **Duke University** - Duke logo
8. **University of Michigan** - UMich logo

## Badge Types

### Status Badges
- ✅ **Completed** - Green checkmark badge
- 🔄 **In Progress** - Blue circular arrow badge
- 📊 **Progress Bar** - Percentage-based progress indicator

### Platform Badges
- 📜 **Coursera** - Official Coursera certificate badge
- 🎓 **Professional Certificate** - Generic professional cert badge
- 🏆 **Specialization** - Multi-course specialization badge

## Downloading Official Logos

### Google
- **Source**: [Google Brand Resources](https://about.google/brand-resources/)
- **Files**: `google-logo.png`, `google-cloud-logo.png`
- **Usage**: Follow Google brand guidelines

### Microsoft
- **Source**: [Microsoft Brand Resources](https://www.microsoft.com/en-us/legal/intellectualproperty/trademarks)
- **Files**: `microsoft-logo.png`, `azure-logo.png`, `powerbi-logo.png`
- **Usage**: Follow Microsoft brand guidelines

### IBM
- **Source**: [IBM Design Language](https://www.ibm.com/design/language/)
- **Files**: `ibm-logo.png`
- **Usage**: Follow IBM brand guidelines

### Meta
- **Source**: [Meta Brand Resources](https://about.meta.com/brand/resources/)
- **Files**: `meta-logo.png`
- **Usage**: Follow Meta brand guidelines

### Vanderbilt University
- **Source**: [Vanderbilt Brand Guidelines](https://www.vanderbilt.edu/communications/brand/)
- **Files**: `vanderbilt-logo.png`
- **Usage**: Follow Vanderbilt brand guidelines

### Duke University
- **Source**: [Duke Brand Guidelines](https://brand.duke.edu/)
- **Files**: `duke-logo.png`
- **Usage**: Follow Duke brand guidelines

### University of Michigan
- **Source**: [UMich Brand Guidelines](https://brand.umich.edu/)
- **Files**: `michigan-logo.png`
- **Usage**: Follow UMich brand guidelines

### DeepLearning.AI
- **Source**: [DeepLearning.AI Website](https://www.deeplearning.ai/)
- **Files**: `deeplearning-ai-logo.png`
- **Usage**: Educational use

## Alternative: Text-Based Logos

For initial implementation without downloading images, the Streamlit dashboard uses text-based provider badges with emoji icons:

```python
providers_emoji = {
    "Google": "🔍",
    "Microsoft": "💻",
    "IBM": "🔷",
    "Vanderbilt University": "🎓",
    "DeepLearning.AI": "🤖",
    "Meta": "👥",
    "Duke University": "🏛️",
    "University of Michigan": "🔬"
}
```

## Badge Specifications

### Image Format
- **Format**: PNG with transparency
- **Size**: 200x200px (logos), 100x100px (status badges)
- **DPI**: 300 DPI for print quality
- **Color**: Full color + grayscale versions

### File Naming Convention
```
{provider}-logo.png           # Main provider logo
{provider}-logo-gray.png      # Grayscale version
completed-badge.png           # Green checkmark
inprogress-badge.png         # Blue circular arrow
specialization-badge.png     # Multi-course badge
certificate-badge.png        # Single certificate badge
```

## Usage in Streamlit

### Current Implementation
The dashboard uses HTML/CSS badges with gradient backgrounds and emoji icons for a modern, professional look without requiring image files.

### Future Enhancement
Replace text badges with official provider logos:

```python
st.image(f"certifications/badges/{provider.lower()}-logo.png", width=50)
```

## Copyright & Attribution

All logos and badges are property of their respective organizations. Use is limited to:
- Personal portfolio showcase
- Educational purposes
- Non-commercial use
- Proper attribution to providers

Always follow official brand guidelines when using provider logos.

---

**Last Updated**: February 10, 2026
**Image Files**: To be added (placeholder directory for future enhancement)
