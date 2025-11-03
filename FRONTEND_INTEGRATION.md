# Frontend-Backend Integration Guide

This guide explains how the Next.js frontend should integrate with the FastAPI backend for the Financial P2P application.

## Architecture Overview

```
Frontend (Next.js)          Backend (FastAPI)           Supabase
     │                            │                         │
     │  1. POST /api/auth/signup  │                         │
     ├───────────────────────────>│  2. Create user in Auth │
     │                            ├────────────────────────>│
     │                            │  3. Return JWT token    │
     │                            │<────────────────────────┤
     │  4. Receive JWT token      │                         │
     │<───────────────────────────┤                         │
     │                            │                         │
     │  5. Store token in state   │                         │
     │                            │                         │
     │  6. Use token for requests │                         │
     ├───────────────────────────>│  7. Verify JWT          │
     │   (Authorization: Bearer)  ├────────────────────────>│
     │                            │  8. Process request     │
     │<───────────────────────────┤                         │
```

**Key Points:**
- ✅ Frontend ONLY calls backend API endpoints (never directly calls Supabase)
- ✅ Backend handles all Supabase operations (signup, login, token verification)
- ✅ Frontend stores and manages JWT tokens from backend responses
- ✅ Frontend includes tokens in Authorization headers for protected routes

---

## Backend API Base URL

Development: `http://localhost:8000`

All API endpoints are prefixed with `/api`:
- Authentication: `/api/auth/*`
- Transfers: `/api/transfers/*`

---

## Authentication Flow

### 1. User Registration (Signup)

**Frontend Code:**
```typescript
// src/lib/api.ts
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export async function signup(email: string, password: string, fullName: string) {
  const response = await fetch(`${API_BASE_URL}/api/auth/signup`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      email,
      password,
      full_name: fullName,
    }),
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Signup failed');
  }

  return await response.json();
}
```

**Backend Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
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

### 2. User Login

**Frontend Code:**
```typescript
export async function login(email: string, password: string) {
  const response = await fetch(`${API_BASE_URL}/api/auth/login`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      email,
      password,
    }),
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Login failed');
  }

  return await response.json();
}
```

**Backend Response:** Same as signup

### 3. Store Token in Frontend

**Using Context API (Recommended):**
```typescript
// src/contexts/AuthContext.tsx
'use client';

import { createContext, useContext, useState, useEffect } from 'react';

interface User {
  id: string;
  email: string;
  full_name: string | null;
  balance: string;
}

interface AuthContextType {
  user: User | null;
  token: string | null;
  login: (email: string, password: string) => Promise<void>;
  signup: (email: string, password: string, fullName: string) => Promise<void>;
  logout: () => void;
  isLoading: boolean;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [token, setToken] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    // Load token from localStorage on mount
    const savedToken = localStorage.getItem('auth_token');
    const savedUser = localStorage.getItem('auth_user');
    
    if (savedToken && savedUser) {
      setToken(savedToken);
      setUser(JSON.parse(savedUser));
    }
    setIsLoading(false);
  }, []);

  const handleLogin = async (email: string, password: string) => {
    const response = await fetch('http://localhost:8000/api/auth/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password }),
    });

    if (!response.ok) throw new Error('Login failed');

    const data = await response.json();
    
    setToken(data.access_token);
    setUser(data.user);
    
    localStorage.setItem('auth_token', data.access_token);
    localStorage.setItem('auth_user', JSON.stringify(data.user));
  };

  const handleSignup = async (email: string, password: string, fullName: string) => {
    const response = await fetch('http://localhost:8000/api/auth/signup', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password, full_name: fullName }),
    });

    if (!response.ok) throw new Error('Signup failed');

    const data = await response.json();
    
    setToken(data.access_token);
    setUser(data.user);
    
    localStorage.setItem('auth_token', data.access_token);
    localStorage.setItem('auth_user', JSON.stringify(data.user));
  };

  const handleLogout = () => {
    setToken(null);
    setUser(null);
    localStorage.removeItem('auth_token');
    localStorage.removeItem('auth_user');
  };

  return (
    <AuthContext.Provider 
      value={{ 
        user, 
        token, 
        login: handleLogin, 
        signup: handleSignup, 
        logout: handleLogout,
        isLoading 
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) throw new Error('useAuth must be used within AuthProvider');
  return context;
}
```

### 4. Making Authenticated Requests

