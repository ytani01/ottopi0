#
# (c) 2025 Yoichi Tanibayashi
#
class Calc:
    """Calc."""

    def add(self, a: float, b: float) -> float:
        """Add function."""
        print(self.__class__.__name__)
        return a + b

    def sub(self, a: float, b: float) -> float:
        """Sample function."""
        return a - b

    def calc(self, func: str, a: float, b: float) -> float:
        """Calc."""

        if func == "add":
            return self.add(a, b)

        if func == "sub":
            return self.sub(a, b)

        return 0.0
