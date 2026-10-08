"""Synthetic regression coverage for safe publication and validation errors."""

from contextlib import redirect_stderr, redirect_stdout
from io import StringIO
import json
from pathlib import Path
import shutil
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch
from xml.etree import ElementTree

from heige_feishu_word.cli import main
from heige_feishu_word.compiler import compile_body
from heige_feishu_word.model import BodyValidationError, validate_body
from tests.fixtures import standard_body


class BundleRegressionTests(unittest.TestCase):
    def setUp(self):
        self.directory = TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)
        self.output = self.root / 'bundle'

    def previous(self):
        self.output.mkdir()
        (self.output / 'previous.txt').write_bytes(b'previous\x00bytes')

    def assert_previous(self):
        self.assertEqual((self.output / 'previous.txt').read_bytes(), b'previous\x00bytes')

    def test_existing_bundle_is_replaced_and_backup_cleaned(self):
        self.previous()
        compile_body(standard_body(), self.output)
        self.assertFalse((self.output / 'previous.txt').exists())
        self.assertTrue((self.output / 'manifest.json').is_file())
        self.assertEqual(list(self.root.iterdir()), [self.output])

    def test_failure_moving_previous_bundle_preserves_it(self):
        self.previous()
        with patch.object(Path, 'replace', side_effect=PermissionError('denied')):
            with self.assertRaises(PermissionError):
                compile_body(standard_body(), self.output)
        self.assert_previous()
        self.assertEqual(list(self.root.iterdir()), [self.output])

    def test_interrupt_immediately_after_backup_rename_keeps_previous_bytes(self):
        self.previous()
        original = Path.replace
        def replace(path, destination):
            result = original(path, destination)
            if path == self.output:
                raise KeyboardInterrupt()
            return result
        with patch.object(Path, 'replace', replace):
            with self.assertRaises(KeyboardInterrupt):
                compile_body(standard_body(), self.output)
        backups = list(self.root.glob('.bundle.backup.*/previous'))
        self.assertEqual(len(backups), 1)
        self.assertEqual((backups[0] / 'previous.txt').read_bytes(), b'previous\x00bytes')

    def test_install_failure_and_interrupt_restore_previous_bundle(self):
        original = Path.replace
        for error in (PermissionError('install denied'), KeyboardInterrupt()):
            with self.subTest(error=type(error).__name__):
                if not self.output.exists():
                    self.previous()
                def replace(path, destination):
                    if destination == self.output and path.name != 'previous':
                        raise error
                    return original(path, destination)
                with patch.object(Path, 'replace', replace):
                    with self.assertRaises(type(error)):
                        compile_body(standard_body(), self.output)
                self.assert_previous()
                self.assertEqual(list(self.root.iterdir()), [self.output])

    def test_rollback_failure_retains_backup_and_reports_recovery_path(self):
        self.previous()
        original = Path.replace
        def replace(path, destination):
            if destination == self.output:
                raise PermissionError('denied')
            return original(path, destination)
        with patch.object(Path, 'replace', replace):
            with self.assertRaisesRegex(OSError, 'previous output retained at') as error:
                compile_body(standard_body(), self.output)
        backups = list(self.root.glob('.bundle.backup.*/previous'))
        self.assertEqual(len(backups), 1)
        self.assertEqual((backups[0] / 'previous.txt').read_bytes(), b'previous\x00bytes')
        self.assertIn(str(backups[0]), str(error.exception))

    def test_cleanup_failure_does_not_undo_success(self):
        self.previous()
        original = shutil.rmtree
        def cleanup(path, *args, **kwargs):
            if '.backup.' in Path(path).name:
                self.assertTrue(kwargs.get('ignore_errors'))
                return  # Model rmtree ignoring an OS-level cleanup error.
            return original(path, *args, **kwargs)
        with patch('heige_feishu_word.compiler.shutil.rmtree', cleanup):
            manifest = compile_body(standard_body(), self.output)
        self.assertEqual(json.loads((self.output / 'manifest.json').read_text()), manifest)
        self.assertEqual(len(list(self.root.glob('.bundle.backup.*'))), 1)

    def test_first_install_failure_leaves_no_partial_output(self):
        with patch.object(Path, 'replace', side_effect=OSError('rename failed')):
            with self.assertRaises(OSError):
                compile_body(standard_body(), self.output)
        self.assertEqual(list(self.root.iterdir()), [])

    def test_malformed_renderer_output_never_replaces_previous_bundle(self):
        self.previous()
        for xml in ('<p>\x00</p>', '<p>', '<p>\ud800</p>'):
            with self.subTest(xml=repr(xml)):
                with patch('heige_feishu_word.compiler.render_document_xml', return_value=xml):
                    with self.assertRaisesRegex(BodyValidationError, 'invalid document XML'):
                        compile_body(standard_body(), self.output)
                self.assert_previous()
                self.assertEqual(list(self.root.iterdir()), [self.output])

    def test_forbidden_xml_characters_report_field_paths(self):
        for character in ('\x00', '\x01', '\x0b', '\x0c', '\x1f', '\ud800', '\udfff', '\ufffe', '\uffff'):
            for field in ('meta.title', 'sections[0].body', 'sections[2].rows[0][0]'):
                with self.subTest(character=repr(character), field=field):
                    body = standard_body()
                    if field == 'meta.title':
                        body['meta']['title'] += character
                    elif field == 'sections[0].body':
                        body['sections'][0]['body'] += character
                    else:
                        body['sections'][2]['rows'][0][0] += character
                    with self.assertRaises(BodyValidationError) as error:
                        validate_body(body)
                    self.assertIn(field, str(error.exception))
                    self.assertIn('XML-forbidden', str(error.exception))
                    with self.assertRaises(BodyValidationError):
                        compile_body(body, self.output)
                    self.assertFalse(self.output.exists())

    def test_permitted_whitespace_and_unicode_compile_as_valid_fragment(self):
        body = standard_body()
        body['sections'][0]['body'] = '中文\t换行\n回车\r😀 & <text>'
        compile_body(body, self.output)
        xml = (self.output / 'document.xml').read_text()
        root = ElementTree.fromstring('<root>' + xml + '</root>')
        self.assertIn('😀 & <text>', ''.join(root.itertext()))
        self.assertIn('\t', xml)
        self.assertIn('<br/>', xml)

    def test_tone_types_and_values_obey_model_and_cli_contract(self):
        body_path = self.root / 'body.json'
        for tone in ([], {}, None, 1, True, 'invalid', 'success', 'warning', 'risk', 'info'):
            valid = isinstance(tone, str) and tone in ('success', 'warning', 'risk', 'info')
            body = standard_body()
            body['sections'][0]['tone'] = tone
            with self.subTest(tone=tone):
                if valid:
                    self.assertIs(validate_body(body), body)
                else:
                    with self.assertRaisesRegex(BodyValidationError, r'sections\[0\].tone'):
                        validate_body(body)
                body_path.write_text(json.dumps(body), encoding='utf-8')
                for command in ('validate', 'compile'):
                    stdout, stderr = StringIO(), StringIO()
                    args = [command, str(body_path)]
                    if command == 'compile':
                        args += ['--output', str(self.output)]
                    with redirect_stdout(stdout), redirect_stderr(stderr):
                        status = main(args)
                    self.assertEqual(status, 0 if valid else 2)
                    payload = json.loads(stdout.getvalue() if valid else stderr.getvalue())
                    self.assertEqual(payload['ok'], valid)
                    if not valid:
                        self.assertIn('sections[0].tone', payload['error'])
                        self.assertEqual(stdout.getvalue(), '')

    def test_cli_forbidden_xml_is_structured_error(self):
        body = standard_body()
        body['meta']['title'] += '\x00'
        body_path = self.root / 'body.json'
        body_path.write_text(json.dumps(body), encoding='utf-8')
        stderr = StringIO()
        with redirect_stderr(stderr):
            status = main(['compile', str(body_path), '--output', str(self.output)])
        self.assertEqual(status, 2)
        payload = json.loads(stderr.getvalue())
        self.assertFalse(payload['ok'])
        self.assertIn('meta.title', payload['error'])
        self.assertFalse(self.output.exists())
