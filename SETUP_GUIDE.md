# Financial P2P Backend - Setup Guide

This guide will walk you through setting up the backend from scratch.

## Prerequisites

- Python 3.10 or higher
- Poetry (Python dependency manager)
- Supabase account (free tier is fine)

## Important: Authentication Architecture

⚠️ **The backend handles ALL Supabase authentication!**

The frontend should NEVER directly call Supabase. Instead:
- Frontend → Backend API endpoints → Supabase
- Backend processes auth and returns JWT tokens
- Frontend uses tokens for subsequent requests

See `FRONTEND_INTEGRATION.md` for complete integration guide.

## Step-by-Step Setup

### 1. Install Poetry

```bash
curl -sSL https://install.python-poetry.org | python3 -
```

Verify installation:
```bash
poetry --version
```

### 2. Set Up Supabase Project

1. Go to [https://supabase.com](https://supabase.com) and create an account
2. Click "New Project"
3. Fill in:
   - Project name: `financial-p2p` (or your choice)
   - Database password: Create a strong password (save it!)
   - Region: Choose closest to you
4. Wait for project to initialize (~2 minutes)

### 3. Get Supabase Credentials

In your Supabase dashboard:

1. Go to **Settings** → **API**
2. Copy these values:
   - **Project URL** (e.g., `https://xxxxx.supabase.co`)
   - **anon public** key
   - **service_role** key (click "Reveal" first)

3. Go to **Settings** → **Database**
4. Copy **Connection string** → **URI**
   - It looks like: `postgresql://postgres:[YOUR-PASSWORD]@db.xxxxx.supabase.co:5432/postgres`

### 4. Create Database Tables

In Supabase dashboard:

1. Go to **SQL Editor**
2. Click "New Query"
3. Copy and paste the entire contents of `database_schema.sql`
4. Click "Run" or press Cmd/Ctrl + Enter
5. You should see "Success. No rows returned" message

### 5. Configure Environment Variables

In the backend directory:

```bash
cd /Users/krish/Projects/brex/financial-app/backend
cp .env.example .env
```

Edit `.env` file with your Supabase credentials:

```env
SUPABASE_URL=https://xxxxx.supabase.co
SUPABASE_SERVICE_ROLE_KEY=eyJhbGc... (your service role key)
SUPABASE_ANON_KEY=eyJhbGc... (your anon key)
DATABASE_URL=postgresql://postgres:[YOUR-PASSWORD]@db.xxxxx.supabase.co:5432/postgres
```

### 6. Install Dependencies

```bash
poetry install
```

This will:
- Create a virtual environment
- Install all required packages
- Set up the project

### 7. Create Test Users in Supabase

Option A: Use Supabase Dashboard
1. Go to **Authentication** → **Users**
2. Click "Add user" → "Create new user"
3. Enter:
   - Email: `test@example.com`
   - Password: `Test123!` (must meet strength requirements)
4. Click "Create user"
5. Repeat for more users

Option B: Use the API signup endpoint (after starting server)

### 8. Seed Mock Data

```bash
poetry run python scripts/seed_data.py
```

This creates:
- 8 mock users in the database
- 30-40 sample transactions

**Important**: You'll still need to create these users in Supabase Auth separately (or use the signup endpoint).

### 9. Start the Server

```bash
poetry run uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

You should see:
```
INFO:     ======================================================================
INFO:      Financial P2P API v1.0.0
INFO:     ======================================================================
INFO:      Server: 0.0.0.0:8000
INFO:      Debug Mode: True
INFO:      Docs: http://0.0.0.0:8000/docs
INFO:     ======================================================================
INFO:     Uvicorn running on http://0.0.0.0:8000
```

### 10. Test the API

Open your browser and go to:
- **API Docs**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health

You should see the Swagger UI with all available endpoints.

## Testing the API

### Register a New User

Using curl:
```bash
curl -X POST http://localhost:8000/api/auth/signup \
  -H "Content-Type: application/json" \
  -d '{
    "email": "alice@example.com",
    "password": "Alice123!",
    "full_name": "Alice Johnson"
  }'
```

Or use the Swagger UI at `/docs`:
1. Expand "Authentication" → "POST /api/auth/signup"
2. Click "Try it out"
3. Edit the request body
4. Click "Execute"

### Login

```bash
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "alice@example.com",
    "password": "Alice123!"
  }'
```

Save the `access_token` from the response.

### Send Money

```bash
curl -X POST http://localhost:8000/api/transfers \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "to_user_email": "bob@example.com",
    "amount": 50.00,
    "description": "Lunch money"
  }'
```

### Get Transaction History

```bash
curl -X GET "http://localhost:8000/api/transfers?limit=10" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

## Common Issues & Solutions

### Issue: "Could not connect to database"

**Solution**: Check your `DATABASE_URL` in `.env`:
- Make sure you replaced `[YOUR-PASSWORD]` with your actual password
- Verify the URL matches your Supabase project
- Check if your IP is allowed (Supabase allows all by default)

### Issue: "Authentication required" when calling endpoints

**Solution**: 
- Make sure you're including the Authorization header
- Format: `Authorization: Bearer YOUR_ACCESS_TOKEN`
- Token expires after 30 minutes - login again if needed

### Issue: "User not found in database" after login

**Solution**: 
- The user exists in Supabase Auth but not in your users table
- Use the signup endpoint instead of creating users manually in Supabase
- Or manually add the user to the users table with matching ID

### Issue: Poetry command not found

**Solution**:
```bash
# Add Poetry to your PATH
export PATH="$HOME/.local/bin:$PATH"

# Or reinstall Poetry
curl -sSL https://install.python-poetry.org | python3 -
```

### Issue: Port 8000 already in use

**Solution**:
```bash
# Use a different port
poetry run uvicorn src.main:app --reload --port 8001

# Or kill the process using port 8000
lsof -ti:8000 | xargs kill -9
```

## Next Steps

1. **Test all endpoints** using the Swagger UI
2. **Create more test users** via signup endpoint
3. **Test P2P transfers** between users
4. **Check transaction history** and filtering
5. **Ready for frontend integration!**

## Environment Variables Reference

| Variable | Required | Description | Example |
|----------|----------|-------------|---------|
| SUPABASE_URL | Yes | Your Supabase project URL | `https://xxx.supabase.co` |
| SUPABASE_SERVICE_ROLE_KEY | Yes | Service role key | `eyJhbG...` |
| SUPABASE_ANON_KEY | Yes | Anonymous public key | `eyJhbG...` |
| DATABASE_URL | Yes | PostgreSQL connection string | `postgresql://postgres:...` |
| HOST | No | Server host | `0.0.0.0` |
| PORT | No | Server port | `8000` |
| DEBUG | No | Debug mode | `true` or `false` |
| ALLOWED_ORIGINS | No | CORS origins | `http://localhost:3000` |
| MIN_TRANSFER_AMOUNT | No | Min transfer limit | `0.01` |
| MAX_TRANSFER_AMOUNT | No | Max transfer limit | `10000.00` |

## Useful Commands

```bash
# Install dependencies
poetry install

# Run server (development)
poetry run uvicorn src.main:app --reload --port 8000

# Run seed script
poetry run python scripts/seed_data.py

# Check Poetry environment
poetry env info

# Update dependencies
poetry update

# Add new dependency
poetry add package-name
```

## Need Help?

1. Check the main **README.md** for detailed API documentation
2. Review **database_schema.sql** for table structures
3. Check server logs for error messages
4. Verify `.env` file has correct credentials
5. Test with Swagger UI at `/docs` for interactive testing

---

**You're all set! 🚀**

The backend is now ready for the frontend to connect to.

