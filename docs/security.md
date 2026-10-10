# Cybersecurity & Defense-in-Depth Model

## 1. Threat Modeling & Security Controls

| Threat Vector | Potential Vulnerability | Security Control in ExpenseWise | Verification Method |
| :--- | :--- | :--- | :--- |
| **Credential Theft** | Plaintext / Weakly Hashed Passwords | Passwords hashed using **Argon2id** (memory-hard, resistant to GPU/ASIC brute forcing) | Automated auth test checks hash format & verifies non-plaintext storage |
| **Session Hijacking** | Indefinite / Unsigned Tokens | Signed **HMAC-SHA256 JWT** tokens with strict expiration (`exp`) and algorithm enforcement | Pytest JWT tampering and expiration test suite |
| **IDOR / Broken Access Control** | User accessing another user's financial data | Every query strictly binds `user_id == current_user.id` derived from JWT; frontend user ID never trusted | Cross-user isolation tests (User A vs User B) |
| **SQL Injection** | Dynamic SQL query concatenation | **SQLAlchemy ORM** parameterized queries exclusively | ORM validation & Pytest query tests |
| **Mass Assignment** | Client injecting unauthorized database fields | **Pydantic schemas** with explicit allowlists of fields for creation and updates | Schema validation tests |
| **Client Token Tampering** | Tokens stored in plain SharedPreferences | **flutter_secure_storage** (Android Keystore / EncryptedSharedPreferences) | Secure storage integration tests |
| **Sensitive Data Exposure** | Secrets committed to Git repository | Strict `.gitignore`, `.env.example` placeholders only, environment-driven configuration | Repository hygiene check |

## 2. Authentication Flow
1. **User Registration (`POST /auth/register`)**:
   - Validates email format, unique email check, and strong password constraints (minimum 8 chars).
   - Password is hashed using Argon2 with salt before saving to SQLite.
2. **User Login (`POST /auth/login`)**:
   - Verifies email and Argon2 hash.
   - If invalid, returns a generic `401 Unauthorized: Invalid email or password` (preventing user enumeration).
   - If valid, generates a signed JWT access token containing `{ "sub": user_id, "exp": ... }`.
3. **Protected Requests (`/transactions`, `/budgets`, etc.)**:
   - `HTTPBearer` dependency extracts token from header.
   - JWT signature and expiration are verified.
   - Database queries are scoped strictly to the authenticated `user_id`.

## 3. Known Limitations & Educational Scope
* **Stateless Token Revocation**: In this version, logging out clears the JWT from mobile secure storage. Immediate server-side token blacklisting (e.g. Redis blocklist) is documented as a future enhancement.
* **HTTPS in Production**: For local development on Android emulator, cleartext HTTP to `10.0.2.2` is permitted. For production, strict TLS/HTTPS is mandatory.
