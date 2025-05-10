from PySide6.QtCore import Qt, QPointF, QRectF, Signal, QObject, QTimer, QEvent
from PySide6.QtGui import QColor, QPen, QBrush, QTransform, QCursor, QPainterPath, QPainter
from PySide6.QtWidgets import QGraphicsView, QGraphicsScene, QGraphicsRectItem, QGraphicsEllipseItem, QGraphicsItem, QGraphicsPathItem, QApplication, QStyleOptionGraphicsItem, QWidget
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


class EditableGraphicsItem(QObject):
    """A wrapper class that adds editing capabilities to QGraphicsItems"""
    itemChanged = Signal(QGraphicsItem)
    transformChanged = Signal(QTransform)
    
    def __init__(self, item, parent=None):
        super(EditableGraphicsItem, self).__init__(parent)
        self.item = item
        self.handles = {}
        self.boundingRect = None
        self.rotationHandle = None
        self.boundingBoxItem = None
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
        
        item.setFlag(QGraphicsItem.ItemIsSelectable, True)
        item.setFlag(QGraphicsItem.ItemIsMovable, True)
        
        item.setCursor(Qt.OpenHandCursor)
        
        item.setAcceptHoverEvents(True)
        
        # we don't want to install scene event filter on the item itself
        # as that can cause issues with event propagation
        # item.installSceneEventFilter(item)
    
    def setupBoundingBox(self):
        """Create bounding box and handles for the item"""
        if not self.item or not self.item.scene():
            return
            
        self.removeBoundingBox()
        
        scene = self.item.scene()
        
        itemRect = self.item.boundingRect()
        sceneRect = self.item.mapToScene(itemRect).boundingRect()
        
        self.boundingBoxItem = QGraphicsRectItem(sceneRect)
        self.boundingBoxItem.setPen(QPen(QColor(0, 120, 215), 1, Qt.DashLine))
        self.boundingBoxItem.setBrush(QBrush(Qt.transparent))
        self.boundingBoxItem.setZValue(self.item.zValue() + 100)
        self.boundingBoxItem.setData(0, "BoundingBox")
        self.boundingBoxItem.setData(1, id(self.item))
        scene.addItem(self.boundingBoxItem)
        
        center = sceneRect.center()
        
        handle_positions = [
            (HandleType.TopLeft, sceneRect.topLeft()),
            (HandleType.Top, QPointF(center.x(), sceneRect.top())),
            (HandleType.TopRight, sceneRect.topRight()),
            (HandleType.Right, QPointF(sceneRect.right(), center.y())),
            (HandleType.BottomRight, sceneRect.bottomRight()),
            (HandleType.Bottom, QPointF(center.x(), sceneRect.bottom())),
            (HandleType.BottomLeft, sceneRect.bottomLeft()),
            (HandleType.Left, QPointF(sceneRect.left(), center.y()))
        ]
        
        for handle_type, pos in handle_positions:
            handle = QGraphicsEllipseItem(pos.x() - self.handleSize/2, pos.y() - self.handleSize/2, 
                                          self.handleSize, self.handleSize)
            handle.setPen(QPen(QColor(0, 120, 215)))
            handle.setBrush(QBrush(QColor(255, 255, 255)))
            handle.setFlag(QGraphicsItem.ItemIsMovable, False)
            handle.setFlag(QGraphicsItem.ItemIsSelectable, False)
            handle.setZValue(self.item.zValue() + 110)
            handle.setData(0, "Handle")
            handle.setData(1, handle_type)
            handle.setData(2, id(self.item))
            
            if handle_type in (HandleType.TopLeft, HandleType.BottomRight):
                handle.setCursor(Qt.SizeFDiagCursor)
            elif handle_type in (HandleType.TopRight, HandleType.BottomLeft):
                handle.setCursor(Qt.SizeBDiagCursor)
            elif handle_type in (HandleType.Left, HandleType.Right):
                handle.setCursor(Qt.SizeHorCursor)
            elif handle_type in (HandleType.Top, HandleType.Bottom):
                handle.setCursor(Qt.SizeVerCursor)
            
            scene.addItem(handle)
            self.handles[handle_type] = handle
        
        rotatePoint = QPointF(center.x(), sceneRect.top() - self.rotateHandleOffset)
        self.rotationHandle = QGraphicsEllipseItem(
            rotatePoint.x() - self.rotateHandleSize/2, 
            rotatePoint.y() - self.rotateHandleSize/2,
            self.rotateHandleSize, self.rotateHandleSize
        )
        self.rotationHandle.setPen(QPen(QColor(0, 120, 215)))
        self.rotationHandle.setBrush(QBrush(QColor(255, 255, 255)))
        self.rotationHandle.setFlag(QGraphicsItem.ItemIsMovable, False)
        self.rotationHandle.setFlag(QGraphicsItem.ItemIsSelectable, False)
        self.rotationHandle.setZValue(self.item.zValue() + 110)
        self.rotationHandle.setCursor(Qt.CrossCursor)
        self.rotationHandle.setData(0, "RotationHandle")
        self.rotationHandle.setData(1, HandleType.Rotation)
        self.rotationHandle.setData(2, id(self.item))
        
        self.rotationLine = QGraphicsPathItem()
        path = QPainterPath()
        path.moveTo(center.x(), sceneRect.top())
        path.lineTo(rotatePoint)
        self.rotationLine.setPath(path)
        self.rotationLine.setPen(QPen(QColor(0, 120, 215), 1, Qt.DashLine))
        self.rotationLine.setZValue(self.item.zValue() + 105)
        
        scene.addItem(self.rotationLine)
        scene.addItem(self.rotationHandle)
        
        self.isEditing = True
        self.boundingRect = sceneRect
    
    def removeBoundingBox(self):
        """Remove bounding box and handles"""
        if self.boundingBoxItem:
            scene = self.boundingBoxItem.scene()
            if scene:
                scene.removeItem(self.boundingBoxItem)
            self.boundingBoxItem = None
        
        for handle in self.handles.values():
            if handle.scene():
                handle.scene().removeItem(handle)
        self.handles.clear()
        
        if self.rotationHandle and self.rotationHandle.scene():
            self.rotationHandle.scene().removeItem(self.rotationHandle)
        self.rotationHandle = None
        
        if hasattr(self, 'rotationLine') and self.rotationLine and self.rotationLine.scene():
            self.rotationLine.scene().removeItem(self.rotationLine)
        self.rotationLine = None
        
        self.isEditing = False
    
    def updateBoundingBox(self):
        """Update the position of bounding box and handles after item moves"""
        if not self.isEditing or not self.item or not self.item.scene():
            return
            
        itemRect = self.item.boundingRect()
        sceneRect = self.item.mapToScene(itemRect).boundingRect()
        
        if self.boundingBoxItem:
            self.boundingBoxItem.setRect(sceneRect)
        
        center = sceneRect.center()
        
        handle_positions = [
            (HandleType.TopLeft, sceneRect.topLeft()),
            (HandleType.Top, QPointF(center.x(), sceneRect.top())),
            (HandleType.TopRight, sceneRect.topRight()),
            (HandleType.Right, QPointF(sceneRect.right(), center.y())),
            (HandleType.BottomRight, sceneRect.bottomRight()),
            (HandleType.Bottom, QPointF(center.x(), sceneRect.bottom())),
            (HandleType.BottomLeft, sceneRect.bottomLeft()),
            (HandleType.Left, QPointF(sceneRect.left(), center.y()))
        ]
        
        for handle_type, pos in handle_positions:
            if handle_type in self.handles:
                handle = self.handles[handle_type]
                handle.setRect(pos.x() - self.handleSize/2, pos.y() - self.handleSize/2, 
                               self.handleSize, self.handleSize)
        
        if self.rotationHandle:
            rotatePoint = QPointF(center.x(), sceneRect.top() - self.rotateHandleOffset)
            self.rotationHandle.setRect(
                rotatePoint.x() - self.rotateHandleSize/2, 
                rotatePoint.y() - self.rotateHandleSize/2,
                self.rotateHandleSize, self.rotateHandleSize
            )
            
            if hasattr(self, 'rotationLine') and self.rotationLine:
                path = QPainterPath()
                path.moveTo(center.x(), sceneRect.top())
                path.lineTo(rotatePoint)
                self.rotationLine.setPath(path)
        
        self.boundingRect = sceneRect
    
    def startEdit(self, handle_type, handle_pos):
        """Start edit operation (resize or rotate)"""
        if not self.item:
            return
            
        self.currentHandle = handle_type
        self.initialClickPos = handle_pos
        self.initialItemPos = self.item.pos()
        self.initialItemTransform = QTransform(self.item.transform())
        self.initialBoundingRect = QRectF(self.boundingRect)
        
        if handle_type == HandleType.Rotation:
            self.initialRotation = self.currentRotation
    
    def handleEditOperation(self, new_pos):
        """Handle move, resize, or rotate operations"""
        if not self.item or self.currentHandle is None:
            return
            
        itemRect = self.item.boundingRect()
        sceneRect = self.item.mapToScene(itemRect).boundingRect()
        center = sceneRect.center()
        
        if self.currentHandle == HandleType.Rotation:
            initial_vec = self.initialClickPos - center
            current_vec = new_pos - center
            
            initial_angle = math.atan2(initial_vec.y(), initial_vec.x())
            current_angle = math.atan2(current_vec.y(), current_vec.x())
            angle_delta = (current_angle - initial_angle) * 180 / math.pi
            
            new_rotation = self.initialRotation + angle_delta
            self.currentRotation = new_rotation
            
            transform = QTransform()
            transform.translate(center.x(), center.y())
            transform.rotate(new_rotation)
            transform.translate(-center.x(), -center.y())
            
            self.item.setTransform(transform)
            
        else: 
            delta = new_pos - self.initialClickPos
            
            new_rect = QRectF(self.initialBoundingRect)
            
            if self.currentHandle == HandleType.TopLeft:
                new_rect.setTopLeft(new_rect.topLeft() + delta)
            elif self.currentHandle == HandleType.Top:
                new_rect.setTop(new_rect.top() + delta.y())
            elif self.currentHandle == HandleType.TopRight:
                new_rect.setTopRight(new_rect.topRight() + delta)
            elif self.currentHandle == HandleType.Right:
                new_rect.setRight(new_rect.right() + delta.x())
            elif self.currentHandle == HandleType.BottomRight:
                new_rect.setBottomRight(new_rect.bottomRight() + delta)
            elif self.currentHandle == HandleType.Bottom:
                new_rect.setBottom(new_rect.bottom() + delta.y())
            elif self.currentHandle == HandleType.BottomLeft:
                new_rect.setBottomLeft(new_rect.bottomLeft() + delta)
            elif self.currentHandle == HandleType.Left:
                new_rect.setLeft(new_rect.left() + delta.x())
            
            scale_x = new_rect.width() / self.initialBoundingRect.width() if self.initialBoundingRect.width() > 0 else 1
            scale_y = new_rect.height() / self.initialBoundingRect.height() if self.initialBoundingRect.height() > 0 else 1
            
            if self.aspectRatioLocked and self.currentHandle not in [HandleType.Left, HandleType.Right, HandleType.Top, HandleType.Bottom]:
                unified_scale = min(scale_x, scale_y)
                scale_x = scale_y = unified_scale
            
            transform = QTransform()
            transform.translate(center.x(), center.y())
            transform.scale(scale_x, scale_y)
            transform.translate(-center.x(), -center.y())
            
            self.item.setTransform(transform * self.initialItemTransform)
        
        self.updateBoundingBox()
        
        self.transformChanged.emit(self.item.transform())
    
    def endEdit(self):
        """End edit operation"""
        self.currentHandle = None
        
        self.itemChanged.emit(self.item)


