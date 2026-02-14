
from github import Auth, Github


class GitHubManager:
    """The 'Hands' of the Agent: Allows it to read/write its own source code."""

    def __init__(self, token: str, repo_name: str):
        self.github = Github(auth=Auth.Token(token))
        self.repo = self.github.get_repo(repo_name)

    def get_file_content(self, file_path: str) -> str:
        """Reads code from the repository."""
        try:
            content = self.repo.get_contents(file_path)
            return content.decoded_content.decode("utf-8")
        except Exception as e:
            return f"Error reading {file_path}: {str(e)}"

    def create_feature_branch(self, branch_name: str, source_branch: str = "main"):
        """Creates a safe sandbox branch for the agent to work in."""
        source = self.repo.get_branch(source_branch)
        self.repo.create_git_ref(ref=f"refs/heads/{branch_name}", sha=source.commit.sha)
        return f"Branch {branch_name} created."

    def commit_file(self, file_path: str, content: str, message: str, branch: str):
        """The Agent 'writing' code to the repository."""
        try:
            file = self.repo.get_contents(file_path, ref=branch)
            self.repo.update_file(file_path, message, content, file.sha, branch=branch)
            return f"Updated {file_path} on {branch}"
        except Exception:
            self.repo.create_file(file_path, message, content, branch=branch)
            return f"Created {file_path} on {branch}"

    def create_pull_request(self, title: str, body: str, head: str, base: str = "main"):
        """The Agent submitting work for review (Human-in-the-loop)."""
        pr = self.repo.create_pull(title=title, body=body, head=head, base=base)
        return f"PR Created: {pr.html_url}"
