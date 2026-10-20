# SDK User Commands 08 — GitHub List Open Issues

This document teaches the bounded Python capability of listing open issues from a
GitHub repository through PyGithub.

## 1. Core capability

When a user wants the open issues from one repository, the reusable capability
is GitHub issue listing by token and repository name.

## 2. Executable Python relation

This capability should be learned as a reusable Python ability artifact.

```python
def main(
    token: str,
    repo_name: str,
    *,
    __dependencies__: tuple[str, ...] = ("PyGithub",),
) -> dict[str, object]:
    from github import Github

    client = Github(token)
    repo = client.get_repo(repo_name)
    issues = [{"number": issue.number, "title": issue.title} for issue in repo.get_issues(state="open")]
    return {"status": "ok", "repo_name": repo_name, "issues": issues}
```

## 3. Inputs and outputs

Inputs:

* `token`: the GitHub personal access token
* `repo_name`: the `owner/repo` repository name

Output:

* status, repository name, and open issues

## 4. Natural-language paraphrases

* list open GitHub issues for repository `octocat/Hello-World`
* fetch open issues with the GitHub SDK
* inspect repository issues through PyGithub

## 5. One-sentence summary

Listing open GitHub issues by token and repository name is a reusable Python SDK
repository-inspection capability.
