from smolagents import Tool

class CalculatorTool(Tool):
    name = "calculator_tool"
    description = """Performs calculations using Python's eval() function. 
    Returns the result of the calculation or an error message."""
    inputs = {
        "expression": {
            "type": "string",
            "description": "The mathematical expression to evaluate."
        }
    }
    output_type = "string"

    def forward(self, expression: str) -> str:
        try:
            # Use eval() to calculate the result of the expression
            result = eval(expression)
            return str(result)
        except Exception as e:
            return f"Error: Calculation failed with error: {e}"

if __name__ == "__main__":
    # Create an instance of the calculator tool
    calculator_tool = CalculatorTool()

    # Test with a simple calculation
    test_expression = "2 + 2 * 3"
    print(f"\nEvaluating expression: {test_expression}\n")

    try:
        result = calculator_tool.forward(test_expression)
        print("Calculation Result:")
        print("-" * 50)
        print(result)
    except ValueError as e:
        print(f"Error: {e}") 