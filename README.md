# Financial P2P Backend API

A production-ready FastAPI backend for P2P money transfers with Supabase authentication and PostgreSQL database.

## Features

✅ **Supabase Authentication** - Email/password auth with JWT tokens (backend only!)  
✅ **P2P Transfers** - Send money between users with atomic transactions  
✅ **Balance Management** - Real-time balance tracking  
✅ **Transaction History** - Complete transaction records with filtering  
✅ **User Search** - Find recipients by email  
✅ **Input Validation** - Comprehensive Pydantic schemas  
✅ **Error Handling** - Structured error responses  
✅ **API Documentation** - Auto-generated Swagger UI  
✅ **Mock Data** - Seed script for testing

## Authentication Architecture

**Important:** The backend handles ALL Supabase authentication operations.

```
Frontend (Next.js)     →     Backend (FastAPI)     →     Supabase
                             (Handles all auth)          (Auth service)

✅ Correct: Frontend calls backend API endpoints
❌ Wrong: Frontend directly calls Supabase
```

The frontend should:
1. Call `/api/auth/signup` and `/api/auth/login` endpoints
2. Receive JWT tokens from backend responses
3. Include tokens in `Authorization: Bearer <token>` headers
4. Never directly interact with Supabase

See **FRONTEND_INTEGRATION.md** for complete integration guide.  

## Quick Start

### 1. Install Dependencies

```bash
cd backend
poetry install
```

### 2. Environment Setup

Create a `.env` file:

```bash
cp .env.example .env
```

Edit `.env` with your Supabase credentials:

```env
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key
SUPABASE_ANON_KEY=your-anon-key
DATABASE_URL=postgresql://postgres:password@db.your-project.supabase.co:5432/postgres
```

### 3. Create Database Tables

The tables will be created automatically when you run the seed script or start the server.

Alternatively, run SQL in Supabase SQL Editor:

```sql
-- Users table (extends Supabase auth.users)
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY,
    email VARCHAR NOT NULL UNIQUE,
    full_name VARCHAR,
    balance NUMERIC(10, 2) DEFAULT 1000.00 NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Transactions table
CREATE TYPE transaction_status AS ENUM ('pending', 'completed', 'failed');
CREATE TYPE transaction_category AS ENUM ('transfer', 'payment', 'refund');

CREATE TABLE IF NOT EXISTS transactions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    from_user_id UUID REFERENCES users(id) NOT NULL,
    to_user_id UUID REFERENCES users(id) NOT NULL,
    amount NUMERIC(10, 2) NOT NULL,
    description VARCHAR,
    status transaction_status DEFAULT 'pending' NOT NULL,
    category transaction_category DEFAULT 'transfer' NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_transactions_from_user ON transactions(from_user_id);
CREATE INDEX idx_transactions_to_user ON transactions(to_user_id);
CREATE INDEX idx_transactions_created_at ON transactions(created_at);
```

### 4. Seed Mock Data (Optional)

```bash
poetry run python scripts/seed_data.py
```

This creates 8 mock users and 30-40 sample transactions.

### 5. Run the Server

```bash
poetry run uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

Server will start at: **http://localhost:8000**

## API Documentation

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## API Endpoints

### Authentication

#### Register
```http
POST /api/auth/signup
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "SecurePass123!",
  "full_name": "John Doe"
}
```

#### Login
```http
POST /api/auth/login
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "SecurePass123!"
}
```

Response:
```json
{
  "access_token": "eyJhbGc...",
  "token_type": "bearer",
  "user": {
    "id": "uuid",
    "email": "user@example.com",
    "full_name": "John Doe",
    "balance": "1000.00",
    "created_at": "2024-11-03T10:00:00",
    "updated_at": "2024-11-03T10:00:00"
  }
}
```

#### Get Current User
```http
GET /api/auth/me
Authorization: Bearer <token>
```

#### Get Balance
```http
GET /api/auth/balance
Authorization: Bearer <token>
```

### Transfers

#### Send Money
```http
POST /api/transfers
Authorization: Bearer <token>
Content-Type: application/json

