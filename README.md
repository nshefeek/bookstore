# Bookstore API

Library Management System named Bookstore. A RESTFul API implementation using FastAPI, SQLAlchemy, and Postgres.
This system facilitates readers and librarians to manage operations such as book inventory, user management, and borrowing.


## Table of Contents

* [Functional Requirements](#functional-requirements)
* [Design Choices](#design-choices)
* [Tech Stack](#tech-stack)
* [Database Modelling](#database-modelling)
* [API Endpoints](#api-endpoints)
* [How to Setup and Run the Application](#how-to-setup-and-run-the-application)

## Functional Requirements

* User roles:
    * admin: Application superuser. First user is created during the initial database migrations. The credentials are set in the .env file.
    * librarian: Responsible for managing books in the library. Can create, read, update, and delete books and titles. Manage borrow requests and records.
    * reader: Regular user of the library. Can borrow books and view their details.
* Book inventory management
    * Librarians can create, read, update, and delete books and titles.
    * Books can be borrowed by readers.
* User management
    * Librarians can create, read, update, and delete users.
* Borrowing and returning of books
    * Readers can borrow books and return the borrowed books.
* Notification of borrow requests and returns
    * Librarians receive a notification when a borrow request is made or returned.
* Book search
    * Librarians and readers can search for books by title, author, category or other attributes.

## Design Choices

The system is designed to be RESTful and uses FastAPI as the API framework. It uses python type hints for code readability and uses pydantic models for validation of the request and response data.

The system is also designed to be modular and extensible. The application is broken down into individual apps or modules that can be run be developed further to run as individual services.

The application is divided into the following packages:

* auth: Authentication and Authorization
* books: Book related operations
* database: Database base models, mixins, connection and session management
* borrowing: Borrowing related operations
* notifications: Notification related operations
* users: User related operations - under implementation. 
* utils: Utility functions

Each package is structured as follows:

* `models`: Database models
* `routes`: API routes
* `services`: Business logic
* `repositories`: Repository layer for data persistence
* `dependencies`: Dependency injection
* `schemas`: Pydantic models for request and response data validation and serialization
* `utils`: Utility functions



## Tech Stack

The system uses the following tech stack:

* `FastAPI` as the API framework
* `Python` type hints for code readability
* `Pydantic` models for validation of the request and response data
* `SQLAlchemy` as the ORM
* `PostgreSQL` as the database
* `asyncpg` as the async postgres DBAPI
* `Redis` as the message broker, rate limiter and cache.
* `Alembic` for database migrations
* `uvicorn` as the ASGI server
* `structlog` as the logging library
* `uv` for dependency management and packaging
* `pytest` as the testing framework


## API Endpoints

The API provides the following endpoints:

* /auth/login: Login
* /auth/users: User related operations. Registration for individual users. Admin can manage users.
* /auth/token: Get a JWT token.
* /auth/me: Get details of the currently active user.
* /auth/users/{user_id}: Manage the details of a specific user. Admin can get details of any user, individual users can update their own details.
* /auth/api-keys: Manage API keys. Admin can create, read, update, and delete API keys. Individual users can create their own API keys.
* /auth/users/{user_id}/api-keys: Manage API keys for a specific user. Admin can create, read, update, and delete API keys for any user, individual users can create their own API keys.
* /books: Manage books. Admin/Librarians can create, read, update, and delete books. Readers can only view and search for books.
* /borrowing: Manage borrow requests. Readers can make borrow requests. Admin/Librarians can view all borrow requests, approve or reject borrow requests.



## Database Modelling

### Entities and Attributes

### 1. `users`
- **Columns:**
  - `id: UUID` (Primary Key)
  - `email: String` (Unique, Indexed)
  - `hashed_password: String` (Not Null)
  - `role: Enum(UserRole)` (Not Null, Default: "reader")
  - `is_active: Boolean` (Default: True)
  - `is_superuser: Boolean` (Default: False)
  - `created_at: TIMESTAMP` (Inherited from `TimeStampMixin`)
  - `updated_at: TIMESTAMP` (Inherited from `TimeStampMixin`)
- **Relationships:**
  - One-to-Many with `api_keys` (via `user_id`)

### 2. `api_keys`
- **Columns:**
  - `id: UUID` (Primary Key)
  - `user_id: UUID` (Foreign Key to `users.id`)
  - `api_key_hash: String` (Unique, Indexed, Not Null)
  - `name: String` (Not Null)
  - `is_active: Boolean` (Default: True)
  - `last_used_at: TIMESTAMP` (Nullable)
  - `last_used_ip: String` (Nullable)
  - `created_at: TIMESTAMP` (Inherited from `TimeStampMixin`)
  - `updated_at: TIMESTAMP` (Inherited from `TimeStampMixin`)
- **Constraints:**
  - Unique Constraint on (`user_id`, `name`)
- **Relationships:**
  - Many-to-One with `users` (via `user_id`)

### 3. `book_categories`
- **Columns:**
  - `id: UUID` (Primary Key)
  - `name: String` (Unique, Indexed, Not Null)
  - `description: String` (Nullable)
  - `created_at: TIMESTAMP` (Inherited from `TimeStampMixin`)
  - `updated_at: TIMESTAMP` (Inherited from `TimeStampMixin`)
- **Relationships:**
  - One-to-Many with `book_titles` (via `category_id`)

### 4. `book_titles`
- **Columns:**
  - `id: UUID` (Primary Key)
  - `title: String` (Indexed, Not Null)
  - `author: String` (Indexed, Not Null)
  - `isbn: String` (Unique, Indexed, Not Null)
  - `description: String` (Nullable)
  - `publisher: String` (Not Null)
  - `category_id: UUID` (Foreign Key to `book_categories.id`, Not Null)
  - `created_at: TIMESTAMP` (Inherited from `TimeStampMixin`)
  - `updated_at: TIMESTAMP` (Inherited from `TimeStampMixin`)
- **Relationships:**
  - Many-to-One with `book_categories` (via `category_id`)
  - One-to-Many with `books` (via `book_title_id`)

### 5. `books`
- **Columns:**
  - `id: UUID` (Primary Key)
  - `book_title_id: UUID` (Foreign Key to `book_titles.id`, Not Null)
  - `edition: String` (Not Null)
  - `published_year: Integer` (Not Null)
  - `barcode: String` (Unique, Indexed, Not Null)
  - `status: Enum(BookStatus)` (Not Null, Default: "available")
  - `created_at: TIMESTAMP` (Inherited from `TimeStampMixin`)
  - `updated_at: TIMESTAMP` (Inherited from `TimeStampMixin`)
- **Relationships:**
  - Many-to-One with `book_titles` (via `book_title_id`)
  - One-to-Many with `borrow_records` (via `book_id`)
  - One-to-Many with `book_requests` (via `book_id`)

### 6. `borrow_records`
- **Columns:**
  - `user_id: UUID` (Foreign Key to `users.id`, Primary Key)
  - `book_id: UUID` (Foreign Key to `books.id`, Primary Key)
  - `returned: Boolean` (Default: False)
  - `borrowed_date: TIMESTAMP` (Not Null, Default: `now()`)
  - `due_date: TIMESTAMP` (Not Null)
  - `return_date: TIMESTAMP` (Nullable, Updated: `now()`)
  - `status: Enum(BorrowStatus)` (Not Null, Default: "borrowed")
  - `created_at: TIMESTAMP` (Inherited from `TimeStampMixin`)
  - `updated_at: TIMESTAMP` (Inherited from `TimeStampMixin`)
- **Relationships:**
  - Many-to-One with `users` (via `user_id`)
  - Many-to-One with `books` (via `book_id`)

### 7. `book_requests`
- **Columns:**
  - `user_id: UUID` (Foreign Key to `users.id`, Primary Key)
  - `book_id: UUID` (Foreign Key to `books.id`, Primary Key)
  - `requested_at: TIMESTAMP` (Not Null, Default: `now()`)
  - `status: Enum(BookRequestStatus)` (Not Null, Default: "pending")
  - `created_at: TIMESTAMP` (Inherited from `TimeStampMixin`)
  - `updated_at: TIMESTAMP` (Inherited from `TimeStampMixin`)
- **Relationships:**
  - Many-to-One with `users` (via `user_id`)
  - Many-to-One with `books` (via `book_id`)

## Relationships Summary

1. **`users` ↔ `api_keys`**
   - One `user` can have many `api_keys`.
   - One `api_key` belongs to one `user`.

2. **`book_categories` ↔ `book_titles`**
   - One `book_category` can have many `book_titles`.
   - One `book_title` belongs to one `book_category`.

3. **`book_titles` ↔ `books`**
   - One `book_title` can have many `books` (copies).
   - One `book` belongs to one `book_title`.

4. **`users` ↔ `borrow_records`**
   - One `user` can have many `borrow_records`.
   - One `borrow_record` is associated with one `user`.

5. **`books` ↔ `borrow_records`**
   - One `book` can have many `borrow_records`.
   - One `borrow_record` is associated with one `book`.

6. **`users` ↔ `book_requests`**
   - One `user` can have many `book_requests`.
   - One `book_request` is associated with one `user`.

7. **`books` ↔ `book_requests`**
   - One `book` can have many `book_requests`.
   - One `book_request` is associated with one `book`.

## Textual ERD Representation

```
[users] ---1:N---> [api_keys]
  |                   |
  |                   +--> user_id (FK)
  |
  +---1:N---> [borrow_records] <---N:1--- [books]
  |              |      |                   |
  |              +------+-------------------+
  |              |      |                   |
  +---1:N---> [book_requests] <---N:1--- [books]
                                       |
[book_categories] ---1:N---> [book_titles]
                        |
                        +--> N:1 --- [books]
```

## How to Setup and Run the Application

### Local Development

* Prerequisites:
  - Python 3.10 or higher
  - Postgres
  - Git
  - Docker and docker compose
  - uv for dependency management and packaging

1. Clone the repository
```bash
git clone https://github.com/nshefeek/bookstore.git
```

2. Enter the repository
```bash
cd bookstore
```

3. Create and activate a virtual environment
```bash
uv venv .venv
source .venv/bin/activate
```

4. Install dependencies
```bash
uv sync
```

5. Configure the .env file
   - Fill in the values for the following variables
   ```
   - DATABASE_HOST
   - DATABASE_PASSWORD
   - DATABASE_USER
   - DATABASE_NAME
   - DATABASE_PORT
   - REDIS_HOST
   - REDIS_PORT
   - REDIS_PASSWORD
   - JWT_SECRET_KEY
   - JWT_ALGORITHM
   - JWT_ACCESS_TOKEN_EXPIRE_MINUTES
   - ADMIN_PASSWORD
   - ADMIN_EMAIL
   ```

6. Build and install the application
```bash
uv build
```

7. Run alembic migrations to create the first user and database tables.
```bash
alembic upgrade head
```

8. Run the application
```bash
uvicorn bookstore.main:app --reload
```

### Docker Compose

1. Setup the .env.docker file (same as .env file)

2. Build and run the application
```bash
docker compose up --build -d
```

3. Run alembic migrations to create the first user and database tables.
```bash
docker exec -it bookstore-app-1 sh -c "alembic upgrade head"
```
