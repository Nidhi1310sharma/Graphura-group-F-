import logging
# Silence passlib's internal version-checking complaints
logging.getLogger("passlib").setLevel(logging.ERROR)

from passlib.context import CryptContext

pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto"
)

password = "meadmin07"

hashed_password = pwd_context.hash(password)
print("hashcode: ")
print(hashed_password)