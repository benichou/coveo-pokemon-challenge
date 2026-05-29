# Coveo Pokemon Challenge

Forward Deployed Engineer technical challenge for Coveo. A custom search experience built on top of the **Coveo Cloud Platform**, indexing [pokemondb.net](https://pokemondb.net) and surfacing it through a hosted UI.

## Status

🚧 Work in progress.

## Architecture (target)

```
   pokemondb.net + pokeapi.co
        │
        ├──► Source A: Coveo Web Crawler  (managed pull)
        │
        └──► Python ingestion ──► Source B: Push source  (custom push)
                                  │
                                  ▼
                       Coveo Cloud Org (benichou)
                       index + RGA + Query Suggest
                                  │
                                  ▼
                       Hosted Search App (Vercel)
                       Atomic main + Headless+React Detail Page
```

## Features

- ✅ Dual-source indexing (Coveo Web Crawler + custom Python Push pipeline)
- ✅ Faceted search by Pokemon Type and Generation
- ✅ Result tiles with Pokemon artwork
- ✅ RGA-powered generative answers
- ✅ Query Suggest type-ahead
- ✅ Pokemon Detail Page (Headless + React)
- ✅ Passage Retrieval API integration (Bonus)

## Live URL

_To be added once deployed._

## Repository layout

```
coveo-pokemon-challenge/
├── atomic-search/      # Main Atomic UI (Vite)
├── detail-page/        # Pokemon Detail Page (Headless + React)
├── push-pokemon/       # Python ingestion pipeline (Push API)
└── README.md
```

## Local development

_Setup instructions added as each module lands._

## License

MIT
