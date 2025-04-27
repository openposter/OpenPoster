import xml.etree.ElementTree as et
import xml.dom.minidom as minidom
import os

# Use to generate xml for reference frames assets folder
class XmlGenerator:
    def __init__(self):
        self.startTag = 'CGImage'
        self.endTag = '/>'

    def make_xml(
            self,
            startFrame: int = 0,
            endFrame: int = 1,
            filePrefix: str = '',
            fileExtension: str = '.png',
            padding: int = 4,
            exportAsAnimation: bool = False,
            fps: int = 30,
            step: int = 1,
            withRoot: bool = True
        ) -> et.ElementTree:
        """
            Generate multi-line xml thingy that you can insert into .caml file directly
            if you don't provide anything it'll just use the default
        """
        root = et.Element('root')

        #<animations>
        #    <animation type="CAKeyframeAnimation" calculationMode="linear" keyPath="contents" beginTime="1e-100" duration="5" removedOnCompletion="0" repeatCount="inf" repeatDuration="0" speed="1" timeOffset="0">
        #        <values>
        #            ...
        #        </values>
        #    </animation>
        #</animations>

        if exportAsAnimation:
            totalDuration = ((endFrame - startFrame) / fps) / step

            animations = et.SubElement(root, 'animations')
            animation = et.SubElement(animations, 'animation', {
                'type': 'CAKeyframeAnimation',
                'calculationMode': 'discrete',
                'keyPath': 'contents',
                'beginTime': '1e-100',
                'duration': str(totalDuration),
                'removedOnCompletion': '0',
                'repeatCount': 'inf',
                'repeatDuration': '0',
                'speed': '1',
                'timeOffset': '0'
            })
            values = et.SubElement(animation, 'values')

        si = startFrame
        for i in range(startFrame, int((endFrame + step) / step)):
            n = f"{si:0{padding}d}"
            si += step

            if exportAsAnimation:
                asset = et.SubElement(values, self.startTag)
            else:
                asset = et.SubElement(root, self.startTag)

            asset.set('src', f"assets/{filePrefix}{n}{fileExtension}")

        if withRoot:
            result = et.ElementTree(root)
        else:
            if exportAsAnimation:
                animations_elem = root.find('animations')
                return et.ElementTree(animations_elem)
            else:
                new_root = et.Element('values')
                for child in list(root):
                    new_root.append(child)
                return et.ElementTree(new_root)

        return result


# TODO: change and auto fixer deadline is in 2 days
class AnimationObjectEditor:
    def __init__(self):
        self.tree = None
        self.root = None
        self.namespace = None

    # file loading and writing section
    def load_file(self, file_path: str) -> bool:
        """
            Open and load the .caml into memory
        """
        script_dir = os.path.dirname(os.path.abspath(__file__))
        resolved_path = os.path.join(script_dir, file_path)

        try:
            self.tree = et.parse(resolved_path)
            self.root = self.tree.getroot()

            # apple's namespace
            if self.root.tag.startswith("{"):
                self.namespace = self.root.tag.split("}")[0][1:]
            else:
                self.namespace = None

            return True
        except et.ParseError as e:
            print(f"Parsing error: {e}")
            return False
        except FileNotFoundError:
            print(f"File not found: {resolved_path}")
            return False
        except Exception as e:
            print(f"Unexpected error: {e}")
            return False
        
    def save_file(self, file_path: str) -> bool:
        """
            Don't forget the file path/name
        """
        script_dir = os.path.dirname(os.path.abspath(__file__))
        resolved_path = os.path.join(script_dir, file_path)

        try:
            if self.namespace:
                et.register_namespace("", self.namespace)

            # saving
            with open(resolved_path, "wb") as f:
                f.write(b'<?xml version="1.0" encoding="UTF-8"?>\n')
                self.tree.write(f, encoding="utf-8", xml_declaration=False)

            print(f"File saved: {resolved_path}")
            return True
        
        except Exception as e:
            print(f"Error saving: {e}")
            return False
    
    def get_root(self): return self.root
    def get_tree(self): return self.tree

    def find_target(self, tag_name: str, attr_name: str, attr_value: str):
        if self.namespace:
            query = f".//{{{self.namespace}}}{tag_name}"
        else:
            query = f".//{tag_name}"

        for elem in self.root.findall(query):
            if elem.get(attr_name) == attr_value:
                return elem
            
        return None
        
    def insert_object_to_target(self, tag_name: str, attr_name: str, attr_value: str, object: et.Element) -> bool:
        """
            Give a name and a tree then it'll do it for you.
        """
        target = self.find_target(tag_name, attr_name, attr_value)
        if target is None:
            print(f"can't find '{tag_name}', {attr_name}={attr_value}")
            return False
        
        target.append(object)
        print(f"inserted object into '{tag_name}', {attr_name}={attr_value}")
        return True


    # am doing these later
    #def change_duration(
    #        self,
    #        autoMode = True,
    #        fps = 30,
    #        targetDuration = 15
    #    ):
    #    """
    #        if autoMode is on then every varible after it is ignored
    #    """
    #    print(self.xmlContent, autoMode, fps, targetDuration)

    #def fix_dereferenced(
    #        self,
    #        fixAll = False,
    #        targetAnimationToFix = et.ElementTree
    #    ):
    #    """
    #        fixAll will go through all animation objects so provide the whole .caml
    #    """
    #    print(self.xmlContent, fixAll, targetAnimationToFix)


# for debugging
if __name__ == "__main__":
    gen = XmlGenerator()
    t = gen.make_xml(
        startFrame=1,
        endFrame=200,
        filePrefix="fg_",
        fileExtension=".png",
        padding=4,
        exportAsAnimation=True,
        fps=12.5,
        step=2,
        withRoot=False
    )
    xml_str = et.tostring(t.getroot(), 'utf-8')
    formatted = minidom.parseString(xml_str).toprettyxml("\t")
    print(formatted)
    
    #editor = AnimationObjectEditor()
    #editor.load_file("main.caml")
    #editor.insert_object_to_target("CALayer", "name", "Target", t.getroot())
    ##editor.insert_object_to_target("CALayer", "nuggetId", "1", t.getroot())
    #editor.save_file("main_output.caml")