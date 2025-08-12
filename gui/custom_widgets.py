from PySide6.QtCore import Qt, QPointF, QRectF, Signal, QObject, QTimer, QEvent
from PySide6.QtGui import QColor, QPen, QBrush, QTransform, QCursor, QPainterPath, QPainter
from PySide6.QtWidgets import QGraphicsView, QGraphicsScene, QGraphicsRectItem, QGraphicsEllipseItem, QGraphicsItem, QGraphicsPathItem, QApplication, QStyleOptionGraphicsItem, QWidget, QGraphicsTextItem, QGraphicsPixmapItem
import math
import platform

class HandleType:
    TopLeft = 0
    Top = 1
    TopRight = 2
    Right = 3
    BottomRight = 4
    Bottom = 5
    BottomLeft = 6
    Left = 7
    Rotation = 8

class ResizeHandle(QGraphicsRectItem):
    """Visual handle for resizing operations"""
    def __init__(self, handle_type, parent=None):
        super().__init__(-10, -10, 20, 20, parent)
        self.handle_type = handle_type

        self.visual_rect = QRectF(-4, -4, 8, 8)

        self.setBrush(Qt.NoBrush)
        self.setPen(Qt.NoPen)

        self.setFlag(QGraphicsItem.ItemIgnoresTransformations, True)
        self.setFlag(QGraphicsItem.ItemIsMovable, False)
        self.setFlag(QGraphicsItem.ItemSendsScenePositionChanges, True)
        self.setAcceptHoverEvents(True)
        
        cursor_map = {
            HandleType.TopLeft: Qt.SizeFDiagCursor,
            HandleType.Top: Qt.SizeVerCursor,
            HandleType.TopRight: Qt.SizeBDiagCursor,
            HandleType.Right: Qt.SizeHorCursor,
            HandleType.BottomRight: Qt.SizeFDiagCursor,
            HandleType.Bottom: Qt.SizeVerCursor,
            HandleType.BottomLeft: Qt.SizeBDiagCursor,
            HandleType.Left: Qt.SizeHorCursor,
            HandleType.Rotation: Qt.PointingHandCursor
        }
        self.handle_cursor = QCursor(cursor_map.get(handle_type, Qt.ArrowCursor))

    def paint(self, painter, option, widget):
        painter.setBrush(QBrush(QColor(100, 150, 255)))
        painter.setPen(QPen(QColor(50, 100, 200), 1))
        painter.drawRect(self.visual_rect)

    def hoverMoveEvent(self, event):
        if self.visual_rect.contains(event.pos()):
            self.setCursor(self.handle_cursor)
        else:
            self.unsetCursor()
        super().hoverMoveEvent(event)

    def hoverLeaveEvent(self, event):
        self.unsetCursor()
        super().hoverLeaveEvent(event)

    def shape(self):
        path = QPainterPath()
        path.addRect(self.rect())
        return path

