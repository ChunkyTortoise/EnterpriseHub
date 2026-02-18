# Portfolio Site

A professional portfolio site built with Next.js, TypeScript, and static export capability.

## Overview

This project serves as the foundation for a content-driven portfolio site featuring:
- Services showcase
- Case studies
- Proof/work samples
- Data-driven content

## Tech Stack

- **Framework**: Next.js 14 with App Router
- **Language**: TypeScript (strict mode)
- **Content**: YAML + Markdown with frontmatter
- **Validation**: JSON Schema via AJV
- **Export**: Static HTML generation

## Project Structure

```
portfolio-site/
├── content/              # Content source files
│   ├── services/         # Service definitions (YAML)
│   ├── case-studies/     # Case study content (Markdown)
│   ├── proof/            # Proof/work samples (Markdown)
│   └── data/             # Data files (YAML/JSON)
├── src/
│   ├── components/       # React components
│   ├── lib/              # Utility functions
│   └── pages/            # Next.js pages
├── public/
│   └── assets/           # Static assets (images, docs)
├── scripts/              # Build and utility scripts
├── next.config.js        # Next.js configuration
├── tsconfig.json         # TypeScript configuration
└── package.json          # Dependencies and scripts
```

## Setup

### Prerequisites

- Node.js 18.x or higher
- npm 9.x or higher

### Installation

```bash
# Install dependencies
npm install

# Run development server
npm run dev

# Build for production
npm run build

# Type checking
npm run type-check
```

## Scripts

### Development

| Command | Description |
|---------|-------------|
| `npm run dev` | Start development server |
| `npm run build` | Build for production (static export) |
| `npm run start` | Start production server |
| `npm run lint` | Run ESLint |
| `npm run type-check` | Run TypeScript type checking |

### Content Scripts

| Command | Description |
|---------|-------------|
| `npm run validate` | Validate YAML against schemas |
| `npm run build-content` | Compile YAML to JSON |
| `npm run check-links` | Verify proof asset links |
| `npm run release-manifest` | Generate release artifacts |

## Content Management

### Adding Services

1. Create a new YAML file in `content/services/`
2. Follow the service schema (TODO: document schema)
3. Run `npm run validate` to verify

### Adding Case Studies

1. Create a new Markdown file in `content/case-studies/`
2. Include required frontmatter fields
3. Run `npm run validate` to verify

### Adding Proof/Work Samples

1. Create a new Markdown file in `content/proof/`
2. Reference assets from `public/assets/`
3. Run `npm run check-links` to verify

## Master Specification

The master specification for this project is located at:
- **TODO**: Add link to master spec location

## Contributing

1. Create a feature branch
2. Make changes following the existing patterns
3. Run validation scripts before committing
4. Submit a pull request

## License

Private - All rights reserved
