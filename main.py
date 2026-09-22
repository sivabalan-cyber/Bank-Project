import os
import hashlib
import hmac
import secrets

from fastapi import FastAPI, Request, Form
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware

from database import conn, cursor


app = FastAPI()
app.add_middleware(
    SessionMiddleware,
    secret_key=os.getenv("BANK_SESSION_SECRET", secrets.token_hex(32)),
    https_only=False,
)

templates = Jinja2Templates(directory="templates")

app.mount(
    "/static",
    StaticFiles(directory="static"),
    name="static"
)


def hash_password(password: str) -> str:
    salt = secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac(
        "sha256", password.encode(), salt.encode(), 120000
    ).hex()
    return f"pbkdf2_sha256${salt}${digest}"


def password_matches(password: str, stored_password: str) -> bool:
    if stored_password.startswith("pbkdf2_sha256$"):
        _, salt, expected_digest = stored_password.split("$", 2)
        actual_digest = hashlib.pbkdf2_hmac(
            "sha256", password.encode(), salt.encode(), 120000
        ).hex()
        return hmac.compare_digest(actual_digest, expected_digest)

    return hmac.compare_digest(password, stored_password)


def redirect_to_login():
    return RedirectResponse("/login", status_code=303)


def require_admin(request: Request):
    if request.session.get("role") != "admin":
        return redirect_to_login()
    return None


def require_customer(request: Request):
    if request.session.get("role") != "customer":
        return redirect_to_login()
    return None


# -----------------------------------
# HOME PAGE
# -----------------------------------

@app.get("/")
def home(request: Request):

    if not request.session.get("role"):
        return redirect_to_login()

    if request.session["role"] == "customer":
        cursor.execute(
            "SELECT * FROM accounts WHERE account_holder=%s",
            (request.session["holder"],)
        )
    else:
        cursor.execute("SELECT * FROM accounts")

    accounts = cursor.fetchall()

    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={
            "accounts": accounts,
            "role": request.session["role"],
            "holder": request.session.get("holder")
        }
    )


# -----------------------------------
# LOGIN AND LOGOUT
# -----------------------------------

@app.get("/login")
def login_page(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="login.html",
        context={
            "error": request.query_params.get("error"),
            "login_type": request.query_params.get("type", "admin")
        }
    )


@app.post("/login")
def login(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    login_type: str = Form("admin")
):
    expected_username = os.getenv("BANK_ADMIN_USERNAME", "admin")
    expected_password = os.getenv("BANK_ADMIN_PASSWORD", "admin123")

    if login_type == "customer":
        cursor.execute(
            "SELECT account_holder, pin FROM accounts WHERE account_holder=%s",
            (username,)
        )
        account = cursor.fetchone()
        if not account or not password_matches(password, account[1]):
            return RedirectResponse(
                "/login?type=customer&error=Invalid%20customer%20username%20or%20password",
                status_code=303
            )

        if not account[1].startswith("pbkdf2_sha256$"):
            cursor.execute(
                "UPDATE accounts SET pin=%s WHERE account_holder=%s",
                (hash_password(password), username)
            )
            conn.commit()

        request.session.clear()
        request.session.update({"role": "customer", "holder": username})
        return RedirectResponse("/", status_code=303)

    if username != expected_username or password != expected_password:
        return RedirectResponse(
            "/login?type=admin&error=Invalid%20admin%20username%20or%20password",
            status_code=303
        )

    request.session.clear()
    request.session["role"] = "admin"
    return RedirectResponse("/", status_code=303)


@app.post("/customer/register")
def register_customer(
    holder: str = Form(...),
    password: str = Form(...),
    confirm_password: str = Form(...)
):
    holder = holder.strip()

    if len(holder) < 2 or len(password) < 4:
        return RedirectResponse(
            "/login?type=customer&register_error=Name%20and%20password%20must%20be%20valid",
            status_code=303
        )

    if password != confirm_password:
        return RedirectResponse(
            "/login?type=customer&register_error=Passwords%20do%20not%20match",
            status_code=303
        )

    cursor.execute(
        "SELECT account_holder FROM accounts WHERE account_holder=%s",
        (holder,)
    )
    if cursor.fetchone():
        return RedirectResponse(
            "/login?type=customer&register_error=Account%20already%20exists",
            status_code=303
        )

    cursor.execute(
        "INSERT INTO accounts (account_holder, pin, balance) VALUES (%s, %s, %s)",
        (holder, hash_password(password), 0)
    )
    conn.commit()

    return RedirectResponse(
        "/login?type=customer&registered=1",
        status_code=303
    )