class EditableGraphicsItem(QObject):
    """A wrapper class that adds editing capabilities to QGraphicsItems"""
    itemChanged = Signal(QGraphicsItem)
    transformChanged = Signal(QTransform)
    itemSelected = Signal(str)
    editFinished = Signal(QGraphicsItem)
    
    def __init__(self, item, parent=None):
        super(EditableGraphicsItem, self).__init__(parent)
        self.item = item
        self.handles = {}
        self.boundingRect = None
        self.rotationHandle = None
        self.boundingBoxItem = None
        self.layerNameItem = None
        self.isEditing = False
        self.originalTransform = QTransform(item.transform())
        self.initialClickPos = QPointF()
        self.initialItemPos = QPointF()
        self.initialItemTransform = QTransform()
        self.initialBoundingRect = QRectF()
        self.initialRotation = 0
        self.currentRotation = 0
        self.handleSize = 8
        self.rotateHandleSize = 10
        self.rotateHandleOffset = 20
        self.currentHandle = None
        self.aspectRatioLocked = False
        
        self.item.setFlag(QGraphicsItem.ItemIsSelectable, True)
        self.item.setFlag(QGraphicsItem.ItemIsMovable, True)
        self.item.setAcceptHoverEvents(True)
    
    def setupBoundingBox(self):
        """Create bounding box and handles for the item"""
        if not self.item.scene():
            return
            
        self.removeBoundingBox()
            
        scene = self.item.scene()
        rect = self.item.boundingRect()
        
        # Layer Name
        if hasattr(self.item, 'data') and self.item.data(0):
            layer_id = self.item.data(0)
            main_window = next((w for w in QApplication.topLevelWidgets() if 'MainWindow' in str(type(w))), None)
            if main_window and hasattr(main_window, 'cafile'):
                layer = main_window.cafile.rootlayer.findlayer(layer_id)
                if layer and hasattr(layer, 'name'):
                    self.layerNameItem = QGraphicsTextItem(layer.name)
                    self.layerNameItem.setParentItem(self.item)
                    self.layerNameItem.setDefaultTextColor(QColor(255, 255, 255, 200))
                    font = self.layerNameItem.font()
                    font.setPointSize(10)
                    self.layerNameItem.setFont(font)
                    self.layerNameItem.setPos(rect.x(), rect.y() - 20)
                    self.layerNameItem.setFlag(QGraphicsItem.ItemIgnoresTransformations, False)
        
        self.boundingBoxItem = QGraphicsRectItem(rect)
        self.boundingBoxItem.setPen(QPen(QColor(100, 150, 255), 1, Qt.DashLine))
        self.boundingBoxItem.setBrush(QBrush(Qt.transparent))
        self.boundingBoxItem.setParentItem(self.item)
        self.boundingBoxItem.setFlag(QGraphicsItem.ItemIgnoresTransformations, False)
        
        handle_positions = [
            (rect.topLeft(), HandleType.TopLeft),
            (QPointF(rect.center().x(), rect.top()), HandleType.Top),
            (rect.topRight(), HandleType.TopRight),
            (QPointF(rect.right(), rect.center().y()), HandleType.Right),
            (rect.bottomRight(), HandleType.BottomRight),
            (QPointF(rect.center().x(), rect.bottom()), HandleType.Bottom),
            (rect.bottomLeft(), HandleType.BottomLeft),
            (QPointF(rect.left(), rect.center().y()), HandleType.Left),
        ]
        
        for pos, handle_type in handle_positions:
            handle = ResizeHandle(handle_type)
            handle.setPos(pos)
            handle.setParentItem(self.item)
            handle.setFlag(QGraphicsItem.ItemIgnoresParentOpacity, True)
            self.handles[handle_type] = handle
        
        rotation_pos = QPointF(rect.center().x(), rect.top() - self.rotateHandleOffset)
        self.rotationHandle = ResizeHandle(HandleType.Rotation)
        self.rotationHandle.setPos(rotation_pos)
        self.rotationHandle.setParentItem(self.item)
        self.rotationHandle.setBrush(QBrush(QColor(255, 100, 100)))
        self.rotationHandle.setPen(QPen(QColor(200, 50, 50), 1))
        self.rotationHandle.setFlag(QGraphicsItem.ItemIgnoresParentOpacity, True)
    
    def removeBoundingBox(self):
        """Remove bounding box and handles"""
        try:
            if self.layerNameItem and not self.isItemDeleted(self.layerNameItem):
                scene = self.layerNameItem.scene()
                if scene:
                    scene.removeItem(self.layerNameItem)
                self.layerNameItem = None
        except (RuntimeError, AttributeError):
            self.layerNameItem = None

        try:
            if self.boundingBoxItem and not self.isItemDeleted(self.boundingBoxItem):
                scene = self.boundingBoxItem.scene()
                if scene:
                    scene.removeItem(self.boundingBoxItem)
                self.boundingBoxItem = None
        except (RuntimeError, AttributeError):
            self.boundingBoxItem = None
        
        handles_to_remove = list(self.handles.values())
        for handle in handles_to_remove:
            try:
                if not self.isItemDeleted(handle):
                    scene = handle.scene()
                    if scene:
                        scene.removeItem(handle)
            except (RuntimeError, AttributeError):
                pass
        self.handles.clear()
        
        try:
            if self.rotationHandle and not self.isItemDeleted(self.rotationHandle):
                scene = self.rotationHandle.scene()
                if scene:
                    scene.removeItem(self.rotationHandle)
                self.rotationHandle = None
        except (RuntimeError, AttributeError):
            self.rotationHandle = None

    def isItemDeleted(self, item):
        """Check if a QGraphicsItem has been deleted by Qt"""
        try:
            _ = item.pos()
            return False
        except (RuntimeError, AttributeError):
            return True
    
    def updateBoundingBox(self):
        """Update the position of bounding box and handles after item moves"""
        try:
            if self.isItemDeleted(self.item):
                # If the wrapped item itself is deleted, remove all adornments and stop.
                if self.boundingBoxItem or self.handles or self.rotationHandle:
                    print(f"Main item {id(self.item)} deleted. Removing its bounding box and handles.")
                self.removeBoundingBox()
                return

            # Ensure our bounding box graphics item is still valid and exists
            if not self.boundingBoxItem or self.isItemDeleted(self.boundingBoxItem):
                if self.boundingBoxItem and self.isItemDeleted(self.boundingBoxItem):
                    # It was deleted by Qt, so nullify our reference.
                    self.boundingBoxItem = None
                # Cannot update if the box item itself is gone.
                # setupBoundingBox would be needed to recreate it if desired.
                # print(f"BoundingBoxItem for item {id(self.item)} is None or deleted. Cannot update.")
                return 

            rect = self.item.boundingRect()
            self.boundingBoxItem.setRect(rect)
            
            handle_positions = {
                HandleType.TopLeft: rect.topLeft(),
                HandleType.Top: QPointF(rect.center().x(), rect.top()),
                HandleType.TopRight: rect.topRight(),
                HandleType.Right: QPointF(rect.right(), rect.center().y()),
                HandleType.BottomRight: rect.bottomRight(),
                HandleType.Bottom: QPointF(rect.center().x(), rect.bottom()),
                HandleType.BottomLeft: rect.bottomLeft(),
                HandleType.Left: QPointF(rect.left(), rect.center().y()),
            }
            
            active_handle_types = list(self.handles.keys()) # Iterate over a copy of keys
            for handle_type in active_handle_types:
                handle = self.handles.get(handle_type)
                if handle:
                    if not self.isItemDeleted(handle):
                        handle.setPos(handle_positions[handle_type])
                    else:
                        # Handle was deleted by Qt, remove our reference
                        del self.handles[handle_type]
            
            if self.rotationHandle:
                if not self.isItemDeleted(self.rotationHandle):
                    rotation_pos = QPointF(rect.center().x(), rect.top() - self.rotateHandleOffset)
                    self.rotationHandle.setPos(rotation_pos)
                    if self.layerNameItem:
                        self.layerNameItem.setPos(rect.x(), rect.y() - self.layerNameItem.boundingRect().height() - 5)
                else:
                    # Rotation handle was deleted by Qt
                    self.rotationHandle = None
                
        except (RuntimeError, AttributeError) as e:
            print(f"Error during updateBoundingBox for item {id(self.item if self.item else 'None')}: {e}")
            if self.item and self.isItemDeleted(self.item):
                print(f"Main item {id(self.item)} confirmed deleted after error. Removing bounding box.")
                self.removeBoundingBox()
            else:
                print(f"Error in updateBoundingBox, but main item not detected as deleted or item is None. Bounding box NOT removed solely due to this error.")
    
    def startEdit(self, handle_type, handle_pos):
        """Start edit operation (resize or rotate)"""
        self.currentHandle = handle_type
        self.isEditing = True
        self.initialClickPos = handle_pos
        self.initialItemPos = self.item.pos()
        self.initialBoundingRect = self.item.boundingRect()
        self.initialItemTransform = QTransform(self.item.transform())
        self.initialSceneTransform = self.item.sceneTransform()
        self.initialRotation = self.getItemRotation()
        
        if handle_type == HandleType.Rotation:
            center = self.item.mapToScene(self.initialBoundingRect.center())
            dx = handle_pos.x() - center.x()
            dy = handle_pos.y() - center.y()
            self.initialAngle = math.degrees(math.atan2(dy, dx))
        
        if hasattr(self.item, 'rect'):
            self.originalRect = self.item.rect()
        else:
            self.originalRect = self.item.boundingRect()
        
        if hasattr(self.item, 'path'):
            self.original_path_at_drag_start = self.item.path()
    
    def handleEditOperation(self, new_pos):
        if self.currentHandle is None:
            return

        if self.currentHandle == HandleType.Rotation:
            self.handleRotation(new_pos)
        else:
            self.handleResize(new_pos)
        
        self.updateBoundingBox()
        self.itemChanged.emit(self.item)
    
    def handleRotation(self, mouse_pos):
        center_scene = self.item.mapToScene(self.item.boundingRect().center())
        
        initial_vec = self.initialClickPos - center_scene
        current_vec = mouse_pos - center_scene
        
        angle_delta = math.degrees(math.atan2(current_vec.y(), current_vec.x())) - math.degrees(math.atan2(initial_vec.y(), initial_vec.x()))
        
        transform = QTransform(self.initialItemTransform)

        rotation_center = self.item.boundingRect().center()

        transform.translate(rotation_center.x(), rotation_center.y())
        transform.rotate(angle_delta)
        transform.translate(-rotation_center.x(), -rotation_center.y())
        
        self.item.setTransform(transform)

    def handleResize(self, mouse_pos_scene):
        new_transform = QTransform(self.initialItemTransform)

        inv_initial_transform, _ = self.initialSceneTransform.inverted()
        
        initial_local_pos = inv_initial_transform.map(self.initialClickPos)
        current_local_pos = inv_initial_transform.map(mouse_pos_scene)
        
        delta = current_local_pos - initial_local_pos

        scale_x = 1.0
        scale_y = 1.0
        
        current_w = self.initialBoundingRect.width()
        current_h = self.initialBoundingRect.height()

        if self.currentHandle in [HandleType.TopLeft, HandleType.Left, HandleType.BottomLeft]:
            if current_w - delta.x() > 0:
                scale_x = (current_w - delta.x()) / current_w
        elif self.currentHandle in [HandleType.TopRight, HandleType.Right, HandleType.BottomRight]:
            if current_w + delta.x() > 0:
                scale_x = (current_w + delta.x()) / current_w

        if self.currentHandle in [HandleType.TopLeft, HandleType.Top, HandleType.TopRight]:
            if current_h - delta.y() > 0:
                scale_y = (current_h - delta.y()) / current_h
        elif self.currentHandle in [HandleType.BottomLeft, HandleType.Bottom, HandleType.BottomRight]:
            if current_h + delta.y() > 0:
                scale_y = (current_h + delta.y()) / current_h

        anchor_point = QPointF()
        if self.currentHandle == HandleType.TopLeft:
            anchor_point = self.initialBoundingRect.bottomRight()
        elif self.currentHandle == HandleType.Top:
            anchor_point = QPointF(self.initialBoundingRect.center().x(), self.initialBoundingRect.bottom())
        elif self.currentHandle == HandleType.TopRight:
            anchor_point = self.initialBoundingRect.bottomLeft()
        elif self.currentHandle == HandleType.Right:
            anchor_point = QPointF(self.initialBoundingRect.left(), self.initialBoundingRect.center().y())
        elif self.currentHandle == HandleType.BottomRight:
            anchor_point = self.initialBoundingRect.topLeft()
        elif self.currentHandle == HandleType.Bottom:
            anchor_point = QPointF(self.initialBoundingRect.center().x(), self.initialBoundingRect.top())
        elif self.currentHandle == HandleType.BottomLeft:
            anchor_point = self.initialBoundingRect.topRight()
        elif self.currentHandle == HandleType.Left:
            anchor_point = QPointF(self.initialBoundingRect.right(), self.initialBoundingRect.center().y())

        new_transform.translate(anchor_point.x(), anchor_point.y())
        new_transform.scale(scale_x, scale_y)
        new_transform.translate(-anchor_point.x(), -anchor_point.y())

        self.item.setTransform(new_transform)

    def endEdit(self):
        self.isEditing = False
        self.currentHandle = None
        self.itemChanged.emit(self.item)
        self.editFinished.emit(self.item)
    
    def getItemRotation(self):
        transform = self.item.transform()
        return math.degrees(math.atan2(transform.m12(), transform.m11()))

