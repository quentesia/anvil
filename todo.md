# Anvil To-Do List

## Changelog & Source Retrieval

- [ ] **Manual Source Override**: Add a configuration option (CLI arg or config file) to manually specify the source URL for a package if detection fails or it's hosted elsewhere (e.g., private GitLab).
- [ ] **Expand Forge Support**: Add support for retrieving changelogs from GitLab and Bitbucket.
- [ ] **Changelog Parsing**: Implement logic to parse the raw text/markdown of a changelog to extract only the relevant version section.
- [ ] **Manual Package Ignore**: Add a configuration option (CLI arg or config file) to manually specify a list of packages to ignore.
- [ ] **Website Parsing AI**: Find out if there's a way to attach an AI that can open any links in the changelogs and parse them for more accurate analysis.

## AI Agent & Models

- [ ] **Model Normalization**: Dynamically configure the LLM provider and model parameters based on the provided API key (e.g., auto-select GPT-4o for OpenAI keys, Claude 3.5 for Anthropic keys).
- [ ] **Connect Agent Brain**: Integrate the `AgentState` and LangGraph workflow into the main `Upgrader` loop to perform actual analysis.
- [ ] **Prompt Refinement**: Improve system prompts to better detect breaking changes and generate safer code migration suggestions.
- [ ] **Context Truncation**: Implement a more sophisticated context truncation strategy to handle long changelogs and codebases.

## Core Upgrade Logic

- [ ] **Target Version Resolution**: Implement logic to determine the "best" next version to upgrade to (e.g., latest stable vs. next patch).
- [ ] **Apply Updates**: Implement the actual execution of upgrade commands (`uv add`, `pip install --upgrade`).
- [ ] **Rollback Mechanism**: Create a safety net to revert changes if the upgrade causes impactful breaking changes or test failures.
- [] **Profiling and Performance**: Add profiling and performance metrics to verify whether the upgrade process actually improves performance. 
- [ ] **Graph Resolution Improvement**: Migrate the graph resolution code to Rust for better performance.

## CLI & UX

- [X] **Interactive Mode**: Allow users to interactively approve or reject individual upgrade proposals.
- [X] **Rich Reporting**: Improve CLI output to show risk levels (Low/Medium/High) and summary reasoning for each package.

## Documentation

- [ ] **User Guide**: Write a comprehensive user guide for Anvil, including setup instructions, common workflows, and best practices.
- [ ] **API Documentation**: Document the public API of Anvil, including classes, methods, and configuration options.
- [ ] Publish v0.1.0 to PyPI (pyproject.toml + twine)
