# SELFHEAL AI – Demo: Buggy Python file
# Bugs present:
#  1. Missing import (numpy not in requirements)
#  2. Division by zero
#  3. Inefficient O(n²) bubble sort instead of built-in O(n log n)
#  4. Hardcoded API key (security issue)

import numpy as np          # ← ModuleNotFoundError if not installed
import requests

SECRET_API_KEY = "hardcoded_key_12345"  # ← Security: hardcoded secret

def bubble_sort(arr):
    """O(n²) bubble sort – intentionally inefficient"""
    n = len(arr)
    for i in range(n):
        for j in range(0, n - i - 1):
            if arr[j] > arr[j + 1]:
                arr[j], arr[j + 1] = arr[j + 1], arr[j]
    return arr

def calculate_average(numbers):
    total = sum(numbers)
    count = len(numbers)
    return total / count      # ← ZeroDivisionError when list is empty

data = [64, 34, 25, 12, 22, 11, 90]
sorted_data = bubble_sort(data)
print("Sorted:", sorted_data)

empty = []
avg = calculate_average(empty)  # ← This will crash!
print("Average:", avg)