class CheckerboardGraphicsScene(QGraphicsScene):
    def __init__(self, parent=None):
        super(CheckerboardGraphicsScene, self).__init__(parent)
        self.checkerboardSize = 20
        self.backgroundColor1 = QColor(240, 240, 240)
        self.backgroundColor2 = QColor(220, 220, 220)
        self.editableItems = {}
        self.currentEditableItem = None
        self.editMode = False
        self.currentHandleItem = None
        self.isDraggingLayer = False
        self.dragStartPos = QPointF()
        self.draggedItem = None
        self.dragStartItemPos = QPointF()

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
        for editable in self.editableItems.values():
            editable.item.setFlag(QGraphicsItem.ItemIsMovable, enabled)
        if not enabled:
            self.clearSelection()
            for editable in self.editableItems.values():
                editable.removeBoundingBox()
            
            self.currentEditableItem = None
            self.currentHandleItem = None
            self.draggedItem = None
            self.isDraggingLayer = False
    
    def makeItemEditable(self, item):
        """Make a graphics item editable"""
        if id(item) not in self.editableItems and hasattr(item, "data") and item.data(1) == "Layer":
            editable = EditableGraphicsItem(item)
            self.editableItems[id(item)] = editable
            return editable
        return self.editableItems.get(id(item))
    
    def mousePressEvent(self, event):
        """Handle mouse press events for editing"""
        if not self.editMode:
            super(CheckerboardGraphicsScene, self).mousePressEvent(event)
            return
        
        self.dragStartPos = event.scenePos()
        
        item_under_cursor = self.itemAt(event.scenePos(), QTransform())
        
        if item_under_cursor and hasattr(item_under_cursor, "data") and item_under_cursor.data(0) in ["Handle", "RotationHandle"]:
            self.currentHandleItem = item_under_cursor
            item_id = item_under_cursor.data(2)
            handle_type = item_under_cursor.data(1)
            
            for item in self.items():
                if hasattr(item, "data") and id(item) == item_id and item.data(1) == "Layer":
                    self.currentEditableItem = self.editableItems.get(id(item))
                    if self.currentEditableItem:
                        self.currentEditableItem.startEdit(handle_type, event.scenePos())
                        event.accept()
                        return
        
        clicked_item = None
        for item in self.items(event.scenePos()):
            if hasattr(item, "data") and item.data(1) == "Layer":
                clicked_item = item
                break
        
        if clicked_item:
            if self.currentEditableItem and self.currentEditableItem.item != clicked_item:
                self.currentEditableItem.removeBoundingBox()
            
            editable = self.makeItemEditable(clicked_item)
            
            if editable:
                self.currentEditableItem = editable
                self.currentEditableItem.setupBoundingBox()
                
                self.isDraggingLayer = True
                self.draggedItem = clicked_item
                self.dragStartItemPos = clicked_item.pos()
                
                QApplication.setOverrideCursor(Qt.ClosedHandCursor)
                
                event.accept()
                return
        
        if item_under_cursor is None or not (hasattr(item_under_cursor, "data") and 
                                          (item_under_cursor.data(0) == "BoundingBox" or
                                           item_under_cursor == self.currentEditableItem.item if self.currentEditableItem else False)):
            if self.currentEditableItem:
                self.currentEditableItem.removeBoundingBox()
                self.currentEditableItem = None
                self.isDraggingLayer = False
                self.draggedItem = None
        
        super(CheckerboardGraphicsScene, self).mousePressEvent(event)
    
    def mouseMoveEvent(self, event):
        """Handle mouse move events for editing"""
        if not self.editMode:
            super(CheckerboardGraphicsScene, self).mouseMoveEvent(event)
            return
        
        if self.currentHandleItem and self.currentEditableItem:
            self.currentEditableItem.handleEditOperation(event.scenePos())
            event.accept()
            return
        
        if self.isDraggingLayer and self.draggedItem:
            delta = event.scenePos() - self.dragStartPos
            
            new_pos = self.dragStartItemPos + delta
            self.draggedItem.setPos(new_pos)
            
            if self.currentEditableItem:
                self.currentEditableItem.updateBoundingBox()
            
            event.accept()
            return
        
        super(CheckerboardGraphicsScene, self).mouseMoveEvent(event)
    
    def mouseReleaseEvent(self, event):
        """Handle mouse release events for editing"""
        if not self.editMode:
            super(CheckerboardGraphicsScene, self).mouseReleaseEvent(event)
            return
        
        if QApplication.overrideCursor():
            QApplication.restoreOverrideCursor()
        
        if self.currentHandleItem and self.currentEditableItem:
            self.currentEditableItem.endEdit()
            self.currentHandleItem = None
            event.accept()
        
        if self.isDraggingLayer and self.draggedItem:
            editable = self.editableItems.get(id(self.draggedItem))
            if editable:
                editable.itemChanged.emit(editable.item)
        
        self.isDraggingLayer = False
        self.draggedItem = None
        
        super(CheckerboardGraphicsScene, self).mouseReleaseEvent(event)


