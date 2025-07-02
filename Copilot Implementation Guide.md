네, 아래는 FastAPI 기반 거래소형(오프체인) USDT(트론/TRC20) 백엔드 서비스 개발을 위한 Copilot(코파일럿)용 개발 지시서입니다.
바로 실무 투입 가능한 명확한 요구사항과 구조/코딩 가이드(영문+주석중심)로 작성했습니다.

⸻

Copilot Implementation Guide

Project: FastAPI-based USDT (TRC20) Backend – Exchange Model
Author: Seyoung Kwon
Target: Github Copilot (Developer AI)

⸻

1. Overview

Develop a backend API server for an exchange-style USDT (TRC20) wallet service.
	•	Backend: FastAPI (Python 3.10+)
	•	DB: PostgreSQL (or MySQL, switchable)
	•	Blockchain: Tron/TRC20 (USDT), on-chain for external deposit/withdrawal only
	•	Wallet structure: All user assets managed centrally (exchange model), per-user balance in DB
	•	Frontend: Not required (admin or API client only)

⸻

2. Core Requirements

2.1 User/Wallet Management
	•	Sign up, login (JWT auth)
	•	Per-user balance (asset: USDT, optionally TRX)
	•	No individual on-chain wallets for users
	•	All on-chain assets are in company wallets (hot/cold/main)

2.2 Internal Transfers (Off-chain)
	•	User-to-user transfer, service payments, rewards, etc.
	•	Handled as DB balance moves (no blockchain tx, no fee, instant)

2.3 External Deposit/Withdrawal (On-chain)
	•	Deposit:
	•	Monitor company wallet(s) for incoming USDT transfers
	•	Identify sender/user via deposit memo or unique deposit address
	•	Update user DB balance accordingly
	•	Withdrawal:
	•	User requests withdrawal (API)
	•	Admin/operator approves and initiates USDT on-chain tx
	•	Deducts user DB balance, records blockchain tx hash

2.4 Admin/Operator Functions
	•	Approve/process withdrawals
	•	View/manage all balances and transactions
	•	Monitor deposit/withdrawal events
	•	Manage operator/admin access

⸻

3. API Endpoints (Sample)

Method	Path	Description	Auth
POST	/signup	User sign-up	-
POST	/login	JWT login	-
GET	/me	User profile	user
GET	/balance	Query balance	user
POST	/transfer	Internal transfer	user
GET	/transactions	Transaction history	user
POST	/withdraw	Request withdrawal	user
POST	/deposit/check	Check deposit (manual trigger)	user
GET	/admin/balances	All balances (admin)	admin
POST	/admin/send	On-chain send (admin only)	admin


⸻

4. DB Schema (minimum required)

users
	•	id (int, PK)
	•	email (string, unique)
	•	password_hash (string)
	•	is_admin (bool)
	•	created_at (datetime)

balances
	•	id (int, PK)
	•	user_id (int, FK)
	•	asset (string, e.g. ‘USDT’)
	•	amount (decimal)
	•	updated_at (datetime)

transactions
	•	id (int, PK)
	•	user_id (int, FK)
	•	type (enum: deposit/withdrawal/transfer/payment)
	•	amount (decimal)
	•	asset (string)
	•	status (enum: pending/completed/failed)
	•	ref_tx_id (string, nullable, on-chain tx hash)
	•	related_user_id (int, nullable, for internal transfer)
	•	created_at (datetime)

⸻

5. Blockchain Integration
	•	Use tronpy or equivalent for Tron on-chain interactions.
	•	All deposits and withdrawals are processed via company wallets.
	•	For deposit detection:
	•	Option 1: assign a unique memo/tag per user, parse incoming transactions
	•	Option 2: assign unique sub-wallets per user (advanced, optional)
	•	Withdrawal processing must be initiated/admin-approved for security.

⸻

6. Security & Operations
	•	Use JWT authentication, bcrypt password hash.
	•	All user and admin actions logged (with IP/time/user).
	•	Operator/admin access requires elevated auth (is_admin flag).
	•	Withdrawals require admin approval (for compliance and risk control).
	•	No private key is ever exposed via API.
	•	(Optional) Add 2FA/multi-factor authentication for admin functions.

⸻

7. Directory Structure (Recommendation)

backend/
├── app/
│   ├── main.py
│   ├── models.py
│   ├── schemas.py
│   ├── crud.py
│   ├── deps.py
│   ├── routers/
│   │   ├── users.py
│   │   ├── wallet.py
│   │   ├── tx.py
│   │   └── admin.py
│   ├── utils/
│   │   ├── tron.py
│   │   └── security.py
│   └── core/
│       ├── config.py
│       └── db.py
└── requirements.txt


⸻

8. Development Guidelines
	•	All database changes must use migrations (e.g. Alembic)
	•	Functions must be type-annotated and have clear docstrings.
	•	Use Pydantic schemas for request/response validation.
	•	API endpoints must be documented (docstrings or OpenAPI)
	•	Transaction logic must be atomic (use DB transactions)
	•	All blockchain interactions must be exception-handled and logged.
	•	Write unit tests for all critical business logic.

⸻

9. Implementation Steps (Checklist)
	1.	Set up FastAPI skeleton project and DB connection.
	2.	Implement user sign-up, login, JWT authentication.
	3.	Create balance and transaction models.
	4.	Implement internal transfer, transaction history.
	5.	Integrate Tron on-chain (tronpy): deposit monitoring, withdrawal.
	6.	Build admin functions for withdrawal approval, balance view.
	7.	Add logging, security, and error handling.
	8.	Prepare API documentation (OpenAPI/swagger).
	9.	Write sample tests for all core endpoints.

⸻

10. References
	•	FastAPI docs
	•	tronpy docs
	•	Pydantic docs
	•	Alembic migrations

⸻

End of Copilot instruction.
If you need more context, refer to the Notion document or ask Seyoung for service specifics.
All questions about requirements, edge-cases, or policy should be raised via project issue tracker.

⸻

복사-붙여넣기만 하면 바로 코파일럿에게 요청 가능한 형식입니다.
추가 요청/특이점/운영 정책 등 있으면 언제든 말씀해 주세요!