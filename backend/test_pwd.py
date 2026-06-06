from auth import hash_password
from auth import verify_password

password = "meadmin07"

hashed = hash_password(password)

print("Hash:", hashed)

print(
    verify_password(
        password,
        hashed
    )
)