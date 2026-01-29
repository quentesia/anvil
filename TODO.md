# Anvil To-Do List

## Recently Completed 

- [X] **Interactive Mode**: Allow users to interactively approve or reject individual upgrade proposals.
- [X] **Rich Reporting**: Improve CLI output to show risk levels (Low/Medium/High) and summary reasoning for each package.
- [X] **Rollback Mechanism**: Create a safety net to revert changes if the upgrade causes test failures.
- [X] **Apply Updates**: Implement the actual execution of upgrade commands (`uv add`, `pip install --upgrade`).
- [X] **LangGraph Refactor**: Convert monolithic upgrader to modular state machine with independent nodes.

## Architecture & Workflow

- [ ] **Parallel Package Analysis**: Leverage LangGraph to analyze multiple packages concurrently (foundation is in place).
- [ ] **Additional AI Agents**: Add specialized agents (Security Auditor, Performance Analyzer, Dependency Resolver).
- [ ] **Resume Capability**: Save/restore workflow state to resume interrupted upgrades.
- [ ] **Workflow Visualization**: Generate visual diagrams of upgrade workflows for debugging.
- [ ] **Custom Node Plugins**: Allow users to add custom nodes to the workflow graph.

## Changelog & Source Retrieval

- [ ] **Manual Source Override**: Add a configuration option (CLI arg or config file) to manually specify the source URL for a package if detection fails or it's hosted elsewhere (e.g., private GitLab).
- [ ] **Expand Forge Support**: Add support for retrieving changelogs from GitLab and Bitbucket.
- [ ] **Changelog Parsing**: Implement logic to parse the raw text/markdown of a changelog to extract only the relevant version section.
- [ ] **Manual Package Ignore**: Add a configuration option (CLI arg or config file) to manually specify a list of packages to ignore.
- [ ] **Website Parsing AI**: Find out if there's a way to attach an AI that can open any links in the changelogs and parse them for more accurate analysis.

## AI Agent & Models

- [ ] **Model Normalization**: Dynamically configure the LLM provider and model parameters based on the provided API key (e.g., auto-select GPT-4o for OpenAI keys, Claude 3.5 for Anthropic keys).
- [ ] **Prompt Refinement**: Improve system prompts to better detect breaking changes and generate safer code migration suggestions.
- [ ] **Context Truncation**: Implement a more sophisticated context truncation strategy to handle long changelogs and codebases.
- [ ] **Security Agent**: Add AI agent for CVE scanning and security vulnerability assessment.
- [ ] **Performance Agent**: Add AI agent to predict performance impacts of upgrades.

## Core Upgrade Logic

- [ ] **Target Version Resolution**: Implement logic to determine the "best" next version to upgrade to (e.g., latest stable vs. next patch).
- [ ] **Profiling and Performance**: Add profiling and performance metrics to verify whether the upgrade process actually improves performance.
- [ ] **Graph Resolution Improvement**: Migrate the graph resolution code to Rust for better performance.
- [ ] **Conflict Resolution**: Smart handling of dependency conflicts with AI-powered resolution strategies.
- [ ] **Batch Upgrades**: Allow upgrading multiple packages in a single transaction with atomic rollback.

## Configuration & Customization

- [ ] **Configuration File**: Support `.anvil.toml` or `pyproject.toml [tool.anvil]` for project-specific settings.
- [ ] **Upgrade Policies**: Define policies (e.g., "only patch updates", "skip major versions", "auto-approve low-risk").
- [ ] **Hook System**: Allow pre/post upgrade hooks for custom validation or notifications.
- [ ] **CI/CD Integration**: Add examples and guides for integrating with GitHub Actions, GitLab CI, etc.

## CLI & UX

- [ ] **Dry Run Mode**: Enhanced dry-run that shows full analysis without any changes.
- [ ] **Progress Indicators**: Better progress feedback for long-running operations.
- [ ] **Verbose/Debug Modes**: Different logging levels for troubleshooting.
- [ ] **Export Reports**: Generate JSON/HTML reports of upgrade analysis and results.

## Testing & Quality

- [ ] **Integration Tests**: Add end-to-end tests for full upgrade workflows.
- [ ] **Mock Package Testing**: Create test fixtures for common upgrade scenarios.
- [ ] **Performance Benchmarks**: Track performance of analysis and upgrade operations.
- [ ] **Error Recovery Tests**: Test failure scenarios and rollback mechanisms.

## Documentation

- [ ] **Architecture Guide**: Document the LangGraph state machine and node system.
- [ ] **User Guide**: Write a comprehensive user guide for Anvil, including setup instructions, common workflows, and best practices.
- [ ] **API Documentation**: Document the public API of Anvil, including classes, methods, and configuration options.
- [ ] **Contributing Guide**: Add guidelines for contributors.
- [ ] **Publish v0.2.0 to PyPI**: Package and publish the refactored version.

## Future Ideas

- [ ] **Web Dashboard**: Create a web UI for monitoring and managing upgrades.
- [ ] **Team Collaboration**: Share upgrade analyses and decisions across teams.
- [ ] **Machine Learning**: Learn from past upgrade decisions to improve risk prediction.
- [ ] **Ecosystem Insights**: Aggregate anonymized data to provide ecosystem-wide upgrade recommendations.
