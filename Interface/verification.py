def verifyTool(data):
    if isinstance(data, int):
        # Handle the case where data is an integer
        dataString = str(data)
        
        # Check 1: Maximum value length check
        # Verify that the value does not have a length greater than 10
        if len(dataString) > 10:
            return 'Maximum value length exceeded'
        
        # Check 2: Data type check
        # Verify that the value is of integer type
        if not isinstance(dataString, int):
            return 'Invalid data type'

        # If all checks pass, return None (indicating success)
        return None

    # Convert data to strings
    dataStrings = [str(value) for value in data]

    # Check 1: Minimum length check
    # Verify that the data has at least 1 element
    if len(dataStrings) == 0:
        return 'Data has no elements'

    # Check 2: Negative value check
    # Verify that none of the values in the data are negative
    if any(value < 0 for value in dataStrings):
        return 'Negative values present'

    # Check 3: Maximum value length check
    # Verify that none of the values in the data have a length greater than 10
    if any(len(value) > 10 for value in dataStrings):
        return 'Maximum value length exceeded'

