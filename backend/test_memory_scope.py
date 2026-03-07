import unittest

from agent import _detect_scope_for_text, _prepare_memory_batches


class _FakeItem:
    def __init__(self, role: str, content: str):
        self.role = role
        self.content = content


class _FakeChatCtx:
    def __init__(self, items):
        self.items = items


class MemoryScopeTests(unittest.TestCase):
    def test_detect_scope_private_for_sensitive_text(self):
        scope = _detect_scope_for_text("Minha senha do banco e 1234", "public")
        self.assertEqual(scope, "private")

    def test_detect_scope_public_when_explicit(self):
        scope = _detect_scope_for_text("isso nao e segredo", "private")
        self.assertEqual(scope, "public")

    def test_prepare_batches_splits_public_and_private(self):
        chat_ctx = _FakeChatCtx(
            [
                _FakeItem("user", "Meu nome e Guilherme"),
                _FakeItem("assistant", "Prazer em te conhecer"),
                _FakeItem("user", "Isso e segredo: meu PIN e 4321"),
                _FakeItem("assistant", "Entendido, vou tratar como privado"),
            ]
        )
        public_batch, private_batch = _prepare_memory_batches(chat_ctx, set())
        self.assertEqual(len(public_batch), 2)
        self.assertEqual(len(private_batch), 2)
        self.assertIn("PIN", private_batch[0]["content"])


if __name__ == "__main__":
    unittest.main()
