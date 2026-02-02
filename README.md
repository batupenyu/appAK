# AppAK - Angka Kredit Pegawai

A Django application for managing employee credit scores (Angka Kredit Pegawai).

## Local Development

To run the application locally:

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Run migrations:
```bash
python manage.py migrate
```

3. Create a superuser (optional):
```bash
python manage.py createsuperuser
```

4. Start the development server:
```bash
python manage.py runserver
```

The application will be available at `http://127.0.0.1:8000/`.

## Deployment on Vercel

This application is configured for deployment on Vercel.

### Prerequisites

- A Vercel account
- Git repository connected to Vercel
- Database (either SQLite for development or PostgreSQL for production)

### Environment Variables

Set these environment variables in your Vercel project settings:

- `DJANGO_SECRET_KEY`: A secure secret key for Django
- `DEBUG`: Set to `False` for production (default: `False`)
- `ENVIRONMENT`: Set to `production` for production deployment
- `DATABASE_URL`: PostgreSQL database URL (optional, will fallback to SQLite if not provided)
- `DB_NAME`: Database name (for Supabase/PostgreSQL)
- `DB_USER`: Database username (for Supabase/PostgreSQL)
- `DB_PASSWORD`: Database password (for Supabase/PostgreSQL)
- `DB_HOST`: Database host (for Supabase/PostgreSQL)
- `DB_PORT`: Database port (default: 5432)

### Deployment Process

1. Connect your Git repository to Vercel
2. Vercel will automatically detect this is a Python/Django project
3. The build process will:
   - Install dependencies from `requirements.txt`
   - Run database migrations
   - Collect static files
   - Deploy the application

### Notes

- The application defaults to SQLite if no PostgreSQL database is configured
- Static files are handled by Whitenoise for production deployment
- The application is configured to work with Vercel's serverless infrastructure