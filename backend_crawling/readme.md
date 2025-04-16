# Newspaper URL Crawler

A web crawling application that scrapes newspaper websites for article URLs and stores them in a PostgreSQL database.

## Requirements

- Python 3.13.1
- Docker and Docker Compose

## Project Setup

### Create Virtual Environment

```bash
python -m venv .venv
```

### Activate Virtual Environment

```bash
# For Windows
.\.venv\Scripts\activate

# For Linux/Mac
source .venv/bin/activate
```

### Install Dependencies

```bash
pip install -r requirements.txt
```

### Start PostgreSQL Database with Docker

```bash
docker-compose up -d
```

## Configuration

The websites to crawl are configured in `config/websites.json`. You can update this file while the application is running to add, remove, or enable/disable websites.

Example configuration:

```json
{
  "websites": [
    {
      "name": "Dan Tri",
      "base_url": "https://dantri.com.vn/",
      "active": true
    },
    {
      "name": "VnExpress",
      "base_url": "https://vnexpress.net/",
      "active": true
    }
  ],
  "crawl_interval_minutes": 30
}
```

## Database Structure

The crawled article URLs are stored in a PostgreSQL database with the following schema:

- `id`: Integer (primary key)
- `url`: String (the crawled URL)
- `contents`: String (empty by default)
- `analysis`: String (empty by default)
- `crawled_at`: DateTime
- `is_analyzed`: Boolean (false by default)
- `analyzed_at`: DateTime (null by default)

## Running the Application

```bash
# Make sure PostgreSQL is running
docker-compose up -d

# Start the web crawler application
python main.py
```

The application will run continuously and crawl the configured websites at the specified interval (default: 30 minutes).

## API Endpoints

- `GET /`: Check if the API is running
- `GET /api/status`: Get the current crawling status
- `POST /api/crawl`: Manually trigger the crawling process

## Monitoring

You can access the API documentation and try out the endpoints at:

```
http://localhost:8000/docs
```
