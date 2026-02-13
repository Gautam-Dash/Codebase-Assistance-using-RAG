"""Authentication module for handling user authentication."""


class AuthenticationError(Exception):
    """Raised when authentication fails."""
    pass


def verify_password(password: str, hashed: str) -> bool:
    """
    Verify a password against its hash.
    
    Args:
        password: The plaintext password
        hashed: The hashed password
        
    Returns:
        True if password matches, False otherwise
    """
    # Simple demo - in production use bcrypt
    return password == hashed


def authenticate_user(username: str, password: str) -> dict:
    """
    Authenticate a user.
    
    Args:
        username: The username
        password: The password
        
    Returns:
        Dictionary with user info if successful
        
    Raises:
        AuthenticationError: If authentication fails
    """
    # Demo user database
    users = {
        "admin": "admin123",
        "user": "password456"
    }
    
    if username not in users:
        raise AuthenticationError(f"User {username} not found")
    
    if not verify_password(password, users[username]):
        raise AuthenticationError("Invalid password")
    
    return {
        "username": username,
        "authenticated": True,
        "role": "admin" if username == "admin" else "user"
    }


class SessionManager:
    """Manages user sessions."""
    
    def __init__(self):
        """Initialize session manager."""
        self.sessions = {}
    
    def create_session(self, username: str, token: str) -> None:
        """Create a new session."""
        self.sessions[token] = {
            "username": username,
            "active": True
        }
    
    def validate_session(self, token: str) -> bool:
        """Validate a session token."""
        return token in self.sessions and self.sessions[token]["active"]
    
    def destroy_session(self, token: str) -> None:
        """Destroy a session."""
        if token in self.sessions:
            self.sessions[token]["active"] = False