class CustomGraphicsView(QGraphicsView):
    def __init__(self, parent=None, min_zoom=0.05, max_zoom=10.0):
        super(CustomGraphicsView, self).__init__(parent)
        self._pan_start_x = 0
        self._pan_start_y = 0
        self._last_mouse_pos = QPointF()
        self.setMouseTracking(True)
        self._panning = False
        self.minZoom = min_zoom
        self.maxZoom = max_zoom
        self.contentFittingZoom = min_zoom
        self.editMode = False
        
        self.viewport().setAttribute(Qt.WA_AcceptTouchEvents, True)
        self.setViewportUpdateMode(QGraphicsView.FullViewportUpdate)
        
        self.isMacOS = platform.system() == "Darwin"
        self.gestureInProgress = False
        self.lastGestureValue = 0
        
        try:
            if hasattr(Qt, 'PinchGesture'):
                self.grabGesture(Qt.PinchGesture)
            if hasattr(Qt, 'PanGesture'):
                self.grabGesture(Qt.PanGesture)
            if hasattr(Qt, 'SwipeGesture'):
                self.grabGesture(Qt.SwipeGesture)
        except Exception as e:
            print(f"Could not enable gestures: {e}")
        
        self.setRenderHints(QPainter.Antialiasing | QPainter.SmoothPixmapTransform)
        self.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)
        self.setDragMode(QGraphicsView.NoDrag)
    
    def setEditMode(self, enabled):
        """Enable or disable edit mode"""
        self.editMode = enabled
        scene = self.scene()
        if scene and isinstance(scene, CheckerboardGraphicsScene):
            scene.setEditMode(enabled)
    
    def wheelEvent(self, event):
        if not self.scene() or not self.scene().items():
            event.accept()
            return
            
        if hasattr(event, 'source') and event.source() == Qt.MouseEventSynthesizedBySystem:
            if event.modifiers() == Qt.ControlModifier:
                self.handleZoom(event.angleDelta().y())
            else:
                self.horizontalScrollBar().setValue(self.horizontalScrollBar().value() - event.angleDelta().x())
                self.verticalScrollBar().setValue(self.verticalScrollBar().value() - event.angleDelta().y())
        else:
            if event.modifiers() == Qt.ControlModifier:
                self.handleZoom(event.angleDelta().y())
            else:
                self.horizontalScrollBar().setValue(self.horizontalScrollBar().value() - event.angleDelta().x())
                self.verticalScrollBar().setValue(self.verticalScrollBar().value() - event.angleDelta().y())
            
        event.accept()
    
    def handleZoom(self, delta):
        """Handle zoom operation for both mouse wheel and gestures"""
        current_scale = self.transform().m11()
        zoom_factor = 1.1 if delta > 0 else 0.9
        new_scale = current_scale * zoom_factor
        new_scale = max(self.minZoom, min(self.maxZoom, new_scale))
        
        if current_scale != 0:
            scale_factor = new_scale / current_scale
        elif new_scale != 0:
            scale_factor = float('inf')

        if abs(scale_factor - 1.0) > 1e-9:
            self.scale(scale_factor, scale_factor)
    
    def mousePressEvent(self, event):
        if self.editMode:
            super(CustomGraphicsView, self).mousePressEvent(event)
            return
            
        if event.button() == Qt.MiddleButton or (event.button() == Qt.LeftButton and event.modifiers() == Qt.AltModifier):
            self._panning = True
            self._last_mouse_pos = event.position()
            self.setCursor(Qt.ClosedHandCursor)
            event.accept()
        else:
            super(CustomGraphicsView, self).mousePressEvent(event)
    
    def mouseMoveEvent(self, event):
        if self.editMode:
            super(CustomGraphicsView, self).mouseMoveEvent(event)
            return
            
        if self._panning:
            delta = event.position() - self._last_mouse_pos
            self.horizontalScrollBar().setValue(self.horizontalScrollBar().value() - delta.x())
            self.verticalScrollBar().setValue(self.verticalScrollBar().value() - delta.y())
            self._last_mouse_pos = event.position()
            event.accept()
        else:
            super(CustomGraphicsView, self).mouseMoveEvent(event)
    
    def mouseReleaseEvent(self, event):
        if self.editMode:
            super(CustomGraphicsView, self).mouseReleaseEvent(event)
            return
            
        if self._panning and (event.button() == Qt.MiddleButton or 
                              (event.button() == Qt.LeftButton and event.modifiers() == Qt.AltModifier)):
            self._panning = False
            self.setCursor(Qt.ArrowCursor)
            event.accept()
        else:
            super(CustomGraphicsView, self).mouseReleaseEvent(event)
    
    def event(self, event):
        """Handle all events including touch gestures"""
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
                    new_scale = max(self.minZoom, min(self.maxZoom, new_scale))
                    
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