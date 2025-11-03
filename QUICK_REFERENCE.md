# Quick Reference - Frontend Integration

## 🎯 Key Principle

**Frontend NEVER calls Supabase directly. All auth goes through backend API.**

```
✅ Frontend → Backend API → Supabase
❌ Frontend → Supabase (NEVER!)
```

---

## 🔑 Authentication Flow

### 1. Signup
```typescript
POST http://localhost:8000/api/auth/signup
Body: { email, password, full_name }
Response: { access_token, token_type: "bearer", user }
```

### 2. Login
```typescript
POST http://localhost:8000/api/auth/login
Body: { email, password }
Response: { access_token, token_type: "bearer", user }
```

### 3. Store Token
```typescript
localStorage.setItem('auth_token', data.access_token);
```

### 4. Use Token
```typescript
Headers: { 'Authorization': 'Bearer <token>' }
```

---

## 📡 API Endpoints

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| POST | `/api/auth/signup` | No | Register user |
| POST | `/api/auth/login` | No | Login user |
| GET | `/api/auth/me` | Yes | Get current user |
| GET | `/api/auth/balance` | Yes | Get balance |
| POST | `/api/transfers` | Yes | Send money |
| GET | `/api/transfers` | Yes | Get transactions |
| GET | `/api/transfers/{id}` | Yes | Get transaction |
| GET | `/api/transfers/users/search?email=` | Yes | Search users |

---

## 💻 Frontend Code Templates

### AuthContext
```typescript
const { user, token, login, signup, logout } = useAuth();
```

### API Client
```typescript
const response = await fetch('http://localhost:8000/api/endpoint', {
  headers: {
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json',
  },
  body: JSON.stringify(data),
});
```

### Send Money
```typescript
await fetch('http://localhost:8000/api/transfers', {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({
    to_user_email: 'recipient@example.com',
    amount: 50.00,
    description: 'Lunch',
  }),
});
```

---

## 🌍 Environment Variables

### Frontend (.env.local)
```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```

### Backend (.env)
```env
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_SERVICE_ROLE_KEY=xxx
SUPABASE_ANON_KEY=xxx
DATABASE_URL=postgresql://...
ALLOWED_ORIGINS=http://localhost:3000
```

---

## ✅ Integration Checklist

- [ ] Backend running on port 8000
- [ ] Frontend configured with `NEXT_PUBLIC_API_URL`
- [ ] AuthContext implemented with localStorage
- [ ] Login/signup pages call backend API
- [ ] Protected routes check for token
- [ ] All API calls include Authorization header
- [ ] Error handling for 401 (expired token)
- [ ] CORS configured in backend

---

## 🚨 Common Mistakes to Avoid

❌ Don't install `@supabase/supabase-js` in frontend  
❌ Don't put Supabase keys in frontend .env  
❌ Don't call Supabase directly from frontend  
❌ Don't forget Authorization header  
❌ Don't forget "Bearer " prefix in token  

✅ Only call backend API endpoints  
✅ Only store JWT token from backend  
✅ Only include token in headers  

---

## 📚 Documentation

- **FRONTEND_INTEGRATION.md** - Complete integration guide with examples
- **README.md** - API reference and backend setup
- **SETUP_GUIDE.md** - Step-by-step backend setup
- **/docs** - Interactive Swagger UI at http://localhost:8000/docs

---

## 🔧 Testing

```bash
# Test backend is running
curl http://localhost:8000/health

# Test signup
curl -X POST http://localhost:8000/api/auth/signup \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"Test123!","full_name":"Test"}'

# Test with token
curl http://localhost:8000/api/auth/me \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

**Need help? Check FRONTEND_INTEGRATION.md for detailed examples!**

