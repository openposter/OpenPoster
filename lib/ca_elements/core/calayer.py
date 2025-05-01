import xml.etree.ElementTree as ET
from typing import Optional, Any

# Simplified imports, assumes these classes exist and handle their own creation/serialization
try:
    from .cgimage import CGImage
    from ..state.lkstate import LKState
    from ..state.lkstatetransition import LKStateTransition
    from ..animation.caanimation import CAAnimation # Assuming a base or specific imports
except ImportError:
    try:
        from lib.ca_elements.core.cgimage import CGImage
        from lib.ca_elements.state.lkstate import LKState
        from lib.ca_elements.state.lkstatetransition import LKStateTransition
        from lib.ca_elements.animation.caanimation import CAAnimation
    except ImportError as e:
        raise ImportError("Could not import dependencies for CALayer. Check package structure.") from e

def create_animation_instance(element):
    anim_type = element.get("type")
    try:
        if anim_type == "CAKeyframeAnimation":
            from ..animation.cakeyframeanimation import CAKeyframeAnimation
            return CAKeyframeAnimation(element)
        elif anim_type == "CAMatchMoveAnimation":
            from ..animation.camatchmoveanimation import CAMatchMoveAnimation
            return CAMatchMoveAnimation(element)
        else:
            print(f"Warning: Unsupported animation type '{anim_type}'. Creating generic CAAnimation.")
            return CAAnimation(element)
    except ImportError:
         print(f"Warning: Could not import class for animation type '{anim_type}'.")
         return None # Or return generic CAAnimation(element)