{
  "to_user_email": "recipient@example.com",
  "amount": 50.00,
  "description": "Lunch payment"
}
```

Response:
```json
{
  "success": true,
  "transaction_id": "uuid",
  "message": "Successfully sent $50.00 to recipient@example.com",
  "transaction": {
    "id": "uuid",
    "from_user_id": "uuid",
    "to_user_id": "uuid",
    "amount": "50.00",
    "description": "Lunch payment",
    "status": "completed",
    "category": "transfer",
    "created_at": "2024-11-03T10:00:00"
  }
}
```

#### Get Transaction History
```http
GET /api/transfers?limit=10&offset=0&type=all
Authorization: Bearer <token>
```

Query Parameters:
- `limit` (1-100): Number of transactions (default: 10)
- `offset` (>=0): Pagination offset (default: 0)
- `type`: Filter by `sent`, `received`, or `all` (default: all)

#### Get Transaction Details
```http
GET /api/transfers/{transaction_id}
Authorization: Bearer <token>
```

#### Search Users
```http
GET /api/transfers/users/search?email=alice
Authorization: Bearer <token>
```

## Project Structure

```
backend/
├── src/
│   ├── __init__.py
│   ├── main.py              # FastAPI app
│   ├── config.py            # Settings
│   ├── database.py          # Database connection
│   ├── models.py            # SQLAlchemy models
│   ├── schemas.py           # Pydantic schemas
│   ├── auth.py              # Supabase authentication
│   ├── api/
│   │   ├── __init__.py
│   │   ├── auth.py          # Auth endpoints
│   │   └── transfers.py     # Transfer endpoints
│   └── services/
│       ├── __init__.py
│       └── transfer_service.py  # Transfer business logic
├── scripts/
│   ├── __init__.py
│   └── seed_data.py         # Database seeding
├── .env.example
├── .gitignore
├── pyproject.toml
└── README.md
```

## Database Models

### User
- `id` (UUID) - Primary key, references Supabase auth.users
- `email` (String) - Unique email address
- `full_name` (String) - User's full name
- `balance` (Decimal) - Current balance (default: 1000.00)
- `created_at` (DateTime)
- `updated_at` (DateTime)

### Transaction
- `id` (UUID) - Primary key
- `from_user_id` (UUID) - Sender's user ID
- `to_user_id` (UUID) - Receiver's user ID
- `amount` (Decimal) - Transfer amount
- `description` (String) - Optional description
- `status` (Enum) - pending, completed, or failed
- `category` (Enum) - transfer, payment, or refund
- `created_at` (DateTime)

## Transfer Logic

The transfer service implements **atomic transactions** to ensure data consistency:

1. Validates transfer amount and limits
2. Checks sender has sufficient balance
3. Prevents self-transfers
4. Creates transaction record (pending status)
5. Updates both users' balances atomically
6. Marks transaction as completed
7. Commits all changes together or rolls back on error

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `SUPABASE_URL` | Supabase project URL | Required |
| `SUPABASE_SERVICE_ROLE_KEY` | Service role key | Required |
| `SUPABASE_ANON_KEY` | Anonymous key | Required |
| `DATABASE_URL` | PostgreSQL connection string | Required |
| `HOST` | Server host | 0.0.0.0 |
| `PORT` | Server port | 8000 |
| `DEBUG` | Debug mode | false |
| `ALLOWED_ORIGINS` | CORS allowed origins | http://localhost:3000 |
| `MIN_TRANSFER_AMOUNT` | Minimum transfer | 0.01 |
| `MAX_TRANSFER_AMOUNT` | Maximum transfer | 10000.00 |

## Security Features

- **Supabase JWT Authentication** - Secure token-based auth
- **Password Validation** - Enforced password strength
- **Atomic Transactions** - ACID compliance for transfers
- **CORS Configuration** - Restricted origins
- **SQL Injection Prevention** - SQLAlchemy ORM
- **Input Validation** - Pydantic schemas
- **Error Handling** - No sensitive data in errors

## Mock Users

After running the seed script, you can use these test accounts:

- alice@example.com
- bob@example.com
- charlie@example.com
- diana@example.com
- eve@example.com
- frank@example.com
- grace@example.com
- henry@example.com

**Note**: You'll need to create these users in Supabase auth first, or create your own test users via the signup endpoint.

## Development

### Run in Development Mode

```bash
poetry run uvicorn src.main:app --reload --port 8000
```

### View Logs

Logs include:
- Request/response logging
- Error tracking
- Performance metrics

## Production Deployment

### Checklist

- [ ] Set strong `SECRET_KEY`
- [ ] Configure production `DATABASE_URL`
- [ ] Set `DEBUG=false`
- [ ] Update `ALLOWED_ORIGINS`
- [ ] Enable HTTPS
- [ ] Set up monitoring
- [ ] Configure backup
- [ ] Review security headers

### Docker Support (Future Enhancement)

Create `Dockerfile` for containerized deployment.

## Technologies

- **FastAPI** - Modern Python web framework
- **SQLAlchemy** - SQL ORM
- **Supabase** - Authentication & PostgreSQL
- **Pydantic** - Data validation
- **Python-JOSE** - JWT handling
- **PostgreSQL** - Database

## API Versioning

Current version: **1.0.0**

## License

MIT License

## Support

For issues and questions:
- Check `/docs` for interactive documentation
- Review error messages (structured responses)
- Check logs for debugging

---

**Built with ❤️ for Brex Interview Practice**

