from anvil.agent.brain import RiskAssessor

def test_brain_migration():
    print("Initializing RiskAssessor...")
    brain = RiskAssessor()
    
    changelog = """
    ## Release 2.0.0
    - BREAKING: Renamed `old_func()` to `new_func()`.
    - Deprecated `legacy_api`.
    """

    print("\n--- Scenario: Migration Guide Generation ---")
    # User uses `old_func`, so this is High Risk and needs migration.
    usages = ["dummy_pkg.old_func()", "dummy_pkg.legacy_api"]
    
    assessment = brain.assess_changelog(
        "dummy-pkg", "1.0.0", "2.0.0", changelog,
        usage_context=usages,
        python_version="3.11.5"
    )
    
    if assessment:
         print(f"VERDICT: {assessment.risk_score}")
         print(f"Reason: {assessment.justification}")
         print("-" * 40)
         if assessment.migration_guide:
             print("MIGRATION GUIDE GENERATED:")
             print(assessment.migration_guide)
         else:
             print("NO MIGRATION GUIDE FOUND.")

if __name__ == "__main__":
    test_brain_migration()