**Helper Function:**
```typescript
// src/lib/api.ts
export async function fetchWithAuth(endpoint: string, options: RequestInit = {}) {
  const token = localStorage.getItem('auth_token');
  
  if (!token) {
    throw new Error('No authentication token found');
  }

  const response = await fetch(`${API_BASE_URL}${endpoint}`, {
    ...options,
    headers: {
      ...options.headers,
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json',
    },
  });

  if (response.status === 401) {
    // Token expired or invalid
    localStorage.removeItem('auth_token');
    localStorage.removeItem('auth_user');
    window.location.href = '/login';
    throw new Error('Authentication expired');
  }

  return response;
}
```

---

## Protected Routes

**Frontend Implementation:**
```typescript
// src/components/AuthGuard.tsx
'use client';

import { useAuth } from '@/contexts/AuthContext';
import { useRouter } from 'next/navigation';
import { useEffect } from 'react';

export function AuthGuard({ children }: { children: React.ReactNode }) {
  const { user, isLoading } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (!isLoading && !user) {
      router.push('/login');
    }
  }, [user, isLoading, router]);

  if (isLoading) {
    return <div>Loading...</div>;
  }

  if (!user) {
    return null;
  }

  return <>{children}</>;
}
```

**Usage in Pages:**
```typescript
// src/app/dashboard/page.tsx
import { AuthGuard } from '@/components/AuthGuard';

export default function DashboardPage() {
  return (
    <AuthGuard>
      <div>Protected Dashboard Content</div>
    </AuthGuard>
  );
}
```

---

## API Integration Examples

### Get User Balance

```typescript
async function getBalance() {
  const response = await fetchWithAuth('/api/auth/balance');
  
  if (!response.ok) {
    throw new Error('Failed to fetch balance');
  }
  
  return await response.json();
}

// Usage
const { user_id, email, balance } = await getBalance();
```

### Send Money (P2P Transfer)

```typescript
async function sendMoney(toEmail: string, amount: number, description?: string) {
  const response = await fetchWithAuth('/api/transfers', {
    method: 'POST',
    body: JSON.stringify({
      to_user_email: toEmail,
      amount: amount,
      description: description || null,
    }),
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Transfer failed');
  }

  return await response.json();
}

// Usage in component
const handleSendMoney = async () => {
  try {
    const result = await sendMoney('recipient@example.com', 50.00, 'Lunch');
    console.log('Transfer successful:', result);
  } catch (error) {
    console.error('Transfer failed:', error);
  }
};
```

### Get Transaction History

```typescript
async function getTransactions(limit = 10, offset = 0, type = 'all') {
  const params = new URLSearchParams({
    limit: limit.toString(),
    offset: offset.toString(),
    type: type,
  });

  const response = await fetchWithAuth(`/api/transfers?${params}`);
  
  if (!response.ok) {
    throw new Error('Failed to fetch transactions');
  }
  
  return await response.json();
}

// Usage
const { total, transactions } = await getTransactions(10, 0, 'all');
```

### Search Users (for recipient selection)

```typescript
async function searchUsers(email: string) {
  const params = new URLSearchParams({ email });
  const response = await fetchWithAuth(`/api/transfers/users/search?${params}`);
  
  if (!response.ok) {
    throw new Error('Failed to search users');
  }
  
  return await response.json();
}

// Usage
const users = await searchUsers('alice');
// Returns: [{ id: "uuid", email: "alice@example.com", full_name: "Alice Johnson" }]
```

---

## Environment Variables

### Frontend (.env.local)

```env
# Backend API URL
NEXT_PUBLIC_API_URL=http://localhost:8000

# No Supabase keys needed in frontend!
# Backend handles all Supabase operations
```

### Backend (.env)

```env
# Supabase credentials (backend only)
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key
SUPABASE_ANON_KEY=your-anon-key
DATABASE_URL=postgresql://postgres:password@db.xxx.supabase.co:5432/postgres

# CORS - Allow frontend origin
ALLOWED_ORIGINS=http://localhost:3000
```

---

## CORS Configuration

The backend is already configured to accept requests from `http://localhost:3000`.

If you need to add more origins:

```env
# .env
ALLOWED_ORIGINS=http://localhost:3000,https://yourapp.com
```

---

## Error Handling

**Backend Error Response Format:**
```json
{
  "detail": "Error message",
  "error_code": "validation_error",
  "message": "Additional context"
}
```

