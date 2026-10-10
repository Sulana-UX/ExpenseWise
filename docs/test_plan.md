# Security & Functional Test Plan

## 1. Test Matrix & Actual Execution Results

| Category | Test Case | Target Endpoint / Component | Expected Result | Actual Result |
| :--- | :--- | :--- | :--- | :--- |
| **Auth** | User Registration | `POST /auth/register` | 201 Created with safe user profile | ✅ **PASSED** (201 Created, Argon2 verified) |
| **Auth** | Duplicate Email Rejection | `POST /auth/register` | 400 Bad Request (Email already registered) | ✅ **PASSED** (400 Bad Request) |
| **Auth** | Password Complexity Policy | `POST /auth/register` | 422 Unprocessable Entity (Password policy) | ✅ **PASSED** (422 Rejected) |
| **Auth** | Successful Login | `POST /auth/login` | 200 OK with valid JWT token | ✅ **PASSED** (200 OK with Bearer token) |
| **Auth** | Invalid Password Login | `POST /auth/login` | 401 Unauthorized (Generic error message) | ✅ **PASSED** (401 Generic error) |
| **Security** | Tampered JWT Signature | `GET /auth/me` | 401 Unauthorized (Invalid token) | ✅ **PASSED** (401 Unauthorized) |
| **Security** | Expired JWT Token | `GET /auth/me` | 401 Unauthorized (Token expired) | ✅ **PASSED** (401 Session expired) |
| **Access Control (IDOR)** | Cross-User Transaction Isolation | `GET /transactions/{id}` | User A cannot access User B's transaction | ✅ **PASSED** (404 Not Found) |
| **Access Control (IDOR)** | Cross-User Transaction Edit | `PUT /transactions/{id}` | User A cannot edit User B's transaction | ✅ **PASSED** (404 Not Found) |
| **Access Control (IDOR)** | Cross-User Transaction Delete | `DELETE /transactions/{id}` | User A cannot delete User B's transaction | ✅ **PASSED** (404 Not Found) |
| **Transactions** | Create Income & Expense | `POST /transactions` | 201 Created with accurate amounts & dates | ✅ **PASSED** (201 Created) |
| **Transactions** | Reject Negative/Zero Amount | `POST /transactions` | 422 Validation error | ✅ **PASSED** (422 Rejected) |
| **Transactions** | Multi-field Filter & Search | `GET /transactions` | Filter by category, type, date range | ✅ **PASSED** (200 OK filtered) |
| **Budgets** | Set & Retrieve Monthly Budget | `POST /budgets`, `GET /budgets` | Upserts budget for user, year, month | ✅ **PASSED** (200 OK) |
| **Budgets** | 80% Warning Status | `GET /budgets/status` | Status changes to "warning" when spending >= 80% | ✅ **PASSED** (Warning trigger verified) |
| **Budgets** | Over-Budget Alert | `GET /budgets/status` | Status changes to "over_budget" when spending > 100% | ✅ **PASSED** (Over-budget trigger verified) |
| **Budgets** | Income Isolation | `GET /budgets/status` | Income not counted as expense | ✅ **PASSED** (Zero expense modification) |
| **Reports** | Monthly Summary Calculation | `GET /reports/monthly` | Accurate income, expenses, balance & savings rate | ✅ **PASSED** (60.00% savings rate verified) |
| **Reports** | Zero-Income Safe Division | `GET /reports/monthly` | Zero income does not trigger division by zero | ✅ **PASSED** (0.00% safe fallback) |
| **Reports** | Safe CSV Export | `GET /reports/export` | CSV containing only authenticated user's records | ✅ **PASSED** (Cross-user data omitted) |
