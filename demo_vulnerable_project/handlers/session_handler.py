import pickle
import ast

def restore_session(raw_bytes):
    # VULNERABILITY: Insecure Deserialization via pickle
    user_session = pickle.loads(raw_bytes)
    return user_session

def calculate_formula(user_expression):
    # VULNERABILITY: Code Injection via eval
    return eval(user_expression)
