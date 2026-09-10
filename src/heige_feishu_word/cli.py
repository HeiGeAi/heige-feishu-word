"""Portable commands for selecting, authoring and compiling visual documents."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import sys
from .compiler import compile_body
from .model import BodyValidationError,validate_body
from .themes import get_theme,list_themes


def _load_body(path):
    payload=json.loads(path.read_text(encoding='utf-8'))
    if not isinstance(payload,dict):
        raise BodyValidationError('body JSON must contain an object')
    return payload


def _parser():
    parser=argparse.ArgumentParser(prog='heige-feishu-word',description='Compile visual reports into editable Feishu documents.')
    commands=parser.add_subparsers(dest='command',required=True)
    for name in ('validate','compile'):
        command=commands.add_parser(name,help=f'{name} a Body JSON')
        command.add_argument('body',type=Path)
        command.add_argument('--theme',help='override the visual theme')
        if name=='compile':
            command.add_argument('--output',required=True,type=Path)
    commands.add_parser('themes',help='list visual themes')
    commands.add_parser('presets',help='list reporting presets')
    init=commands.add_parser('init',help='create a replaceable sample Body')
    init.add_argument('preset')
    init.add_argument('--output',required=True,type=Path)
    init.add_argument('--theme')
    gallery=commands.add_parser('gallery',help='build all presets and an offline gallery')
    gallery.add_argument('--output',required=True,type=Path)
    return parser


def main(argv=None):
    args=_parser().parse_args(argv)
    try:
        if args.command=='themes':
            result={'ok':True,'themes':list_themes()}
        elif args.command=='presets':
            from .presets import list_presets
            result={'ok':True,'presets':list_presets()}
        elif args.command=='init':
            from .presets import get_preset
            body=get_preset(args.preset)
            if args.theme:
                body['theme']=get_theme(args.theme)['slug']
            validate_body(body)
            args.output.parent.mkdir(parents=True,exist_ok=True)
            with args.output.open('x',encoding='utf-8') as handle:
                handle.write(json.dumps(body,ensure_ascii=False,indent=2)+'\n')
            result={'ok':True,'body':str(args.output.resolve())}
        elif args.command=='gallery':
            from .presets import list_presets,get_preset
            from .preview import render_gallery_html
            # Dedicated new gallery directory prevents overwriting user material.
            if args.output.exists():
                raise BodyValidationError('gallery output already exists; choose a new directory')
            entries=list_presets()
            for entry in entries:
                compile_body(get_preset(entry['slug']),args.output/entry['slug'])
            (args.output/'index.html').write_text(render_gallery_html(entries),encoding='utf-8')
            result={'ok':True,'gallery':str((args.output/'index.html').resolve()),'count':len(entries)}
        else:
            body=_load_body(args.body)
            if args.theme:
                body['theme']=get_theme(args.theme)['slug']
            validate_body(body)
            result={'ok':True,'title':body['meta']['title']}
            if args.command=='compile':
                manifest=compile_body(body,args.output)
                result={'ok':True,'output':str(args.output.resolve()),'manifest':manifest}
        print(json.dumps(result,ensure_ascii=False,indent=2,sort_keys=True))
        return 0
    except (BodyValidationError,ValueError,OSError) as exc:
        print(json.dumps({'ok':False,'error':str(exc)},ensure_ascii=False),file=sys.stderr)
        return 2


if __name__=='__main__':
    raise SystemExit(main())
