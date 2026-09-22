import os

from fastapi import FastAPI, Request, Form
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles

from database import conn, cursor


app = FastAPI()

templates = Jinja2Templates(directory="templates")

app.mount(
    "/static",
    StaticFiles(directory="static"),
    name="static"
)


# -----------------------------------
# HOME PAGE
# -----------------------------------

@app.get("/")
def home(request: Request):

    cursor.execute("SELECT * FROM accounts")

    accounts = cursor.fetchall()

    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={"accounts": accounts}
    )


# -----------------------------------
# LOGIN AND LOGOUT
# -----------------------------------

@app.get("/login")
def login_page(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="login.html",
        context={"error": request.query_params.get("error")}
    )


@app.post("/login")
def login(username: str = Form(...), password: str = Form(...)):
    expected_username = os.getenv("BANK_ADMIN_USERNAME", "admin")
    expected_password = os.getenv("BANK_ADMIN_PASSWORD", "admin123")

    if username != expected_username or password != expected_password:
        return RedirectResponse(
            "/login?error=Invalid%20username%20or%20password",
            status_code=303
        )

    return RedirectResponse("/", status_code=303)


@app.get("/logout")
def logout():
    return RedirectResponse("/login", status_code=303)


# -----------------------------------
# ACCOUNT AND TRANSACTION PAGES
# -----------------------------------

@app.get("/accounts/new")
def new_account_page(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="account_form.html",
        context={"error": request.query_params.get("error")}
    )


@app.get("/transactions/deposit")
def deposit_page(request: Request):
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
    holder: str = Form(...),
    pin: str = Form(...),
    balance: float = Form(...)
):

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
        (holder, pin, balance)
    )

    conn.commit()

    return RedirectResponse(
        "/",
        status_code=303
    )


@app.post("/deposit")
def deposit(holder: str = Form(...), amount: float = Form(...)):
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
def withdraw(holder: str = Form(...), amount: float = Form(...)):
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
    holder: str = Form(...),
    pin: str = Form(...),
    balance: float = Form(...)
):

    cursor.execute(
        """
        UPDATE accounts
        SET pin=%s,
            balance=%s
        WHERE account_holder=%s
        """,
        (pin, balance, holder)
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
def delete_account(holder: str):

    cursor.execute(
        "DELETE FROM accounts WHERE account_holder=%s",
        (holder,)
    )

    conn.commit()

    return RedirectResponse(
        "/",
        status_code=303
    )
