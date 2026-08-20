"""Installed vendor CLIs are not routable until their authentication check passes."""

from run_all import claude_auth_ready, codex_auth_ready, cursor_auth_ready


if __name__ == "__main__":
    assert claude_auth_ready('{"loggedIn":true,"authMethod":"claude.ai"}', 0)
    assert not claude_auth_ready('{"loggedIn":false}', 0)
    assert not claude_auth_ready("not json", 0)
    assert codex_auth_ready("Logged in using ChatGPT", 0)
    assert codex_auth_ready("Logged in using API key", 0)
    assert not codex_auth_ready("Not logged in", 1)
    assert cursor_auth_ready("✓ Logged in as user@example.com", 0)
    assert not cursor_auth_ready("", 1)
    print("vendor-native harness authentication gates pass")
