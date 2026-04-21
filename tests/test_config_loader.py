"""Unit tests for config_loader — no network, no DB needed."""
import os
import tempfile
import textwrap
import unittest


class TestConfigLoader(unittest.TestCase):

    def _write_config(self, content: str) -> str:
        f = tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False,
                                        encoding='utf-8')
        f.write(textwrap.dedent(content))
        f.close()
        return f.name

    def _load(self, path: str) -> dict:
        os.environ['CONFIG_FILE'] = path
        # Re-import each time so the env var is picked up
        import importlib, web.config_loader as m
        importlib.reload(m)
        return m.load_config()

    def tearDown(self):
        os.environ.pop('CONFIG_FILE', None)

    # ─────────────────────────────────────────────────────────────────────────

    def test_loads_property_name(self):
        path = self._write_config("""
            property:
              name: "Test House"
        """)
        cfg = self._load(path)
        self.assertEqual(cfg['property']['name'], 'Test House')
        os.unlink(path)

    def test_loads_apartments_list(self):
        path = self._write_config("""
            apartments:
              - name: "Apt A"
                max_guests: 4
              - name: "Apt B"
                max_guests: 2
        """)
        cfg = self._load(path)
        self.assertEqual(len(cfg['apartments']), 2)
        self.assertEqual(cfg['apartments'][0]['name'], 'Apt A')
        os.unlink(path)

    def test_missing_file_raises(self):
        os.environ['CONFIG_FILE'] = '/nonexistent/path/config.yaml'
        import importlib, web.config_loader as m
        importlib.reload(m)
        with self.assertRaises(FileNotFoundError):
            m.load_config()

    def test_empty_file_returns_empty_dict(self):
        path = self._write_config('')
        cfg = self._load(path)
        self.assertEqual(cfg, {})
        os.unlink(path)

    def test_branding_color(self):
        path = self._write_config("""
            branding:
              primary_color: "#4a7c59"
        """)
        cfg = self._load(path)
        self.assertEqual(cfg['branding']['primary_color'], '#4a7c59')
        os.unlink(path)


if __name__ == '__main__':
    unittest.main()
