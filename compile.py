from sys import platform

import PyInstaller.__main__

args = [
    'app.py',
    '--onedir',
    '--noconfirm',
    '--name=OpenPoster',
    '--optimize=2',
]

args.extend([
    '--collect-data=assets',
    '--collect-data=icons',
])

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

PyInstaller.__main__.run(args)
