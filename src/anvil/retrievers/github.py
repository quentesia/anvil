import requests
import base64
import os
from typing import Optional
from anvil.retrievers.base import BaseRetriever
from anvil.core.logging import get_logger

logger = get_logger("retriever.github")

class GitHubRetriever(BaseRetriever):
    """Fetches changelogs from GitHub."""
    
    def __init__(self, api_token: Optional[str] = None):
        self.api_token = api_token or os.getenv("GITHUB_TOKEN")
        if self.api_token:
            logger.debug("GitHubRetriever initialized with API token")
        else:
            logger.debug("GitHubRetriever initialized without API token (unauthenticated)")
        
    def get_source_url(self, package_name: str) -> Optional[str]:
        return None

    def get_changelog(self, repo_slug: str, current_version: str, target_version: str, subdirectory: Optional[str] = None, package_name: Optional[str] = None) -> Optional[str]:
        logger.debug(f"Fetching changelog for {repo_slug} (target: {target_version}, dir: {subdirectory}, pkg: {package_name})")
        
        # 1. Try Fetching All Releases in Range
        # This is preferred as it gives full history
        full_history = self._fetch_all_releases_in_range(repo_slug, current_version, target_version, package_name)
        if full_history:
             logger.debug(f"Found aggregated release notes for range {current_version} -> {target_version}")
             return full_history
             
        # Fallback: Try exact single release note (latest) if range failed
        release_note = self._get_release_note(repo_slug, target_version, package_name)
        if release_note:
            logger.debug(f"Found release notes for {target_version}")
            return release_note
            
        # 2. Try CHANGELOG.md file content (standard names)
        logger.debug(f"No release notes found for {target_version}, trying CHANGELOG files...")
        content = self._get_changelog_file(repo_slug, subdirectory)
        if content:
            return content

        # 3. Try Scanning README for links
        logger.debug("No standard changelog file found. Scanning README for links...")
        return self._scan_readme_for_changelog(repo_slug, subdirectory)

    def _get_headers(self):
        headers = {"Accept": "application/vnd.github.v3+json"}
        if self.api_token:
            headers["Authorization"] = f"Bearer {self.api_token}"
        return headers

    def _fetch_all_releases_in_range(self, repo_slug: str, current_version: str, latest_version: str, package_name: Optional[str] = None) -> Optional[str]:
        """Fetches and aggregates all release notes strictly between current_version and latest_version."""
        try:
            from packaging.version import parse
            current = parse(current_version)
            latest = parse(latest_version)
        except ImportError:
            logger.debug("packaging library not found, skipping version range checks")
            return None
            
        url = f"https://api.github.com/repos/{repo_slug}/releases?per_page=100"
        logger.debug(f"Fetching release history from {url}")
        
        try:
            resp = requests.get(url, headers=self._get_headers(), timeout=10)
            if resp.status_code != 200:
                logger.debug(f"Failed to list releases: {resp.status_code}")
                return None
                
            releases = resp.json()
            relevant_notes = []
            
            for release in releases:
                tag_name = release.get("tag_name", "")
                body = release.get("body", "")
                
                # Parse version from tag
                version_str = tag_name
                # Strip known prefixes
                if version_str.startswith("v"):
                    version_str = version_str[1:]
                elif package_name:
                    # Strip "package-name-" or "package-name@" or "package-name==" prefixes
                    prefixes = [f"{package_name}==", f"{package_name}@", f"{package_name}-v", f"{package_name}-"]
                    for prefix in prefixes:
                        if version_str.startswith(prefix):
                            version_str = version_str[len(prefix):]
                            break
                
                try:
                    rel_ver = parse(version_str)
                    # Check if in range: current < version <= latest
                    if current < rel_ver <= latest:
                        if body:
                            header = f"## Release {tag_name}\n"
                            relevant_notes.append(header + body)
                except Exception:
                    # Skip tags that don't look like versions
                    continue
            
            if relevant_notes:
                # Releases often returned newest first, but we might want them in order?
                # Actually newer-first is usually better for reading changelogs.
                return "\n\n".join(relevant_notes)
                
        except Exception as e:
            logger.debug(f"Error fetching release range: {e}")
            
        return None

    def _get_release_note(self, repo_slug: str, version: str, package_name: Optional[str] = None) -> Optional[str]:
        # Legacy method for single release, or fallback if range fails?
        # Actually, let's just use the range logic inside get_changelog() 
        # But this method is still useful for exact matches if needed.
        tags_to_try = [version, f"v{version}"]
        
        if package_name:
            # Add monorepo style tags
            tags_to_try.append(f"{package_name}=={version}")  # langchain style
            tags_to_try.append(f"{package_name}@{version}")   # lerna/turborepo style
            tags_to_try.append(f"{package_name}-{version}")   # common style
            tags_to_try.append(f"{package_name}-v{version}")  # common style

        for tag in tags_to_try:
            url = f"https://api.github.com/repos/{repo_slug}/releases/tags/{tag}"
            logger.debug(f"Checking GitHub releases for tag: {tag}")
            try:
                resp = requests.get(url, headers=self._get_headers(), timeout=5)
                if resp.status_code == 200:
                    data = resp.json()
                    return data.get("body")
            except requests.RequestException:
                pass
        return None

    def _get_changelog_file(self, repo_slug: str, subdirectory: Optional[str] = None, specific_filename: Optional[str] = None) -> Optional[str]:
        files = [specific_filename] if specific_filename else ["CHANGELOG.md", "History.md", "RELEASES.md", "CHANGES.md"]
        
        for filename in files:
            path = f"{subdirectory}/{filename}" if subdirectory else filename
            url = f"https://api.github.com/repos/{repo_slug}/contents/{path}"
            logger.debug(f"Checking for file: {path}")
            try:
                resp = requests.get(url, headers=self._get_headers(), timeout=5)
                if resp.status_code == 200:
                    content = resp.json().get("content", "")
                    if content:
                        logger.debug(f"Successfully retrieved {filename}")
                        return base64.b64decode(content).decode("utf-8", errors="ignore")
                else:
                     logger.debug(f"File lookup for {path} returned {resp.status_code}")
            except requests.RequestException as e:
                logger.debug(f"GitHub file request failed: {e}")
                
        return None

    def _scan_readme_for_changelog(self, repo_slug: str, subdirectory: Optional[str] = None) -> Optional[str]:
        # Fetch README
        url = f"https://api.github.com/repos/{repo_slug}/readme"
        if subdirectory:
            # If in subdirectory, explicitly look for README in that dir
            url = f"https://api.github.com/repos/{repo_slug}/contents/{subdirectory}/README.md"
        
        logger.debug(f"Fetching README from {url}")
        try:
            resp = requests.get(url, headers=self._get_headers(), timeout=5)
            if resp.status_code == 200:
                content_b64 = resp.json().get("content", "")
                if not content_b64:
                    return None
                readme_text = base64.b64decode(content_b64).decode("utf-8", errors="ignore")
                
                # Simple link extraction: [Link Text](Link URL)
                import re
                # Look for links with text containing 'change', 'history', 'release'
                # Case insensitive
                link_pattern = re.compile(r'\[([^\]]*?(?:change|history|release)[^\]]*?)\]\(([^\)]+)\)', re.IGNORECASE)
                matches = link_pattern.findall(readme_text)
                
                for text, link_url in matches:
                    logger.debug(f"Found potential changelog link in README: [{text}]({link_url})")
                    
                    # If it's a relative link, try to fetch it
                    if not link_url.startswith("http"):
                        # Resolve relative path
                        # If link is "./CHANGELOG.md", strip ./
                        clean_link = link_url.lstrip("./")
                        # If we encountered a fragment #, strip it
                        clean_link = clean_link.split("#")[0]
                        
                        logger.debug(f"Following relative link: {clean_link}")
                        return self._get_changelog_file(repo_slug, subdirectory, specific_filename=clean_link)
            else:
                logger.debug(f"README fetch failed: {resp.status_code}")
        except Exception as e:
            logger.debug(f"Error scanning README: {e}")
            
        return None