@app.get("/logout")
def logout(request: Request):
    request.session.clear()
    return RedirectResponse("/login", status_code=303)


# -----------------------------------
# ACCOUNT AND TRANSACTION PAGES
# -----------------------------------

@app.get("/accounts/new")
def new_account_page(request: Request):
    if (response := require_admin(request)):
        return response
    return RedirectResponse("/", status_code=303)


@app.get("/transactions/deposit")
def deposit_page(request: Request):
    if (response := require_customer(request)):
        return response
    return templates.TemplateResponse(
        request=request,
        name="transaction_form.html",
        context={
            "title": "Deposit Money",
            "description": "Add money to an existing account.",
            "action": "/deposit",
            "button": "Deposit",
            "error": request.query_params.get("error")
        }
    )


@app.get("/transactions/withdraw")
def withdraw_page(request: Request):
    if (response := require_customer(request)):
        return response
    return templates.TemplateResponse(
        request=request,
        name="transaction_form.html",
        context={
            "title": "Withdraw Money",
            "description": "Withdraw money without exceeding the account balance.",
            "action": "/withdraw",
            "button": "Withdraw",
            "error": request.query_params.get("error")
        }
    )


# -----------------------------------
# CREATE ACCOUNT
# -----------------------------------

@app.post("/add")
def add_account(
    request: Request,
    holder: str = Form(...),
    pin: str = Form(...),
    balance: float = Form(...)
):
    if (response := require_admin(request)):
        return response
    return RedirectResponse("/", status_code=303)

    cursor.execute(
        "SELECT * FROM accounts WHERE account_holder=%s",
        (holder,)
    )

    if cursor.fetchone():
        return RedirectResponse(
            "/accounts/new?error=Account%20already%20exists",
            status_code=303
        )

    cursor.execute(
        """
        INSERT INTO accounts (account_holder, pin, balance)
        VALUES (%s, %s, %s)
        """,
        (holder, hash_password(pin), balance)
    )

    conn.commit()

    return RedirectResponse(
        "/",
        status_code=303
    )


@app.post("/deposit")
def deposit(request: Request, amount: float = Form(...)):
    if (response := require_customer(request)):
        return response
    holder = request.session["holder"]
    if amount <= 0:
        return RedirectResponse(
            "/transactions/deposit?error=Amount%20must%20be%20greater%20than%20zero",
            status_code=303
        )

    cursor.execute(
        "UPDATE accounts SET balance = balance + %s WHERE account_holder=%s",
        (amount, holder)
    )

    if cursor.rowcount == 0:
        return RedirectResponse(
            "/transactions/deposit?error=Account%20not%20found",
            status_code=303
        )

    conn.commit()
    return RedirectResponse("/", status_code=303)


@app.post("/withdraw")
def withdraw(request: Request, amount: float = Form(...)):
    if (response := require_customer(request)):
        return response
    holder = request.session["holder"]
    if amount <= 0:
        return RedirectResponse(
            "/transactions/withdraw?error=Amount%20must%20be%20greater%20than%20zero",
            status_code=303
        )

    cursor.execute(
        """
        UPDATE accounts
        SET balance = balance - %s
        WHERE account_holder=%s AND balance >= %s
        """,
        (amount, holder, amount)
    )

    if cursor.rowcount == 0:
        return RedirectResponse(
            "/transactions/withdraw?error=Account%20not%20found%20or%20insufficient%20balance",
            status_code=303
        )

    conn.commit()
    return RedirectResponse("/", status_code=303)


# -----------------------------------
# UPDATE ACCOUNT
# -----------------------------------

@app.post("/update")
def update_account(
    request: Request,
    holder: str = Form(...),
    pin: str = Form(...),
    balance: float = Form(...)
):
    if (response := require_admin(request)):
        return response
    return RedirectResponse("/", status_code=303)

    cursor.execute(
        """
        UPDATE accounts
        SET pin=%s,
            balance=%s
        WHERE account_holder=%s
        """,
        (hash_password(pin), balance, holder)
    )

    conn.commit()

    return RedirectResponse(
        "/",
        status_code=303
    )


# -----------------------------------
# DELETE ACCOUNT
# -----------------------------------

@app.get("/delete/{holder}")
def delete_account(request: Request, holder: str):
    if (response := require_admin(request)):
        return response
    return RedirectResponse("/", status_code=303)

    cursor.execute(
        "DELETE FROM accounts WHERE account_holder=%s",
        (holder,)
    )

    conn.commit()

    return RedirectResponse(
        "/",
        status_code=303
    )
