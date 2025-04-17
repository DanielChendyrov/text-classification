# Environment Configuration (.env)

To run this project, you need to create a `.env` file in the `backend_analysis` directory. This file stores sensitive configuration such as API keys and database connection strings.

## Steps to Create `.env`

1. In the `backend_analysis` folder, create a file named `.env`.
2. Add the following content to the file (replace values as needed):

```md
# API Key của DeepSeek
DEEPSEEK_API=your_deepseek_api_key_here

# Postgres DB Url
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/newspaper_crawler
```

- Replace `your_deepseek_api_key_here` with your actual DeepSeek API key.
- Uncomment and edit the `DATABASE_URL` line as needed for your database setup.

## Example

```md
DEEPSEEK_API=sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/newspaper_crawler
```

Keep your `.env` file private and do not commit it to version control.
