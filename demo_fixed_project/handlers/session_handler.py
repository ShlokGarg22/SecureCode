import json

def restore_session(raw_json_str):
    # REMEDIATED: Safe JSON deserialization instead of pickle
    return json.loads(raw_json_str)

def calculate_formula(user_expression):
    # REMEDIATED: Safe literal evaluation
    import ast
    return ast.literal_eval(user_expression)
