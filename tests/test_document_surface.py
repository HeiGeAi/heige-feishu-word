"""The host is a white Feishu document, not an independent slide deck."""
import unittest
from xml.etree import ElementTree as ET
from heige_feishu_word.presets import list_presets,get_preset
from heige_feishu_word.themes import get_theme
from heige_feishu_word.xml_renderer import render_document_xml
from heige_feishu_word.cover import render_metrics_svg

class DocumentSurfaceTests(unittest.TestCase):
    def test_first_decision_precedes_any_board_and_title_appears_once(self):
        for item in list_presets():
            body=get_preset(item['slug']);xml=render_document_xml(body)
            self.assertEqual(xml.count(body['meta']['title']),1)
            self.assertLess(xml.index('<callout'),xml.index('<whiteboard'))
            self.assertNotIn('<h2',xml)

    def test_all_embedded_boards_use_white_compact_geometry(self):
        for item in list_presets():
            root=ET.fromstring('<doc>'+render_document_xml(get_preset(item['slug']))+'</doc>')
            for board in root.findall('whiteboard'):
                svg=board[0];height=float(svg.attrib['height'])
                self.assertLess(height,900)
                self.assertEqual(svg.attrib['viewBox'],f'0 0 1600 {int(height)}')
                background=svg[0]
                self.assertEqual(background.attrib['fill'].lower(),'#ffffff')
                self.assertEqual(float(background.attrib['height']),height)

    def test_metric_strip_preserves_every_value_and_has_no_title(self):
        for item in list_presets():
            body=get_preset(item['slug']);section=next((s for s in body['sections'] if s['type']=='metrics'),None)
            if section is None:continue
            svg=render_metrics_svg(section,get_theme(body['theme']))
            text=''.join(ET.fromstring(svg).itertext())
            normal=lambda s:''.join(s.split())
            for metric in section['items']:
                for value in metric.values():self.assertIn(normal(value),normal(text))
            self.assertNotIn(body['meta']['title'],text)

    def test_metric_percent_and_latin_words_stay_on_one_line(self):
        from heige_feishu_word.cover import _wrap
        lines=_wrap('本月增速达到 10%，保留 OpenAPI 名称',10)
        self.assertTrue(any('10%' in line for line in lines))
        self.assertTrue(any('OpenAPI' in line for line in lines))
        self.assertEqual(''.join(lines),'本月增速达到 10%，保留 OpenAPI 名称')

    def test_complete_native_evidence_follows_the_action_sections(self):
        for item in list_presets():
            body=get_preset(item['slug']);xml=render_document_xml(body)
            story,details=xml.split('<h1>数据与流程明细</h1>')
            self.assertIn('<checkbox',story)
            self.assertNotIn('<whiteboard',details)
            root=ET.fromstring('<doc>'+details+'</doc>')
            text=''.join(''.join(root.itertext()).split())
            for section in body['sections']:
                if section['type']=='metrics':
                    for metric in section['items']:
                        for value in metric.values():self.assertIn(''.join(value.split()),text)
                elif section['type']=='whiteboard_workflow':
                    for step in section['steps']:
                        for field in ('title','description'):self.assertIn(''.join(step[field].split()),text)
                elif section['type']=='chart':
                    self.assertIn(section['source'],story)
                    for label in section['labels']:self.assertIn(''.join(label.split()),text)
                    for series in section['series']:
                        for value in series['values']:self.assertIn(str(value),text)

    def test_white_page_text_colors_have_readable_contrast(self):
        def luminance(color):
            values=[int(color[i:i+2],16)/255 for i in (1,3,5)]
            channels=[v/12.92 if v<=.04045 else ((v+.055)/1.055)**2.4 for v in values]
            return sum(a*b for a,b in zip(channels,[.2126,.7152,.0722]))
        for item in list_presets():
            theme=get_theme(item['theme'])
            for role in ('ink','muted','primary'):
                self.assertGreaterEqual(1.05/(luminance(theme[role])+.05),4.5,(item['slug'],role))
            self.assertEqual(len(theme['palette']),len(theme['tints']))
            for accent,tint in zip(theme['palette'],theme['tints']):
                for text_color in (accent,theme['ink'],theme['muted']):
                    ratio=(luminance(tint)+.05)/(luminance(text_color)+.05)
                    self.assertGreaterEqual(ratio,4.5,(item['slug'],text_color,tint))
            self.assertNotIn('yellow',theme['native_accents'][:2])

if __name__=='__main__':unittest.main()
