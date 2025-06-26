import xml.etree.ElementTree as ET
import os.path
import plistlib

from .calayer import CALayer

class CAFile:
    def __init__(self, path):
        self.path = path
        # parse index.xml because it tells you the name of the .caml file
        self.assets = {}
        with open(os.path.join(path, "index.xml"), 'rb') as f:
            self.index = plistlib.load(f, fmt=plistlib.FMT_XML)
            f.close()

        if os.path.exists(os.path.join(path, "assets")):
            for asset in os.listdir(os.path.join(path, "assets")):
                with open(os.path.join(path, "assets", asset), "rb") as f:
                    val = f.read()
                    self.assets[os.path.basename(f.name)] = val
                    f.close()

        self.elementTree = ET.parse(
            os.path.join(path, self.index["rootDocument"]))
        self.root = self.elementTree.getroot()
        self.rootlayer = CALayer().load(self.root[0])

    def create(self):
        tree = ET.ElementTree()
        root = ET.Element("caml")
        root.set('xmlns', 'http://www.apple.com/CoreAnimation/1.0')
        root.append(self.rootlayer.create())

        tree._setroot(root)
        return tree

    def write_file(self, filename, path="./"):
        capath = os.path.join(path, filename)
        if not os.path.exists(capath):
            os.makedirs(capath)
        with open(os.path.join(capath, 'index.xml'), 'wb') as f:
            plistlib.dump(self.index, f, fmt=plistlib.FMT_XML)
            f.close()

        if len(self.assets) > 0:
            assetspath = os.path.join(capath, "assets")
            if not os.path.exists(assetspath):
                os.makedirs(assetspath)
            for asset in self.assets:
                with open(os.path.join(assetspath, asset), 'wb') as f:
                    f.write(self.assets[asset])
                    f.close()

        # Build XML tree and sanitize None attribute values to avoid serialization errors
        tree = self.create()
        for elem in tree.iter():
            for key, val in list(elem.attrib.items()):
                if val is None:
                    elem.attrib.pop(key)
        tree.write(os.path.join(capath, self.index['rootDocument']))
