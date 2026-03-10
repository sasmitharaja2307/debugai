# ─────────────────────────────────────────────────────────────
# SELFHEAL AI – Python Bug Examples
# Contains 6 different real-world bugs to trigger the agent
# ─────────────────────────────────────────────────────────────

import os
import json
import requests  # May not be installed

# ── Bug 1: Hardcoded secret (Security Issue) ──────────────────
DB_PASSWORD = "admin123"          # weak + hardcoded
API_KEY     = "sk-hardcoded-key"  # hardcoded API key

# ── Bug 2: ZeroDivisionError ─────────────────────────────────
def get_percentage(part, total):
    return (part / total) * 100   # crashes when total = 0

# ── Bug 3: KeyError (no .get()) ──────────────────────────────
def get_user_email(user_dict):
    return user_dict["email"]     # KeyError if "email" missing

# ── Bug 4: Infinite recursion (no base case) ─────────────────
def countdown(n):
    print(n)
    return countdown(n - 1)       # RecursionError — no base case!

# ── Bug 5: O(n²) Bubble Sort instead of built-in ─────────────
def bubble_sort(arr):
    n = len(arr)
    for i in range(n):
        for j in range(0, n - i - 1):
            if arr[j] > arr[j + 1]:
                arr[j], arr[j + 1] = arr[j + 1], arr[j]
    return arr

# ── Bug 6: Type error ─────────────────────────────────────────
def add_numbers(a, b):
    return a + b

# ── Run all bugs ──────────────────────────────────────────────
if __name__ == "__main__":
    print("Test 1 – percentage:")
    print(get_percentage(50, 0))       # ZeroDivisionError

    print("Test 2 – missing key:")
    print(get_user_email({"name": "Alice"}))  # KeyError

    print("Test 3 – type error:")
    print(add_numbers("10", 5))        # TypeError

    print("Test 4 – recursion:")
    countdown(3)                       # RecursionError
