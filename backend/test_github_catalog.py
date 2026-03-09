import unittest
from unittest.mock import Mock, patch

from github_catalog import GitHubCatalogClient


def _mock_response(payload):
    response = Mock()
    response.raise_for_status.return_value = None
    response.json.return_value = payload
    return response


class GitHubCatalogClientTests(unittest.TestCase):
    def test_list_repos_returns_empty_when_token_missing(self):
        with patch("github_catalog.os.getenv") as getenv:
            getenv.side_effect = lambda key, default="": default
            client = GitHubCatalogClient()
            self.assertFalse(client.is_configured())
            self.assertEqual(client.list_repos(), [])

    def test_list_repos_parses_payload(self):
        payload = [
            {
                "id": 1,
                "name": "Jarvez2.0",
                "full_name": "guilh/Jarvez2.0",
                "private": True,
                "default_branch": "main",
                "clone_url": "https://github.com/guilh/Jarvez2.0.git",
                "html_url": "https://github.com/guilh/Jarvez2.0",
                "description": "Jarvez repo",
                "owner": {"login": "guilh"},
            }
        ]

        with patch("github_catalog.os.getenv") as getenv:
            getenv.side_effect = lambda key, default="": "token-123" if key == "GITHUB_TOKEN" else default
            client = GitHubCatalogClient()
        with patch("github_catalog.requests.get", return_value=_mock_response(payload)) as get_mock:
            repos = client.list_repos(limit=5)

        self.assertEqual(len(repos), 1)
        self.assertEqual(repos[0].full_name, "guilh/Jarvez2.0")
        self.assertTrue(repos[0].private)
        self.assertEqual(get_mock.call_args.kwargs["params"]["per_page"], 5)

    def test_resolve_repo_requires_exact_when_multiple_candidates(self):
        payload = [
            {
                "id": 1,
                "name": "Jarvez2.0",
                "full_name": "guilh/Jarvez2.0",
                "private": True,
                "default_branch": "main",
                "clone_url": "https://github.com/guilh/Jarvez2.0.git",
                "html_url": "https://github.com/guilh/Jarvez2.0",
                "description": "Jarvez repo",
                "owner": {"login": "guilh"},
            },
            {
                "id": 2,
                "name": "Jarvez",
                "full_name": "guilh/Jarvez",
                "private": False,
                "default_branch": "main",
                "clone_url": "https://github.com/guilh/Jarvez.git",
                "html_url": "https://github.com/guilh/Jarvez",
                "description": "Older repo",
                "owner": {"login": "guilh"},
            },
        ]

        with patch("github_catalog.os.getenv") as getenv:
            getenv.side_effect = lambda key, default="": "token-123" if key == "GITHUB_TOKEN" else default
            client = GitHubCatalogClient()
        with patch("github_catalog.requests.get", return_value=_mock_response(payload)):
            repo, candidates = client.resolve_repo("Jar")

        self.assertIsNone(repo)
        self.assertEqual(len(candidates), 2)


if __name__ == "__main__":
    unittest.main()