class CheckerboardGraphicsScene(QGraphicsScene):
    itemSelectedOnCanvas = Signal(str)
    
    def __init__(self, parent=None):
        super(CheckerboardGraphicsScene, self).__init__(parent)
        self.backgroundColor1 = QColor(200, 200, 200)
        self.backgroundColor2 = QColor(230, 230, 230)
        self.checkerboardSize = 20
        self.editMode = False
        self.currentEditableItem = None
        self.activeHandle = None
        self.isDragging = False
        self.lastMousePos = QPointF()
        self.editableItems = {}

    def setBackgroundColor(self, color1, color2):
        """Set the background colors for the checkerboard pattern"""
        self.backgroundColor1 = color1
        self.backgroundColor2 = color2
        self.update()

    def drawBackground(self, painter, rect):
        super(CheckerboardGraphicsScene, self).drawBackground(painter, rect)
        
        painter.save()
        painter.fillRect(rect, self.backgroundColor1)
        
        left = int(rect.left()) - (int(rect.left()) % self.checkerboardSize)
        top = int(rect.top()) - (int(rect.top()) % self.checkerboardSize)
        
        for x in range(left, int(rect.right()), self.checkerboardSize):
            for y in range(top, int(rect.bottom()), self.checkerboardSize):
                if (x // self.checkerboardSize + y // self.checkerboardSize) % 2 == 0:
                    painter.fillRect(x, y, self.checkerboardSize, self.checkerboardSize, self.backgroundColor2)
        
        painter.restore()
    
    def setEditMode(self, enabled):
        """Enable or disable edit mode"""
        self.editMode = enabled
        
        if enabled:
            items_to_cleanup = []
            for item, editable_item in self.editableItems.items():
                try:
                    if not self.isItemDeleted(item):
                        editable_item.setupBoundingBox()
                    else:
                        items_to_cleanup.append(item)
                except (RuntimeError, AttributeError):
                    items_to_cleanup.append(item)
            
            for item in items_to_cleanup:
                if item in self.editableItems:
                    del self.editableItems[item]
        else:
            self.deselectAllItems()
            self.currentEditableItem = None

    def makeItemEditable(self, item):
        """Make a graphics item editable"""
        if item not in self.editableItems:
            editable_item = EditableGraphicsItem(item, self)
            self.editableItems[item] = editable_item
            
            editable_item.itemChanged.connect(self.onItemChanged)
            editable_item.itemSelected.connect(self.itemSelectedOnCanvas.emit)
            
            return editable_item
        return self.editableItems[item]

    def mousePressEvent(self, event):
        handle = self.getHandleAt(event.scenePos())
        if handle and self.currentEditableItem:
            self.currentEditableItem.startEdit(handle.handle_type, event.scenePos())
            self.isDragging = True
            event.accept()
            return

        super().mousePressEvent(event)

        items_at_pos = self.items(event.scenePos())
        top_item = next((item for item in items_at_pos if item.data(1) == "Layer" and item.flags() & QGraphicsItem.ItemIsSelectable), None)

        if top_item:
            if not self.currentEditableItem or self.currentEditableItem.item != top_item:
                self.selectItem(top_item)
        elif not event.isAccepted():
            self.deselectAllItems()

    def getHandleAt(self, pos):
        if not self.currentEditableItem:
            return None
        items_at_pos = self.items(pos)
        for item in items_at_pos:
            if isinstance(item, ResizeHandle):
                return item
        return None

    def mouseMoveEvent(self, event):
        if self.isDragging and self.currentEditableItem:
            self.currentEditableItem.handleEditOperation(event.scenePos())
            self.onItemChanged(self.currentEditableItem.item)
            event.accept()
        else:
            super().mouseMoveEvent(event)
            if self.currentEditableItem and event.buttons() & Qt.LeftButton:
                self.currentEditableItem.itemChanged.emit(self.currentEditableItem.item)

    def mouseReleaseEvent(self, event):
        if self.isDragging and self.currentEditableItem:
            self.currentEditableItem.endEdit()
            self.isDragging = False
            event.accept()
        else:
            super().mouseReleaseEvent(event)
            if self.currentEditableItem:
                self.currentEditableItem.editFinished.emit(self.currentEditableItem.item)

    def selectItem(self, item):
        if self.isItemDeleted(item):
            return

        if self.currentEditableItem and self.currentEditableItem.item != item:
            self.deselectAllItems()
            
        if not self.currentEditableItem or self.currentEditableItem.item != item:
            self.currentEditableItem = self.makeItemEditable(item)
            if self.currentEditableItem:
                self.currentEditableItem.item.setSelected(True)
                self.currentEditableItem.setupBoundingBox()
                layer_id = item.data(0)
                if layer_id:
                    self.itemSelectedOnCanvas.emit(layer_id)
            else:
                self.deselectAllItems()
                
    def deselectAllItems(self):
        if self.currentEditableItem and not self.isItemDeleted(self.currentEditableItem.item):
            self.currentEditableItem.removeBoundingBox()
            self.currentEditableItem.item.setSelected(False)
        self.currentEditableItem = None

    def isItemDeleted(self, item):
        try:
            _ = item.pos()
            return False
        except (RuntimeError, AttributeError):
            return True
    
    def onItemChanged(self, item):
        """Handle item change events"""
        pass

class CustomGraphicsView(QGraphicsView):
    def __init__(self, parent=None, min_zoom=0.05, max_zoom=10.0):
        super(CustomGraphicsView, self).__init__(parent)
        self.min_zoom = min_zoom
        self.max_zoom = max_zoom
        self.current_zoom_level = 1.0
        self.setRenderHint(QPainter.Antialiasing)
        self.setRenderHint(QPainter.SmoothPixmapTransform)
        self.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.AnchorUnderMouse)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setDragMode(QGraphicsView.ScrollHandDrag)
        
        self.is_panning = False
        self.last_pan_point = QPointF()
        
        self.editMode = False
        
        self.gesture_active = False
        self.initial_pinch_distance = 0.0
        self.initial_zoom_level = 1.0
        
        self.grabGesture(Qt.PinchGesture)
        
        self.setViewportUpdateMode(QGraphicsView.FullViewportUpdate)

    def setEditMode(self, enabled):
        """Enable or disable edit mode"""
        self.editMode = enabled
        
        if enabled:
            self.setDragMode(QGraphicsView.NoDrag)
        else:
            self.setDragMode(QGraphicsView.ScrollHandDrag)
        
        if self.scene() and hasattr(self.scene(), 'setEditMode'):
            self.scene().setEditMode(enabled)

    def wheelEvent(self, event):
        if event.modifiers() == Qt.ControlModifier:
            self.handleZoom(event.angleDelta().y())
            event.accept()
        elif event.modifiers() == Qt.ShiftModifier:
            h_scroll = self.horizontalScrollBar()
            h_scroll.setValue(h_scroll.value() - event.angleDelta().y())
            event.accept()
        else:
            v_scroll = self.verticalScrollBar()
            v_scroll.setValue(v_scroll.value() - event.angleDelta().y())
            event.accept()
            
    def handleZoom(self, delta):
        if delta > 0:
            self.scale(1.1, 1.1)
        else:
            self.scale(0.9, 0.9)

    def mousePressEvent(self, event):
        if not self.editMode and event.button() == Qt.LeftButton:
            self.is_panning = True
            self.last_pan_point = event.pos()
            self.setCursor(Qt.ClosedHandCursor)
            event.accept()
        else:
            super(CustomGraphicsView, self).mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self.is_panning:
            delta = event.pos() - self.last_pan_point
            self.horizontalScrollBar().setValue(self.horizontalScrollBar().value() - delta.x())
            self.verticalScrollBar().setValue(self.verticalScrollBar().value() - delta.y())
            self.last_pan_point = event.pos()
            event.accept()
        else:
            super(CustomGraphicsView, self).mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if self.is_panning:
            self.is_panning = False
            self.setCursor(Qt.ArrowCursor)
            event.accept()
        else:
            super(CustomGraphicsView, self).mouseReleaseEvent(event)
    
    def event(self, event):
        if event.type() == QEvent.Gesture:
            try:
                return self.handleGestureEvent(event)
            except Exception as e:
                print(f"Gesture handling error: {e}")
                
        return super(CustomGraphicsView, self).event(event)
    
    def handleGestureEvent(self, event):
        """Handle touch gesture events for zooming on macOS"""
        try:
            if hasattr(Qt, 'PinchGesture'):
                pinch_gesture = event.gesture(Qt.PinchGesture)
                if pinch_gesture:
                    self.handlePinchGesture(pinch_gesture)
                    return True
        except Exception as e:
            print(f"Error handling gesture: {e}")
        return False
    
    def handlePinchGesture(self, gesture):
        """Handle pinch gesture for zooming"""
        try:
            if hasattr(gesture, 'state'):
                if gesture.state() == Qt.GestureStarted:
                    self.gestureInProgress = True
                    self.lastGestureValue = gesture.scaleFactor()
                elif gesture.state() == Qt.GestureUpdated and self.gestureInProgress:
                    scale_change = gesture.scaleFactor() / self.lastGestureValue
                    self.lastGestureValue = gesture.scaleFactor()
                    
                    current_scale = self.transform().m11()
                    new_scale = current_scale * scale_change
                    new_scale = max(self.min_zoom, min(self.max_zoom, new_scale))
                    
                    if current_scale != 0:
                        scale_factor = new_scale / current_scale
                        if abs(scale_factor - 1.0) > 1e-9:
                            self.scale(scale_factor, scale_factor)
                elif gesture.state() in [Qt.GestureFinished, Qt.GestureCanceled]:
                    self.gestureInProgress = False
        except Exception as e:
            print(f"Error in pinch gesture: {e}")
            self.gestureInProgress = False

    def updateContentFittingZoom(self, sceneRect):
        if sceneRect.isEmpty():
            return

        padded_rect = sceneRect.adjusted(-30, -30, 30, 30)
        
        view_width = self.viewport().width()
        view_height = self.viewport().height()
        
        if view_width <= 0 or view_height <= 0:
            return
            
        scale_x = view_width / padded_rect.width()
        scale_y = view_height / padded_rect.height()
        
        fitting_scale = min(scale_x, scale_y)
        
        self.contentFittingZoom = max(0.01, fitting_scale * 0.9)

def create_sample_scene():
    """Create a sample scene with editable items"""
    scene = CheckerboardGraphicsScene()
    
    rect_item = QGraphicsRectItem(0, 0, 100, 60)
    rect_item.setBrush(QBrush(QColor(255, 100, 100)))
    rect_item.setPos(50, 50)
    scene.addItem(rect_item)
    
    ellipse_item = QGraphicsEllipseItem(0, 0, 80, 80)
    ellipse_item.setBrush(QBrush(QColor(100, 255, 100)))
    ellipse_item.setPos(200, 100)
    scene.addItem(ellipse_item)
    
    scene.makeItemEditable(rect_item)
    scene.makeItemEditable(ellipse_item)
    
    return scene