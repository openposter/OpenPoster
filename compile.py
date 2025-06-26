from sys import platform
import PyInstaller.__main__
import os
import re
import subprocess

args = [
    'app.py',
    '--onefile',
    # '--noconfirm',
    '--name=OpenPoster',
    '--optimize=2',
]

args.extend([
    '--collect-data=assets',
    '--collect-data=icons',
    '--add-data=languages:languages',
    '--add-data=themes:themes',
])

sep = ';' if platform == 'win32' else ':'
args.append(f"--add-data=descriptors{sep}descriptors")

# for some stupid reason it couldn't find pyside6 for me - anh
hacks = [
    '--hidden-import=PySide6.QtCore',
    '--hidden-import=PySide6.QtWidgets',
    '--hidden-import=PySide6.QtGui',
    '--collect-submodules=PySide6',
    '--collect-data=PySide6'
]

if platform == "darwin":
    # add --windowed arg for macOS
    args.append('--windowed')
    args.append('--icon=assets/openposter.icns')
    args.append('--osx-bundle-identifier=dev.openposter.openposter')

    # codesigning resources
    try:
        import secrets.compile_config as compile_config # type: ignore
        args.append('--osx-entitlements-file=entitlements.plist')
        args.append(f"--codesign-identity={compile_config.CODESIGN_HASH}")
    except ImportError:
        print("No compile_config found, ignoring codesign...")

elif platform == "win32":
    args.append('--icon=assets/openposter.ico')
    # add windows version info
    args.append('--version-file=version.txt')
    args.append('--windowed') # or --noconsole

    args.extend(hacks)

if platform == "darwin":
    subprocess.run(['pyi-makespec'] + args)

    spec_path = 'OpenPoster.spec'
    info_plist = '''    info_plist={
        'NSPrincipalClass': 'NSApplication',
        'CFBundleDocumentTypes': [
            {
                'CFBundleTypeName': 'OpenPoster Project',
                'CFBundleTypeRole': 'Editor',
                'CFBundleTypeIconFile': 'openposter.icns',
                'LSItemContentTypes': ['dev.openposter.openposter.ca'],
                'LSTypeIsPackage': True,
            }
        ],
        'UTExportedTypeDeclarations': [
            {
                'UTTypeIdentifier': 'dev.openposter.openposter.ca',
                'UTTypeDescription': 'OpenPoster Project',
                'UTTypeConformsTo': ['com.apple.package'],
                'UTTypeTagSpecification': {
                    'public.filename-extension': ['ca'],
                },
            }
        ],
    },
'''
    if os.path.exists(spec_path):
        with open(spec_path, 'r') as f:
            content = f.read()
        if 'info_plist=' in content:
            content = re.sub(r'info_plist\s*=\s*\{[\s\S]+?\},', info_plist, content, flags=re.DOTALL)
        else:
            content = re.sub(r'(BUNDLE\([^)]+)', r'\1' + info_plist, content, flags=re.DOTALL)
        with open(spec_path, 'w') as f:
            f.write(content)
        print("Patched info_plist into OpenPoster.spec for macOS.")

    PyInstaller.__main__.run(['OpenPoster.spec', '--noconfirm'])
else:
    PyInstaller.__main__.run(args)
