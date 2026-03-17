# Content Freshness Dashboard

A Streamlit dashboard to visualize content freshness across a Contentstack stack.

## Features

- **Freshness Metrics**: Track content as Fresh (<30 days), Aging (30-90 days), or Stale (90+ days)
- **Interactive Filters**: Filter by time period, content type, environment, locale, publish state, tags, and taxonomies
- **Visualizations**: Pie chart, stacked bar chart by content type, and sortable data table
- **CSV Export**: Download filtered results as CSV

## Setup

1. Clone this repository
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Copy `.env.example` to `.env` and add your Contentstack credentials:
   ```bash
   cp .env.example .env
   ```
4. Edit `.env` with your credentials:
   ```
   CONTENTSTACK_API_KEY=your_api_key
   CONTENTSTACK_MANAGEMENT_TOKEN=your_management_token
   CONTENTSTACK_BASE_URL=https://api.contentstack.io
   ```

## Running the Dashboard

```bash
streamlit run app.py
```

The dashboard will open at `http://localhost:8501`

## Project Structure

```
├── .env.example          # Template for environment variables
├── .gitignore            # Git ignore file
├── requirements.txt      # Python dependencies
├── app.py                # Main Streamlit dashboard
├── contentstack_client.py # Contentstack API wrapper
├── utils.py              # Helper functions
└── README.md             # This file
```

## Requirements

- Python 3.8+
- Contentstack Management Token with read access

## Screenshots

### Dashboard Overview
The dashboard shows a summary of content freshness with interactive charts.

### Filters
Use the sidebar to filter content by various criteria.

## License

MIT
