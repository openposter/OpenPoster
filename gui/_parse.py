from PySide6.QtGui import QTransform, QColor

class Parse:
    def __init__(self):
        pass

    # TRANSFORMS
    def parseTransform(self, transform_str) -> QTransform:
        transform = QTransform()
        if not transform_str:
            return transform
            
        try:
            if "scale" in transform_str:
                scale_parts = transform_str.split("scale(")[1].split(")")[0].split(",")
                scale_x = float(scale_parts[0].strip())
                scale_y = float(scale_parts[1].strip())
                transform.scale(scale_x, scale_y)
                
            if "rotate" in transform_str:
                rotation_str = transform_str.split("rotate(")[1].split("deg")[0].strip()
                rotation_angle = float(rotation_str)
                transform.rotate(rotation_angle)
                
            if "translate" in transform_str:
                translate_parts = transform_str.split("translate(")[1].split(")")[0].split(",")
                translate_x = float(translate_parts[0].strip())
                translate_y = float(translate_parts[1].strip())
                transform.translate(translate_x, translate_y)
        except:
            pass
            
        return transform
    
    # COLORS
    def parseColor(self, color_str) -> QColor:
        if not color_str:
            return None
            
        try:
            if color_str.lower() in ["black", "white", "red", "green", "blue", "yellow"]:
                return QColor(color_str)
                
            if color_str.startswith("rgb("):
                rgb = color_str.replace("rgb(", "").replace(")", "").split(",")
                if len(rgb) >= 3:
                    r = int(rgb[0].strip())
                    g = int(rgb[1].strip())
                    b = int(rgb[2].strip())
                    return QColor(r, g, b)
                    
            if color_str.startswith("rgba("):
                rgba = color_str.replace("rgba(", "").replace(")", "").split(",")
                if len(rgba) >= 4:
                    r = int(rgba[0].strip())
                    g = int(rgba[1].strip())
                    b = int(rgba[2].strip())
                    a = int(float(rgba[3].strip()) * 255)
                    return QColor(r, g, b, a)
                    
            if color_str.startswith("#"):
                return QColor(color_str)
            if " " in color_str and all(p.replace(".", "", 1).isdigit() for p in color_str.split()):
                parts = color_str.split()
                r = int(float(parts[0])); g = int(float(parts[1])); b = int(float(parts[2]))
                a = float(parts[3]) if len(parts) == 4 else 1.0
                return QColor(r, g, b, int(a * 255))
        except:
            pass
            
        return QColor(150, 150, 150, 100)