# Supabase Setup Instructions

This project has been configured to use Supabase as the database instead of SQLite. Follow these steps to configure your Supabase connection:

## Prerequisites

1. Create a Supabase account at [supabase.io](https://supabase.io)
2. Create a new project in your Supabase dashboard
3. Get your database connection details from the project settings

## Environment Variables

Copy the `.env.example` file to `.env` and fill in your Supabase credentials:

```bash
# Supabase Database Configuration
DB_NAME=postgres
DB_USER=your_supabase_username
DB_PASSWORD=your_supabase_password
DB_HOST=your-project-id.supabase.co
DB_PORT=5432

# Django Secret Key (for production)
DJANGO_SECRET_KEY=your_django_secret_key
```

### How to Get Your Supabase Credentials

1. Go to your [Supabase Dashboard](https://app.supabase.com/projects)
2. Select your project
3. Navigate to Settings → Database
4. Find your connection details:
   - DB_NAME: Usually 'postgres'
   - DB_USER: Found in the connection string details
   - DB_PASSWORD: Found in the connection string details
   - DB_HOST: Your project ID followed by '.supabase.co'
   - DB_PORT: Usually 5432

Alternatively, you can find these details in the Database → Connection strings section of your Supabase dashboard.

## Required Dependencies

The following packages have been added to support PostgreSQL connections:
- `psycopg2-binary`: PostgreSQL adapter for Python
- `python-decouple`: For managing environment variables

## Additional Configuration Options

The system now supports additional configuration options:

- `DB_SSL`: Enable SSL connection (true/false)
- `DB_SSL_CERT_PATH`: Path to SSL certificate file (optional)
- `NODE_ENV`: Environment indicator (development/production)

## Django Configuration

The Django settings have been updated to:
- Use PostgreSQL as the database engine
- Load database credentials from environment variables
- Maintain compatibility with existing models and migrations

## Flexible Database Configuration

The project now supports flexible database configuration:

### Using SQLite (for development/migration)
To run with SQLite temporarily (e.g., for initial migrations):
```bash
python manage.py migrate --settings=AppAk2.settings_sqlite
python manage.py runserver --settings=AppAk2.settings_sqlite
```

### Using Supabase (for production)
After filling in your Supabase credentials in the `.env` file:
```bash
python manage.py migrate
python manage.py runserver
```

### Environment-Specific Configuration Files
The project includes several environment configuration files:
- `.env` - Default development environment
- `.env.example` - Template for team members
- `.env.production` - Production environment settings

## Migrating Existing Data

If you have existing data in your SQLite database that you want to migrate to Supabase:

1. First, make sure you have run initial migrations with SQLite:
   ```bash
   python manage.py migrate --settings=AppAk2.settings_sqlite
   ```

2. Once your Supabase credentials are configured in `.env`, run:
   ```bash
   python manage.py migrate
   ```

3. To transfer data from SQLite to Supabase, you can dump your SQLite data and import it:
   ```bash
   # Dump data from SQLite
   python manage.py dumpdata --settings=AppAk2.settings_sqlite > datadump.json

   # Load data into Supabase (after configuring the connection)
   python manage.py loaddata datadump.json
   ```

## Running the Application

Once you've configured your environment variables, you can run the application normally:

```bash
python manage.py runserver
```

## Troubleshooting

- If you get a "connection refused" error, double-check your DB_HOST and credentials
- If you get authentication errors, verify your DB_USER and DB_PASSWORD
- Make sure your Supabase project allows connections from your IP address
- Check that the PostgreSQL extension is enabled in your Supabase project
- If you encounter issues during migration, try using the temporary SQLite settings first:
  ```bash
  python manage.py migrate --settings=AppAk2.settings_sqlite
  ```
- The system has intelligent fallback logic: if Supabase credentials are incomplete or missing, it will automatically use SQLite
- When you see the warning "Supabase credentials not found or incomplete. Using SQLite for now.", it means the system is using SQLite as intended until you provide valid Supabase credentials

## Specific Error Resolution

If you received an error like "FATAL: Tenant or user not found", please check:

1. Your connection string format should be:
   ```
   postgresql://[username]:[password]@[host]:[port]/[database_name]
   ```

2. For your specific case, based on the information provided:
   - Host: aws-0-ap-southeast-1.pooler.supabase.com
   - Port: 6543
   - Database name: postgres
   - Username: postgres
   - Password: [your actual database password - not the publishable key]

Note: The SUPABASE_KEY you mentioned (sb_publishable_...) is typically for client-side authentication, not for direct database connections. For database connections, you need the actual database password which can be found in your Supabase dashboard under Project Settings -> Database.