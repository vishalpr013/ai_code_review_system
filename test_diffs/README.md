# AI Code Review Test Diffs

This folder contains 20 git diff files with **progressively increasing complexity** for testing the AI Code Review System.

## Purpose
These diffs are designed to test the AI's ability to:
- Identify various types of code issues
- Assess severity levels correctly
- Provide meaningful feedback
- Handle complexity ranging from simple syntax errors to complex security vulnerabilities

## Complexity Progression

### Level 1-5: Basic Issues (Simple)
1. **diff_01_missing_semicolon.diff** - Simple syntax error
2. **diff_02_hardcoded_credentials.diff** - Security: Hardcoded credentials
3. **diff_03_sql_injection.diff** - Security: SQL injection vulnerability
4. **diff_04_missing_error_handling.diff** - Error handling removed
5. **diff_05_memory_leak.diff** - Resource management issue

### Level 6-10: Intermediate Issues (Moderate)
6. **diff_06_infinite_loop.diff** - Logic error causing infinite loop
7. **diff_07_race_condition.diff** - Concurrency issue
8. **diff_08_api_key_exposure.diff** - Frontend security vulnerability
9. **diff_09_poor_naming_conventions.diff** - Code quality/readability
10. **diff_10_no_input_validation.diff** - Missing validation

### Level 11-15: Advanced Issues (Complex)
11. **diff_11_code_duplication.diff** - DRY violation, maintenance issues
12. **diff_12_insecure_random.diff** - Cryptographic weakness
13. **diff_13_unencrypted_sensitive_data.diff** - Data protection violation
14. **diff_14_complex_cyclomatic_complexity.diff** - High complexity code
15. **diff_15_cors_vulnerability.diff** - CORS misconfiguration

### Level 16-20: Expert Issues (Very Complex)
16. **diff_16_xxe_injection.diff** - XML External Entity attack
17. **diff_17_timing_attack_vulnerability.diff** - Timing side-channel
18. **diff_18_command_injection.diff** - Shell injection vulnerability
19. **diff_19_deserialization_vulnerability.diff** - Insecure deserialization
20. **diff_20_complex_security_architecture.diff** - **MOST COMPLEX**: 10+ critical vulnerabilities in authentication system

## File Format

Each diff file follows this structure:
```
ERROR: [Brief description]
SEVERITY: [Low/Medium/High/Critical]
EXPECTED ISSUES: [What the AI should detect]

[Git diff content]
```

## Usage

To test the AI Code Review System:

1. **Individual Testing**: Upload each diff file separately to test specific issue detection
2. **Progressive Testing**: Upload in order (01 → 20) to test complexity handling
3. **Batch Testing**: Test multiple files to evaluate consistency
4. **Scoring Validation**: Verify AI scoring aligns with severity levels

## Expected AI Behavior

The AI should:
- ✅ Detect the primary error/vulnerability described at the top
- ✅ Provide severity assessment matching the indicated level
- ✅ Offer specific, actionable recommendations
- ✅ Score appropriately based on issue severity
- ✅ Handle complex scenarios (diff 20) with multiple issues

## Severity Mapping

| Severity | Expected Score Range | Examples |
|----------|---------------------|----------|
| Low | 7-9 | Formatting, minor style issues |
| Medium | 5-7 | Missing error handling, code quality |
| High | 3-5 | Resource leaks, logic errors, race conditions |
| Critical | 0-3 | Security vulnerabilities, data breaches |

## Security Issues Coverage

These diffs cover common OWASP Top 10 and CWE vulnerabilities:
- Injection (SQL, Command, XXE)
- Broken Authentication
- Sensitive Data Exposure
- Security Misconfiguration
- Insecure Deserialization
- Using Components with Known Vulnerabilities
- Insufficient Logging & Monitoring

## Notes

- Diffs show both "before" (secure/good) and "after" (vulnerable/bad) code
- Comments in diffs explain the specific vulnerability
- Real-world scenarios are simulated
- Multiple programming languages covered (Python, JavaScript)

## Testing Checklist

- [ ] Test each diff individually
- [ ] Verify AI detects primary issue
- [ ] Check severity scoring accuracy
- [ ] Validate recommendation quality
- [ ] Test complexity progression (simple → complex)
- [ ] Verify handling of diff_20 (most complex)
- [ ] Compare AI scores with expected ranges

## Created: October 29, 2025
## Version: 1.0
