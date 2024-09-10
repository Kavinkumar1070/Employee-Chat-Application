from fastapi import HTTPException
from datetime import datetime, timedelta
import random
import hashlib
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from pydantic import EmailStr
import string
from dotenv import load_dotenv
import os
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


load_dotenv()


def normalize_string(value: str) -> str:

    if isinstance(value, str):
        return value.strip().lower()


def generate_password(suffix: str = "@cds", length: int = 4) -> str:

    digits = "".join(random.choices(string.digits, k=length))

    password = f"{digits}{suffix}"
    return password


async def send_email(
    recipient_email: EmailStr, name: str, lname: str, Email: str, Password: str
):

    sender_email = os.getenv("SENDER_EMAIL")
    password = os.getenv("EMAIL_PASSWORD")
    subject = "User Details"
    body = f"Hi 'Mrs.{name} {lname}' \n Your Email_id: {Email} \n Your Password is:{Password} "
    message = MIMEMultipart()
    message["From"] = sender_email
    message["To"] = recipient_email
    message["Subject"] = subject
    message.attach(MIMEText(body, "plain"))
    try:
        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()
            server.login(sender_email, password)
            server.sendmail(sender_email, recipient_email, message.as_string())
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to send OTP email: {str(e)}",
            headers={"message": "OTP Send"},
        )


async def send_email_leave(
    recipient_email: EmailStr,
    name: str,
    lname: str,
    Leave_id: int,
    reason: str,
    status: str,
    other_entires:list
):

    sender_email = os.getenv("SENDER_EMAIL")
    password = os.getenv("EMAIL_PASSWORD")
    subject = "User Details"
    body = f"Hi 'Mrs.{name} {lname}' \n Your leave_id is : {" "}{Leave_id} \n Leave_status:{" "} {status} \n Your reason is:{" "} {reason}  \n Other_entires:{" "} {other_entires}"
    message = MIMEMultipart()
    message["From"] = sender_email
    message["To"] = recipient_email
    message["Subject"] = subject
    message.attach(MIMEText(body, "plain"))
    try:
        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()
            server.login(sender_email, password)
            server.sendmail(sender_email, recipient_email, message.as_string())
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to send OTP email: {str(e)}",
            headers={"message": "OTP Send"},
        )


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)
