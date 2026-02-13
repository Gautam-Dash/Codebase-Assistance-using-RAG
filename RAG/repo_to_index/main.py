"""Main application module."""


def greet(name: str) -> str:
    """
    Greet a user by name.
    
    Args:
        name: The user's name
        
    Returns:
        A greeting message
    """
    return f"Hello, {name}!"


def add(a: int, b: int) -> int:
    """Add two numbers."""
    return a + b


def multiply(a: int, b: int) -> int:
    """Multiply two numbers."""
    return a * b


class Calculator:
    """A simple calculator class."""
    
    def __init__(self):
        """Initialize the calculator."""
        self.result = 0
    
    def add(self, x: int) -> None:
        """Add to result."""
        self.result += x
    
    def multiply(self, x: int) -> None:
        """Multiply result."""
        self.result *= x
    
    def get_result(self) -> int:
        """Get current result."""
        return self.result


if __name__ == "__main__":
    print(greet("World"))
    print(f"2 + 3 = {add(2, 3)}")
    print(f"2 * 3 = {multiply(2, 3)}")
    
    calc = Calculator()
    calc.add(5)
    calc.multiply(3)
    print(f"Calculator result: {calc.get_result()}")
