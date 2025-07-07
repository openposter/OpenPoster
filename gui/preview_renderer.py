from PySide6.QtCore import QRectF, QPointF, Qt
from PySide6.QtGui import QTransform
from PySide6.QtWidgets import QGraphicsRectItem, QGraphicsPixmapItem, QGraphicsTextItem
from PySide6.QtGui import QPen, QBrush, QColor

class PreviewRenderer:
    def __init__(self, window):
        self.window = window
        self.scene = window.scene
        self.animation_helper = window._applyAnimation
        self.assets = window._assets
        self.load_image = window.loadImage
        self.parse_transform = window.parseTransform
        self.parse_color = window.parseColor
        self.animations = []

    def render_preview(self, root_layer, target_state=None):
        if hasattr(self.animation_helper, 'animations'):
            self.animation_helper.animations.clear()
        self.animations = []
        self.scene.clear()
        default_w, default_h = 1000, 1000
        try:
            b = root_layer.bounds
            root_w = float(b[2])
            root_h = float(b[3])
        except Exception:
            root_w, root_h = default_w, default_h
        bounds = QRectF(0, 0, root_w, root_h)

        border = QGraphicsRectItem(bounds)
        border.setPen(QPen(QColor(0, 0, 0), 2))
        border.setBrush(QBrush(Qt.transparent))
        self.scene.addItem(border)

        base_state = None
        if hasattr(root_layer, 'states') and root_layer.states and 'Base State' in root_layer.states:
            base_state = root_layer.states['Base State']

        self.render_layer(root_layer, QPointF(0, 0), QTransform(), base_state, target_state)

        rect = self.scene.itemsBoundingRect()
        self.scene.setSceneRect(rect)

        if hasattr(self.animation_helper, 'animations'):
            self.animations = list(self.animation_helper.animations)
        return self.animations

    def render_layer(self, layer, parent_pos, parent_transform, base_state=None, target_state=None):
        if getattr(layer, 'hidden', False):
            return
        if layer.id == self.window.cafile.rootlayer.id:
            for lid in getattr(layer, '_sublayerorder', []):
                sub = layer.sublayers.get(lid)
                if sub:
                    self.render_layer(sub, QPointF(0, 0), parent_transform, base_state, target_state)
            return

        pos = QPointF(0, 0)
        if hasattr(layer, 'position') and layer.position:
            try:
                pos = QPointF(float(layer.position[0]), float(layer.position[1]))
            except Exception:
                pass

        bounds = QRectF(0, 0, 100, 100)
        if hasattr(layer, 'bounds') and layer.bounds:
            try:
                x, y, w, h = map(float, layer.bounds[:4])
                bounds = QRectF(x, y, w, h)
            except Exception:
                pass

        transform = QTransform(parent_transform)
        if hasattr(layer, 'transform') and layer.transform:
            transform = transform * self.parse_transform(layer.transform)

        anchor = QPointF(0.5, 0.5)
        if hasattr(layer, 'anchorPoint') and layer.anchorPoint:
            try:
                ax, ay = map(float, layer.anchorPoint.split()[:2])
                anchor = QPointF(ax, ay)
            except Exception:
                pass

        zpos = float(getattr(layer, 'zPosition', 0) or 0)
        try:
            opacity = float(layer.opacity) if hasattr(layer, 'opacity') else 1.0
        except Exception:
            opacity = 1.0
        bg_color = None
        if hasattr(layer, 'backgroundColor') and layer.backgroundColor:
            bg_color = self.parse_color(layer.backgroundColor)
        try:
            radius = float(layer.cornerRadius) if hasattr(layer, 'cornerRadius') else 0
        except Exception:
            radius = 0

        for state in (base_state, target_state):
            if state and hasattr(state, 'elements'):
                for el in state.elements:
                    if getattr(el, '__class__', None).__name__ == 'LKStateSetValue' and el.targetId == layer.id:
                        key, val = el.keyPath, el.value
                        try:
                            if key == 'position.x': pos.setX(float(val))
                            elif key == 'position.y': pos.setY(float(val))
                            elif key == 'transform': transform = self.parse_transform(val) * parent_transform
                            elif key == 'opacity': opacity = float(val)
                            elif key == 'zPosition': zpos = float(val)
                            elif key == 'backgroundColor': bg_color = self.parse_color(val)
                            elif key == 'cornerRadius': radius = float(val)
                        except Exception:
                            pass

        has_content = False
        missing_asset = False
        is_text = getattr(layer, 'layer_class', '') == 'CATextLayer'
        if is_text:
            item = QGraphicsTextItem()
            text = getattr(layer, 'string', '') or 'Text Layer'
            item.setPlainText(text)
            if hasattr(layer, 'fontSize') and layer.fontSize:
                try:
                    f = item.font()
                    f.setPointSizeF(float(layer.fontSize))
                    item.setFont(f)
                except Exception:
                    pass
            if hasattr(layer, 'fontFamily') and layer.fontFamily:
                f = item.font()
                f.setFamily(layer.fontFamily)
                item.setFont(f)
            if hasattr(layer, 'color') and layer.color:
                c = self.parse_color(layer.color)
                if c: item.setDefaultTextColor(c)
            item.setTransformOriginPoint(bounds.width()*anchor.x(), bounds.height()*anchor.y())
            item.setPos(QPointF(pos.x() - bounds.width()*anchor.x(), pos.y() - bounds.height()*anchor.y()))
            item.setTransform(transform)
            item.setZValue(zpos)
            item.setOpacity(opacity)
            item.setData(0, layer.id)
            item.setData(1, 'Layer')
            self.scene.addItem(item)
            has_content = True
            self.apply_default_animations(layer, item)
        elif hasattr(layer, '_content') and layer._content is not None:
            src = getattr(layer.content, 'src', None)
            if src:
                self.assets.cafilepath = self.window.cafilepath
                self.assets.cachedImages = self.window.cachedImages
                pix = self.load_image(src)
                self.window.cachedImages = self.assets.cachedImages
                if not pix and src in self.window.missing_assets:
                    missing_asset = True
                if pix:
                    pitem = QGraphicsPixmapItem()
                    pitem.setPixmap(pix)
                    sx = bounds.width()/pix.width() if pix.width()>0 else 1
                    sy = bounds.height()/pix.height() if pix.height()>0 else 1
                    tf = QTransform().scale(sx, sy)
                    pitem.setTransform(tf*transform)
                    ww, hh = pix.width()*sx, pix.height()*sy
                    pitem.setTransformOriginPoint(ww*anchor.x(), hh*anchor.y())
                    pitem.setPos(QPointF(pos.x() - ww*anchor.x(), pos.y() - hh*anchor.y()))
                    pitem.setTransformationMode(Qt.SmoothTransformation)
                    pitem.setZValue(zpos)
                    pitem.setOpacity(opacity)
                    pitem.setData(0, layer.id)
                    pitem.setData(1, 'Layer')
                    self.scene.addItem(pitem)
                    has_content = True
                    self.apply_default_animations(layer, pitem)

        if not has_content:
            rect = QGraphicsRectItem(bounds)
            rect.setTransformOriginPoint(bounds.width()*anchor.x(), bounds.height()*anchor.y())
            rect.setPos(QPointF(pos.x() - bounds.width()*anchor.x(), pos.y() - bounds.height()*anchor.y()))
            rect.setTransform(transform)
            rect.setZValue(zpos)
            rect.setOpacity(opacity)
            pen = QPen(QColor(200,200,200,180),1)
            brush = QBrush(QColor(180,180,180,30))
            if layer.id == self.window.cafile.rootlayer.id:
                pen = QPen(QColor(0,0,0,200),1.5)
                brush = QBrush(Qt.transparent)
            if missing_asset:
                pen = QPen(QColor(255,0,0,200),2)
                brush = QBrush(QColor(255,200,200,30))
            if bg_color:
                brush = QBrush(bg_color)
            if radius>0:
                pen.setStyle(Qt.DashLine)
            rect.setPen(pen)
            rect.setBrush(brush)
            rect.setData(0, layer.id)
            rect.setData(1, 'Layer')
            self.scene.addItem(rect)
            self.apply_default_animations(layer, rect)

        for lid in getattr(layer, '_sublayerorder', []):
            sub = layer.sublayers.get(lid)
            if sub:
                self.render_layer(sub, pos, transform, base_state, target_state)

    def apply_default_animations(self, layer, item):
        if not hasattr(layer, 'animations') or not layer.animations:
            return
        for anim in layer.animations:
            if getattr(anim, 'type', None) == 'CAKeyframeAnimation':
                self.animation_helper.applyKeyframeAnimationToItem(item, anim.keyPath, anim)

    def highlight_layer(self, layer):
        self.scene.clearSelection()
        for item in self.scene.items():
            if hasattr(item, 'data') and item.data(0)==layer.id and item.data(1)=='Layer':
                if isinstance(item, QGraphicsRectItem):
                    if layer.id==self.window.cafile.rootlayer.id:
                        item.setPen(QPen(QColor(0,120,215,255),2))
                    else:
                        item.setPen(QPen(QColor(0,120,215,200),1.5))
                    item.setSelected(True)
                    self.window.ui.graphicsView.centerOn(item)
        for item in self.scene.items():
            if hasattr(item,'data') and item.data(0)==layer.id+'_name':
                item.setDefaultTextColor(QColor(0,120,215))

    def highlight_animation(self, layer, animation):
        self.highlight_layer(layer) 