**Frontend Error Handling:**
```typescript
try {
  const result = await sendMoney(email, amount);
} catch (error) {
  if (error instanceof Error) {
    // Show error to user
    toast.error(error.message);
  }
}
```

---

## Complete Frontend API Client Example

```typescript
// src/lib/api-client.ts
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

class ApiClient {
  private getAuthHeaders() {
    const token = localStorage.getItem('auth_token');
    return {
      'Content-Type': 'application/json',
      ...(token && { 'Authorization': `Bearer ${token}` }),
    };
  }

  private async request(endpoint: string, options: RequestInit = {}) {
    const response = await fetch(`${API_BASE_URL}${endpoint}`, {
      ...options,
      headers: {
        ...this.getAuthHeaders(),
        ...options.headers,
      },
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: 'Request failed' }));
      throw new Error(error.detail || 'Request failed');
    }

    return response.json();
  }

  // Auth
  async signup(email: string, password: string, fullName: string) {
    return this.request('/api/auth/signup', {
      method: 'POST',
      body: JSON.stringify({ email, password, full_name: fullName }),
    });
  }

  async login(email: string, password: string) {
    return this.request('/api/auth/login', {
      method: 'POST',
      body: JSON.stringify({ email, password }),
    });
  }

  async getMe() {
    return this.request('/api/auth/me');
  }

  async getBalance() {
    return this.request('/api/auth/balance');
  }

  // Transfers
  async sendMoney(toEmail: string, amount: number, description?: string) {
    return this.request('/api/transfers', {
      method: 'POST',
      body: JSON.stringify({ to_user_email: toEmail, amount, description }),
    });
  }

  async getTransactions(limit = 10, offset = 0, type = 'all') {
    const params = new URLSearchParams({ 
      limit: limit.toString(), 
      offset: offset.toString(), 
      type 
    });
    return this.request(`/api/transfers?${params}`);
  }

  async getTransaction(id: string) {
    return this.request(`/api/transfers/${id}`);
  }

  async searchUsers(email: string) {
    const params = new URLSearchParams({ email });
    return this.request(`/api/transfers/users/search?${params}`);
  }
}

export const apiClient = new ApiClient();
```

---

## Testing the Integration

### 1. Start Backend
```bash
cd backend
poetry run uvicorn src.main:app --reload --port 8000
```

### 2. Test with cURL
```bash
# Test signup
curl -X POST http://localhost:8000/api/auth/signup \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"Test123!","full_name":"Test User"}'

# Save the access_token from response

# Test authenticated request
curl http://localhost:8000/api/auth/me \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### 3. Start Frontend (when ready)
```bash
cd frontend
npm run dev
```

### 4. Test Flow
1. Open http://localhost:3000
2. Navigate to signup page
3. Register a new user
4. Should receive token and redirect to dashboard
5. Make a transfer
6. View transaction history

---

## Common Issues & Solutions

### Issue: CORS errors in browser

**Solution:** Check backend `.env`:
```env
ALLOWED_ORIGINS=http://localhost:3000
```

Restart backend after changing.

### Issue: 401 Unauthorized on authenticated requests

**Solutions:**
1. Check token is being sent in Authorization header
2. Verify token hasn't expired (30 min default)
3. Check token format: `Bearer <token>` (note the space)
4. Login again to get fresh token

### Issue: "User not found in database" after Supabase signup

**Solution:** 
- Use backend `/api/auth/signup` endpoint (not Supabase directly)
- Backend creates user in both Supabase Auth AND application database

---

## Security Best Practices

1. ✅ **Never expose Supabase service role key in frontend**
   - Only in backend .env
   - Never commit to git

2. ✅ **Always use HTTPS in production**
   - Update API_BASE_URL to https://

3. ✅ **Store tokens securely**
   - Use httpOnly cookies in production (requires backend cookie handling)
   - Or secure localStorage (current implementation)

4. ✅ **Validate input on frontend**
   - Before sending to backend
   - Backend also validates (defense in depth)

5. ✅ **Handle token expiration**
   - Implement token refresh
   - Or redirect to login on 401

---

## Next Steps

1. ✅ Backend is ready
2. 📝 Use this guide to integrate frontend
3. 📝 Implement AuthContext in Next.js
4. 📝 Create login/signup pages
5. 📝 Build protected dashboard
6. 📝 Test end-to-end flow

---

**The backend handles ALL Supabase operations. Frontend just calls backend API! 🎉**