class CALayer:
    id: Optional[str] = None
    name: Optional[str] = None
    position: Optional[list[str]] = None
    bounds: Optional[list[str]] = None
    hidden: bool = False
    transform: Optional[str] = None
    anchorPoint: Optional[str] = None
    geometryFlipped: bool = False
    opacity: Optional[str] = None
    zPosition: Optional[str] = None
    backgroundColor: Optional[str] = None
    cornerRadius: Optional[str] = None
    layer_class: Optional[str] = None
    content: Optional[Any] = None
    string: Optional[str] = None
    fontSize: Optional[str] = None
    fontFamily: Optional[str] = None
    alignmentMode: Optional[str] = None
    color: Optional[str] = None

    def __init__(self, element: ET.Element):
        if element is None:
            raise ValueError("CALayer cannot be initialized with a None element.")
        self.element = element
        self._parse_attributes()
        self._parse_content()
        self._parse_sublayers()
        self._parse_states()
        self._parse_state_transitions()
        self._parse_animations()

    def _parse_attributes(self):
        """Reads attributes from the XML element."""
        self.id = self.element.get('id')
        self.name = self.element.get('name')
        self.position = self.element.get('position', '0 0').split() # Default to '0 0'
        self.bounds = self.element.get('bounds', '0 0 0 0').split() # Default to '0 0 0 0'
        self.hidden = self.element.get('hidden') == '1' # Check against '1' for True
        self.transform = self.element.get('transform')
        self.anchorPoint = self.element.get('anchorPoint', '0.5 0.5') # Default anchor
        self.geometryFlipped = self.element.get('geometryFlipped') == '1'
        self.opacity = self.element.get('opacity', '1.0') # Default opacity
        self.zPosition = self.element.get('zPosition', '0') # Default zPos
        self.backgroundColor = self.element.get('backgroundColor')
        self.cornerRadius = self.element.get('cornerRadius', '0') # Default radius
        self.layer_class = self.element.get('class', 'CALayer') # Default class

        if self.layer_class == "CATextLayer":
            self.string = self.element.get('string')
            self.fontSize = self.element.get('fontSize')
            self.fontFamily = self.element.get('fontFamily')
            self.alignmentMode = self.element.get('alignmentMode')
            self.color = self.element.get('color')

    def _parse_content(self):
        """Parses the <contents> element."""
        content_element = self.element.find('{*}contents')
        if content_element is not None:
            content_type = content_element.get('type')
            src = content_element.get('src')
            if content_type == "CGImage" and src:
                self.content = CGImage(src)

    def _parse_sublayers(self):
        """Parses <sublayers> and creates child CALayer instances."""
        self.sublayers = {}
        self._sublayerorder = []
        sublayers_element = self.element.find('{*}sublayers')
        if sublayers_element is not None:
            for layer_element in sublayers_element:
                 try:
                     layer_id = layer_element.get('id')
                     if layer_id:
                         self.sublayers[layer_id] = CALayer(layer_element)
                         self._sublayerorder.append(layer_id)
                     else:
                          print(f"Warning: Sublayer found without an 'id' attribute. Skipping.")
                 except Exception as e:
                      print(f"Warning: Failed to initialize sublayer: {e}")


    def _parse_states(self):
        """Parses <states> and creates LKState instances."""
        self.states = {}
        states_element = self.element.find('{*}states')
        if states_element is not None:
            for state_element in states_element:
                try:
                    state_name = state_element.get("name")
                    if state_name:
                         self.states[state_name] = LKState(state_element)
                    else:
                         print("Warning: State found without a 'name' attribute. Skipping.")
                except Exception as e:
                     print(f"Warning: Failed to initialize state: {e}")

    def _parse_state_transitions(self):
        """Parses <stateTransitions> and creates LKStateTransition instances."""
        self.stateTransitions = []
        transitions_element = self.element.find('{*}stateTransitions')
        if transitions_element is not None:
            for transition_element in transitions_element:
                 try:
                     self.stateTransitions.append(LKStateTransition(transition_element))
                 except Exception as e:
                      print(f"Warning: Failed to initialize state transition: {e}")

    def _parse_animations(self):
        """Parses <animations> and creates CAAnimation instances."""
        self.animations = []
        animations_element = self.element.find('{*}animations')
        if animations_element is not None:
            for anim_element in animations_element:
                try:
                    anim_instance = create_animation_instance(anim_element)
                    if anim_instance:
                        self.animations.append(anim_instance)
                except Exception as e:
                     print(f"Warning: Failed to initialize animation: {e}")

    def findlayer(self, uniqueid: str) -> Optional['CALayer']:
        """Recursively finds a sublayer by its ID."""
        if not uniqueid: return None

        if self.id == uniqueid: # Check if the current layer is the target
             return self

        for layer_id in self._sublayerorder:
            possible_layer = self.sublayers.get(layer_id)
            if possible_layer:
                 if possible_layer.id == uniqueid:
                     return possible_layer
                 if hasattr(possible_layer, '_sublayerorder') and possible_layer._sublayerorder:
                     found_layer = possible_layer.findlayer(uniqueid)
                     if found_layer:
                         return found_layer
        return None

    def findanimation(self, keyPath: str) -> Optional[Any]:
        """Finds the first animation matching the keyPath."""
        if not keyPath or not hasattr(self, 'animations'): return None
        for animation in self.animations:
            if hasattr(animation, 'keyPath') and animation.keyPath == keyPath:
                return animation
        return None

    def _safe_set_attrib(self, element: ET.Element, key: str, value: Any):
        """Safely sets element attributes, skipping None and converting types."""
        if value is None:
            return 

        str_value = ""
        if isinstance(value, bool):
            str_value = "1" if value else "0"
        elif isinstance(value, (list, tuple)):
            str_value = " ".join(map(str, value))
        else:
            str_value = str(value)

        element.set(key, str_value)


    def create(self) -> ET.Element:
        """Creates an XML element for this layer and its children."""
        tag_name = self.layer_class if self.layer_class else 'CALayer'
        e = ET.Element(tag_name)

        # set attributes
        self._safe_set_attrib(e, 'id', self.id)
        self._safe_set_attrib(e, 'name', self.name)
        self._safe_set_attrib(e, 'position', self.position)
        self._safe_set_attrib(e, 'bounds', self.bounds)
        self._safe_set_attrib(e, 'hidden', self.hidden)
        self._safe_set_attrib(e, 'transform', self.transform)
        self._safe_set_attrib(e, 'anchorPoint', self.anchorPoint)
        self._safe_set_attrib(e, 'geometryFlipped', self.geometryFlipped)
        self._safe_set_attrib(e, 'opacity', self.opacity)
        self._safe_set_attrib(e, 'zPosition', self.zPosition)
        self._safe_set_attrib(e, 'backgroundColor', self.backgroundColor)
        self._safe_set_attrib(e, 'cornerRadius', self.cornerRadius)
        if self.layer_class and self.layer_class != 'CALayer':
             self._safe_set_attrib(e, 'class', self.layer_class)

        # CATextLayer specific attributes
        if tag_name == "CATextLayer":
            self._safe_set_attrib(e, 'string', self.string)
            self._safe_set_attrib(e, 'fontSize', self.fontSize)
            self._safe_set_attrib(e, 'fontFamily', self.fontFamily)
            self._safe_set_attrib(e, 'alignmentMode', self.alignmentMode)
            self._safe_set_attrib(e, 'color', self.color)

        if isinstance(self.content, CGImage) and self.content.src is not None:
            content_element = ET.SubElement(e, 'contents')
            content_element.set('type', 'CGImage') # Assuming type is always CGImage for now
            self._safe_set_attrib(content_element, 'src', self.content.src)

        # Create <sublayers> element and append children
        if hasattr(self, '_sublayerorder') and self._sublayerorder:
            sublayers_element = ET.SubElement(e, 'sublayers')
            for layer_id in self._sublayerorder:
                sublayer = self.sublayers.get(layer_id)
                if sublayer:
                    sublayers_element.append(sublayer.create())

        # Create <states> element
        if hasattr(self, 'states') and self.states:
            states_element = ET.SubElement(e, 'states')
            for state_obj in self.states.values():
                if state_obj and hasattr(state_obj, 'create'):
                    states_element.append(state_obj.create())

        # Create <stateTransitions> element
        if hasattr(self, 'stateTransitions') and self.stateTransitions:
            transitions_element = ET.SubElement(e, 'stateTransitions')
            for transition_obj in self.stateTransitions:
                if transition_obj and hasattr(transition_obj, 'create'):
                    transitions_element.append(transition_obj.create())

        # Create <animations> element
        if hasattr(self, 'animations') and self.animations:
            animations_element = ET.SubElement(e, 'animations')
            for animation_obj in self.animations:
                if animation_obj and hasattr(animation_obj, 'create'):
                     animations_element.append(animation_obj.create())

        return e