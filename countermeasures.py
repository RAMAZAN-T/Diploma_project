# countermeasures.py

def get_countermeasure():
    return """
    Countermeasures for Common Web Vulnerabilities:

    SQL Injection:
    - Use prepared statements and parameterized queries.
    - Sanitize all input data rigorously.

    XSS (Cross-Site Scripting):
    - Sanitize and validate all user inputs to ensure they are not executable code.
    - Use Content Security Policy (CSP) to reduce the severity of any XSS vulnerabilities that do occur.

    Always ensure your web applications are updated and follow the latest security practices.
    """
