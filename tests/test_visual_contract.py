"""Public input and output guarantees across the visual extension."""
import copy
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch
from xml.etree import ElementTree as ET
from heige_feishu_word.compiler import compile_body,sha256_file
from heige_feishu_word.model import validate_body,BodyValidationError
from heige_feishu_word.themes import get_theme,THEMES
from heige_feishu_word.xml_renderer import render_document_xml
from heige_feishu_word.cover import render_cover_svg
from heige_feishu_word.svg_renderer import validate_svg,render_workflow_svg
from tests.fixtures import minimal_body,standard_body

class VisualContractTests(unittest.TestCase):
    def test_sample_boards_do_not_strand_final_cjk_character_or_period(self):
        from heige_feishu_word.presets import get_preset
        body=get_preset('project-pulse')
        root=ET.fromstring(render_cover_svg(body,get_theme(body['theme'])))
        self.assertNotIn('率',[node.text for node in root.iter()])
        body=get_preset('executive-brief')
        section=next(s for s in body['sections'] if s['type']=='whiteboard_workflow')
        root=ET.fromstring(render_workflow_svg(section,get_theme(body['theme'])))
        self.assertNotIn('。',[node.text for node in root.iter()])

    def test_workflow_theme_preserves_literal_color_in_user_text(self):
        section=next(s for s in standard_body()['sections'] if s['type']=='whiteboard_workflow')
        section['steps'][0]['description']='保留 #FFFFFF 与 #2E4A2A'
        svg=render_workflow_svg(section,get_theme('atelier-bone'))
        text=''.join(ET.fromstring(svg).itertext())
        self.assertIn('保留 #FFFFFF 与 #2E4A2A',text)
        self.assertIn('fill="'+get_theme('atelier-bone')['surface']+'"',svg)

    def test_theme_changes_real_output_and_rejects_misspelling(self):
        body=standard_body()
        a=render_document_xml(body)
        body['theme']='nocturne-teal'
        b=render_document_xml(body)
        self.assertNotEqual(a,b)
        self.assertIn(get_theme('nocturne-teal')['primary'],b)
        body['theme']='not-a-theme'
        with self.assertRaises(BodyValidationError):validate_body(body)

    def test_does_not_invent_disclaimer_or_numeric_status(self):
        body=minimal_body()
        xml=render_document_xml(body)
        self.assertNotIn('所有数字均为试点目标',xml)
        body['meta']['disclaimer']='数值来自已核对的台账。'
        self.assertIn('数值来自已核对的台账。',render_document_xml(body))

    def test_heading_order_and_native_colors(self):
        xml=render_document_xml(standard_body())
        root=ET.fromstring('<doc>'+xml+'</doc>')
        self.assertEqual(next(n.tag for n in root if n.tag.startswith('h') and n.tag!='hr'),'h1')
        for node in root.iter():
            for name in ('text-color','background-color','border-color'):
                if name in node.attrib:self.assertNotIn('#',node.attrib[name])
        for cell in root.findall('.//td')+root.findall('.//th'):
            self.assertEqual(cell[0].tag,'p')

    def test_invalid_xml_control_character_rejected(self):
        body=minimal_body();body['meta']['title']='Title\x00'
        with self.assertRaisesRegex(BodyValidationError,'XML'):validate_body(body)

    def test_compiler_refuses_user_files_modified_build_and_symlink(self):
        with TemporaryDirectory() as d:
            root=Path(d);out=root/'out';out.mkdir();(out/'my-notes.txt').write_text('keep')
            with self.assertRaises(BodyValidationError):compile_body(standard_body(),out)
            self.assertEqual((out/'my-notes.txt').read_text(),'keep')
            link=root/'link';link.symlink_to(out,target_is_directory=True)
            with self.assertRaises(BodyValidationError):compile_body(standard_body(),link)
            build=root/'build';compile_body(standard_body(),build)
            (build/'document.xml').write_text('manual edit')
            with self.assertRaises(BodyValidationError):compile_body(standard_body(),build)
            self.assertEqual((build/'document.xml').read_text(),'manual edit')

    def test_recompile_deterministic_complete_hashes(self):
        with TemporaryDirectory() as d:
            path=Path(d)/'out'
            a=compile_body(standard_body(),path)
            b=compile_body(standard_body(),path)
            self.assertEqual(a,b)
            for artifact in b['artifacts']:
                self.assertEqual(artifact['sha256'],sha256_file(path/artifact['path']))

    def test_publish_directory_failure_restores_existing_build(self):
        with TemporaryDirectory() as d:
            out=Path(d)/'out';compile_body(standard_body(),out)
            before=(out/'manifest.json').read_bytes()
            original=Path.replace
            def replace(path,target):
                if Path(target)==out and '.backup-' not in path.name:
                    raise OSError('simulated rename failure')
                return original(path,target)
            with patch.object(Path,'replace',replace):
                with self.assertRaises(OSError):compile_body(standard_body(),out)
            self.assertEqual(before,(out/'manifest.json').read_bytes())

    def test_user_file_created_during_render_survives(self):
        with TemporaryDirectory() as d:
            out=Path(d)/'out';compile_body(standard_body(),out)
            def render(body):
                (out/'review-notes.txt').write_text('keep review notes')
                return render_document_xml(body)
            with patch('heige_feishu_word.compiler.render_document_xml',render):
                with self.assertRaises(BodyValidationError):compile_body(standard_body(),out)
            self.assertEqual((out/'review-notes.txt').read_text(),'keep review notes')

    def test_cover_has_safe_text_and_theme_geometry(self):
        body=standard_body();body['meta']['eyebrow']='季度复盘'
        body['meta']['title']='短标题 & <审阅>'
        result=[]
        for theme in THEMES.values():
            svg=render_cover_svg(body,theme)
            self.assertEqual(validate_svg(svg).errors,())
            self.assertIn('&amp;',svg);result.append(svg)
        self.assertEqual(len(set(result)),len(THEMES))
        body['meta']['title']='非常长的标题'*30
        with self.assertRaises(BodyValidationError):render_cover_svg(body,get_theme())

if __name__=='__main__':unittest.main()
