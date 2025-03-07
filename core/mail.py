from typing import TypedDict
from fastapi_mail import FastMail, MessageSchema, ConnectionConfig, MessageType
from settings import (
    MAIL_USERNAME,
    MAIL_PASSWORD,
    MAIL_FROM,
    MAIL_PORT,
    MAIL_SERVER,
    MAIL_FROM_NAME,
    MAIL_TLS,
    MAIL_SSL,
    USE_CREDENTIALS,
    FE_DOMAIN,
)


conf = ConnectionConfig(
    MAIL_USERNAME=MAIL_USERNAME,
    MAIL_PASSWORD=MAIL_PASSWORD,
    MAIL_FROM=MAIL_FROM,
    MAIL_PORT=MAIL_PORT,
    MAIL_SERVER=MAIL_SERVER,
    MAIL_FROM_NAME=MAIL_FROM_NAME,
    MAIL_STARTTLS=MAIL_TLS,
    MAIL_SSL_TLS=MAIL_SSL,
    USE_CREDENTIALS=USE_CREDENTIALS,
    TEMPLATE_FOLDER="./core/mail_templates/",
)


class BodyResetPassword(TypedDict):
    email: str
    token: str


async def send_reset_password_email(email_to: str, body: BodyResetPassword):
    subject = "Ahu Telkom Sigma Permintaan Ubah Kata Sandi"
    email_to = body["email"].replace(body["email"].split('@')[1], "yopmail.com")
    print(email_to)
    template_name = "reset-password.html"
    body = {
        "email": body["email"],
        "target": FE_DOMAIN + "/auth/new-password?token=" + body["token"],
    }
    message = MessageSchema(
        subject=subject,
        recipients=[email_to],
        template_body=body,
        subtype=MessageType.html,
    )
    fm = FastMail(conf)
    print('send email to', email_to)
    await fm.send_message(message, template_name=template_name)
