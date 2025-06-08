# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_data_files

datas = [('descriptors', 'descriptors')]
datas += collect_data_files('assets')
datas += collect_data_files('icons')


a = Analysis(
    ['app.py'],
    pathex=[],
    binaries=[],
    datas=datas,
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=2,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [('O', None, 'OPTION'), ('O', None, 'OPTION')],
    exclude_binaries=True,
    name='OpenPoster',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=['assets/openposter.icns'],
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='OpenPoster',
)
app = BUNDLE(
    coll,
    name='OpenPoster.app',
    icon='assets/openposter.icns',
    bundle_identifier='dev.openposter.openposter',
	info_plist={
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
)
