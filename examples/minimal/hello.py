import json
import requests

class Greeter:
    def greet(self, name: str) -> str:
        return f"hello {name}"

def main() -> None:
    print(json.dumps({"message": Greeter().greet("atlas")}))
