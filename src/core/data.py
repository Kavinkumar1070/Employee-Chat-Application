from passlib.context import CryptContext

# Define the password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

# Password to hash
password = "adminpass123"

# Hash the password
hashed_password = hash_password(password)

print("Hashed password:", hashed_password)
