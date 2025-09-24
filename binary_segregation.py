def getMaxCost(s):
    """
    Calculate the maximum possible cost to segregate a binary string.
    
    Rules:
    - A "1" can be moved to the right until it reaches the end or another "1"
    - Cost = 1 + number of places moved
    - Each "1" must be moved to its maximum possible position
    
    The strategy is to maximize the total cost by ensuring each '1' moves as far as possible.
    We can do this by moving '1's one step at a time to maximize the number of operations.
    
    Args:
        s (str): Binary string containing only '0' and '1'
    
    Returns:
        int: Maximum possible cost to segregate the string
    """
    n = len(s)
    ones_count = s.count('1')
    
    if ones_count == 0:
        return 0
    
    # Convert to list for easier manipulation
    arr = list(s)
    total_cost = 0
    
    # Move each '1' to its maximum possible position
    # We'll process from left to right and move each '1' as far right as possible
    for i in range(n):
        if arr[i] == '1':
            # Find the rightmost position this '1' can move to
            # It can move until it hits another '1' or the end
            j = i
            while j < n - 1 and arr[j + 1] != '1':
                # Move this '1' one position to the right
                arr[j], arr[j + 1] = arr[j + 1], arr[j]
                j += 1
                total_cost += 1 + 1  # Cost = 1 + distance (distance = 1 for each step)
    
    return total_cost


def getMaxCostOptimized(s):
    """
    Optimized version that calculates cost without explicitly tracking positions.
    """
    n = len(s)
    total_cost = 0
    ones_count = 0
    
    # Process from right to left
    for i in range(n - 1, -1, -1):
        if s[i] == '1':
            # This '1' can move to position (n - 1 - ones_count)
            # Distance = (n - 1 - ones_count) - i
            distance = (n - 1 - ones_count) - i
            if distance > 0:
                total_cost += 1 + distance
            ones_count += 1
    
    return total_cost


# Test with the provided example
if __name__ == "__main__":
    # Test case from the problem
    s = "110100"
    result = getMaxCost(s)
    print(f"Input: {s}")
    print(f"Maximum cost: {result}")
    
    # Test with optimized version
    result_opt = getMaxCostOptimized(s)
    print(f"Optimized result: {result_opt}")
    
    # Additional test cases
    test_cases = [
        "110100",  # Expected: 13
        "111000",  # All 1s at start
        "000111",  # All 1s at end
        "101010",  # Alternating
        "100000",  # Single 1 at start
        "000001",  # Single 1 at end
        "111111",  # All 1s
        "000000",  # All 0s
    ]
    
    print("\nTesting additional cases:")
    for test in test_cases:
        cost = getMaxCost(test)
        cost_opt = getMaxCostOptimized(test)
        print(f"{test}: {cost} (both methods: {cost == cost_opt})")
