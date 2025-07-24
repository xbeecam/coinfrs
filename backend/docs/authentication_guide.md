# Authentication Integration Guide

## Overview

Coinfrs uses passwordless authentication with two options:
1. **Google OAuth** - Sign in with Google account
2. **Email OTP** - Sign in with a 6-digit code sent to your email

Both methods return JWT tokens that must be included in subsequent API requests.

## Authentication Endpoints

### Google OAuth Flow

#### 1. Redirect to Google
```
GET /api/v1/auth/oauth/google?redirect_uri={your_callback_url}
```

This endpoint redirects the user to Google's OAuth consent screen.

#### 2. Handle Callback
```
POST /api/v1/auth/oauth/google/callback
Content-Type: application/json

{
  "code": "authorization_code_from_google",
  "state": "optional_state_parameter"
}
```

**Response:**
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "token_type": "bearer"
}
```

### Email OTP Flow

#### 1. Request OTP
```
POST /api/v1/auth/otp/request
Content-Type: application/json

{
  "email": "user@example.com"
}
```

**Response:**
```json
{
  "message": "If the email exists, an OTP has been sent."
}
```

#### 2. Verify OTP
```
POST /api/v1/auth/otp/verify
Content-Type: application/json

{
  "email": "user@example.com",
  "otp": "123456"
}
```

**Response:**
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "token_type": "bearer"
}
```

## Token Management

### Access Token
- Include in Authorization header: `Authorization: Bearer {access_token}`
- Expires in 15 minutes
- Used for API requests

### Refresh Token
- Stored as httpOnly cookie
- Expires in 7 days
- Used to get new access tokens

## Frontend Implementation

### Google OAuth

```javascript
// 1. Redirect to Google
const redirectUri = encodeURIComponent('https://yourapp.com/auth/google/callback');
window.location.href = `/api/v1/auth/oauth/google?redirect_uri=${redirectUri}`;

// 2. Handle callback (on callback page)
const urlParams = new URLSearchParams(window.location.search);
const code = urlParams.get('code');

const response = await fetch('/api/v1/auth/oauth/google/callback', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({ code }),
  credentials: 'include', // Important for cookies
});

const { access_token } = await response.json();
// Store access_token in memory or localStorage
```

### Email OTP

```javascript
// 1. Request OTP
async function requestOTP(email) {
  const response = await fetch('/api/v1/auth/otp/request', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ email }),
  });
  
  return response.ok;
}

// 2. Verify OTP
async function verifyOTP(email, otp) {
  const response = await fetch('/api/v1/auth/otp/verify', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ email, otp }),
    credentials: 'include', // Important for cookies
  });
  
  if (response.ok) {
    const { access_token } = await response.json();
    // Store access_token in memory or localStorage
    return access_token;
  }
  
  throw new Error('Invalid OTP');
}
```

### Making Authenticated Requests

```javascript
// Include access token in all API requests
async function fetchUserProfile(accessToken) {
  const response = await fetch('/api/v1/users/me', {
    headers: {
      'Authorization': `Bearer ${accessToken}`,
    },
  });
  
  return response.json();
}
```

## Security Considerations

1. **Access Token Storage**: Store in memory or sessionStorage, not localStorage
2. **HTTPS Only**: All authentication endpoints require HTTPS in production
3. **CORS**: Configure allowed origins properly
4. **Rate Limiting**: OTP requests are rate-limited to 5 per hour per email

## Error Handling

### Common Error Responses

```json
{
  "detail": "Invalid email or OTP"
}
```

```json
{
  "detail": "Google OAuth not configured"
}
```

### Rate Limiting (OTP)
If rate limited, the request will still return success but no OTP will be sent.

## Development Setup

### Environment Variables
```
GOOGLE_CLIENT_ID=your_google_client_id
GOOGLE_CLIENT_SECRET=your_google_client_secret
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USERNAME=your_email@gmail.com
EMAIL_PASSWORD=your_app_password
```

### Testing Without Email
In development, if email is not configured, OTP codes will be logged to the console.