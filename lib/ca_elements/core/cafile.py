import xml.etree.ElementTree as ET
import os
import plistlib
import re
import io
import shutil
from pathlib import Path

try:
    from .calayer import CALayer
except ImportError:
    try:
        from lib.ca_elements.core.calayer import CALayer
    except ImportError as e:
        raise ImportError("Could not import CALayer. Ensure the package structure is correct or run as part of the package.") from e

def _attempt_xml_repair(xml_content, line_num=None, col_num=None):
    """Tries to fix common XML errors, focusing on the reported location."""
    lines = xml_content.splitlines()
    if not lines:
        return xml_content

    repaired = False
    if line_num is not None and col_num is not None and 0 < line_num <= len(lines):
        line_index = line_num - 1
        line = lines[line_index]
        col_index = col_num - 1 # 0-based index

        if 0 <= col_index < len(line):
            segment_before_error = line[:col_num]
            match = re.search(r'=\s*([^"\'>\s]+)\s*$', segment_before_error)
            if match:
                 likely_end = col_index
                 while likely_end < len(line) and line[likely_end] not in ('"', "'", ' ', '>', '/'):
                     likely_end += 1

                 start_val_index = match.start(1)
                 lines[line_index] = line[:start_val_index] + '"' + line[start_val_index:likely_end] + '"' + line[likely_end:]
                 repaired = True
                 print(f"Repair attempt: Added quotes around value at line {line_num}, col {start_val_index + 1}-{likely_end}.")


    if not repaired:
        print("Repair attempt: Applying general attribute quoting as fallback.")
        fixed_xml = "\n".join(lines)
        fixed_xml = re.sub(r'=([^"\'\s][^>\s]*)', r'="\1"', fixed_xml)
        return fixed_xml
    else:
        return "\n".join(lines)


class CAFile:
    def __init__(self, path):
        self.path = Path(path)
        self.assets = {}
        self.index = {}
        self.rootlayer = None
        self.elementTree = None
        self.root = None

        if not self.path.is_dir():
             raise FileNotFoundError(f"Input path is not a valid directory: {self.path}")

        self._load_index()
        self._load_assets()
        self._load_caml()
        self._initialize_root_layer()

    def _load_index(self):
        index_path = self.path / "index.xml"
        if not index_path.is_file():
            raise FileNotFoundError(f"index.xml not found in {self.path}")
        try:
            with open(index_path, 'rb') as f:
                self.index = plistlib.load(f, fmt=plistlib.FMT_XML)
        except Exception as e:
            raise Exception(f"Error loading index.xml: {e}") from e
        if "rootDocument" not in self.index:
            raise KeyError("Missing 'rootDocument' key in index.xml")

    def _load_assets(self):
        assets_path = self.path / "assets"
        if assets_path.is_dir():
            for item in assets_path.iterdir():
                if item.is_file():
                    try:
                        self.assets[item.name] = item.read_bytes()
                    except Exception as e:
                        print(f"Warning: Failed to load asset {item.name}: {e}")

    def _load_caml(self):
        caml_filename = self.index["rootDocument"]
        caml_path = self.path / caml_filename

        if not caml_path.is_file():
            raise FileNotFoundError(f"Root document '{caml_filename}' not found in {self.path}")

        try:
            xml_content = caml_path.read_text(encoding='utf-8')
            if not xml_content.strip().startswith('<'):
                 raise ValueError("Invalid XML - doesn't start with an opening tag")

            parser = ET.XMLParser(encoding='utf-8')
            self.root = ET.fromstring(xml_content, parser=parser)
            self.elementTree = ET.ElementTree(self.root)

        except ET.ParseError as e:
            original_error_msg = f"XML parsing error in {caml_filename}: {e}"
            print(f"Info: {original_error_msg}")
            line_num, col_num = self._extract_error_location(str(e))

            print("Attempting to repair XML...")
            repaired_xml = _attempt_xml_repair(xml_content, line_num, col_num)
            self._try_parse_repaired(repaired_xml, caml_path, original_error_msg)

        except Exception as load_err:
            raise Exception(f"Error loading CAML file '{caml_filename}': {load_err}") from load_err

    def _extract_error_location(self, error_msg):
        match = re.search(r'line (\d+), column (\d+)', error_msg)
        if match:
            return int(match.group(1)), int(match.group(2))
        return None, None

    def _try_parse_repaired(self, repaired_xml, caml_path, original_error_msg):
        try:
            parser = ET.XMLParser(encoding='utf-8')
            self.root = ET.fromstring(repaired_xml, parser=parser)
            self.elementTree = ET.ElementTree(self.root)
            self._backup_and_save_repaired(repaired_xml, caml_path)
        except ET.ParseError as repair_e:
            repair_fail_msg = f"Repair attempt failed with: {repair_e}"
            print(f"Error: {repair_fail_msg}")
            raise Exception(f"{original_error_msg}. {repair_fail_msg}") from repair_e
        except Exception as general_repair_e:
             raise Exception(f"{original_error_msg}. Unexpected error during repair parsing: {general_repair_e}") from general_repair_e

    def _backup_and_save_repaired(self, repaired_xml, caml_path):
        backup_path = caml_path.with_suffix(caml_path.suffix + ".backup")
        try:
            print(f"Info: Backing up original file to {backup_path}")
            shutil.copy2(caml_path, backup_path)
            print(f"Info: Saving repaired XML to {caml_path}")
            caml_path.write_text(repaired_xml, encoding='utf-8')
            print("Info: XML file successfully repaired and saved.")
        except Exception as backup_save_err:
            print(f"Warning: Could not backup or save repaired file: {backup_save_err}")

    def _initialize_root_layer(self):
        if self.root is None:
             raise Exception("XML root element could not be determined.")

        if self.root.tag == 'caml' and list(self.root):
             self.rootlayer = CALayer(self.root[0])
        elif self.root.tag == 'caml' and not list(self.root):
             print("Info: Creating a default root CALayer for empty CAML file.")
             default_layer_element = ET.Element("CALayer")
             self.root.append(default_layer_element)
             self.rootlayer = CALayer(default_layer_element)
        elif self.root.tag != 'caml':
             print(f"Warning: Root element is <{self.root.tag}>, not <caml>. Using it as root layer.")
             self.rootlayer = CALayer(self.root)
        else: # Should not happen if checks above are correct
             raise ValueError("Cannot initialize CALayer: No suitable root layer element found.")


    def create_tree(self):
        """Generates the ElementTree for the current state."""
        if not self.rootlayer:
            raise Exception("Cannot create XML: rootlayer is not initialized.")

        caml_root = ET.Element("caml")
        caml_root.set('xmlns', 'http://www.apple.com/CoreAnimation/1.0')
        caml_root.append(self.rootlayer.create())

        return ET.ElementTree(caml_root)

    def write_file(self, output_filename, output_dir="./"):
        """Writes the complete CAFile structure to disk."""
        output_path = Path(output_dir) / output_filename
        output_path.mkdir(parents=True, exist_ok=True)

        caml_filename = output_path.stem + ".caml"
        self.index['rootDocument'] = caml_filename

        try:
            index_path = output_path / 'index.xml'
            with open(index_path, 'wb') as f:
                plistlib.dump(self.index, f, fmt=plistlib.FMT_XML)
        except Exception as e:
            raise Exception(f"Error writing index.xml to {index_path}: {e}") from e

        if self.assets:
            assets_output_path = output_path / "assets"
            assets_output_path.mkdir(exist_ok=True)
            for asset_name, asset_data in self.assets.items():
                try:
                    (assets_output_path / asset_name).write_bytes(asset_data)
                except Exception as e:
                    print(f"Warning: Failed to write asset {asset_name}: {e}")

        try:
            tree_to_write = self.create_tree()
            caml_output_path = output_path / caml_filename
            tree_to_write.write(caml_output_path, xml_declaration=True,
                                encoding='utf-8', method='xml')
            print(f"Info: Successfully wrote CAML file to {caml_output_path}")
        except Exception as e:
            raise Exception(f"Error writing CAML file '{caml_filename}' to {output_path}: {e}") from e