# -*- coding: utf-8 -*-

from math import sin, cos, radians, atan2
from string import ascii_uppercase, ascii_lowercase

from OpenGL.GL import glClear, GL_COLOR_BUFFER_BIT, glEnable, GL_DEPTH_TEST, glMatrixMode, GL_PROJECTION, GL_TRUE, \
    glLoadIdentity, glOrtho, glClearColor, GL_DEPTH_BUFFER_BIT, GL_MODELVIEW, glLineWidth, glBegin, glColor, glVertex, \
    glEnd, glPointSize, GL_POINT_SMOOTH, GL_POINTS, GL_BLEND, glBlendFunc, GL_SRC_ALPHA, GL_QUADS, glDisable, \
    GL_LINES, GL_LINE_LOOP, glDepthMask, GL_FALSE, GL_ONE_MINUS_SRC_ALPHA, GL_TRIANGLE_FAN
from OpenGL.GLU import gluLookAt
from PyQt5.QtCore import Qt, QRect, QSize
from PyQt5.QtGui import QPainter, QPen, QCursor, QTransform, QFont, QColor
from PyQt5.QtWidgets import QOpenGLWidget, QWidget, QCheckBox, QPushButton, QHBoxLayout, QMainWindow, QLabel, QMenu, \
    QApplication, QVBoxLayout, QSpinBox, QPlainTextEdit, QComboBox, QMessageBox, QGraphicsScene, QGraphicsView, \
    QListWidgetItem, QListWidget, QAction, QColorDialog, QDockWidget, QFrame
from sympy import Line, intersection, Point3D, Plane, Line3D, Segment3D


class EntidadGeometrica(QWidget):
    def __init__(self, internal_id: int, nombre: QLabel):
        QWidget.__init__(self)
        self.id = internal_id
        self.customContextMenuRequested.connect(self.context_menu)
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.menu = QMenu()
        self.borrar = QAction("Borrar")
        self.render = QAction("Ver")
        self.render.setCheckable(True)
        self.render.setChecked(True)
        self.menu.addAction(self.borrar)
        self.menu.addAction(self.render)

        hbox = QHBoxLayout()
        hbox.addWidget(nombre)
        self.setLayout(hbox)

        self.editar_color = QAction("Color")
        self.menu.addAction(self.editar_color)
        self.editar_color.triggered.connect(self.cambiar_color)

        self.color = (0, 0, 0, 1)

        # Vértices del cubo
        self.vertices = (Point3D(500, 500, 500), Point3D(-500, 500, 500), Point3D(-500, -500, 500),
                         Point3D(500, -500, 500), Point3D(500, 500, -500), Point3D(-500, 500, -500),
                         Point3D(-500, -500, -500), Point3D(500, -500, -500))

        # Aristas del cubo
        self.aristas = (Segment3D(self.vertices[0], self.vertices[1]), Segment3D(self.vertices[1], self.vertices[2]),
                        Segment3D(self.vertices[2], self.vertices[3]), Segment3D(self.vertices[3], self.vertices[0]),
                        Segment3D(self.vertices[0], self.vertices[4]), Segment3D(self.vertices[1], self.vertices[5]),
                        Segment3D(self.vertices[2], self.vertices[6]), Segment3D(self.vertices[3], self.vertices[7]),
                        Segment3D(self.vertices[4], self.vertices[5]), Segment3D(self.vertices[5], self.vertices[6]),
                        Segment3D(self.vertices[6], self.vertices[7]), Segment3D(self.vertices[7], self.vertices[4]))

        # Caras del cubo
        self.planos = (Plane(self.vertices[0], self.vertices[1], self.vertices[2]),
                       Plane(self.vertices[0], self.vertices[1], self.vertices[5]),
                       Plane(self.vertices[0], self.vertices[4], self.vertices[7]),
                       Plane(self.vertices[4], self.vertices[5], self.vertices[7]),
                       Plane(self.vertices[2], self.vertices[3], self.vertices[7]),
                       Plane(self.vertices[1], self.vertices[2], self.vertices[5]))

        self.plano_v = Plane(Point3D(0, 0, 1), Point3D(0, 0, 0), Point3D(1, 0, 0))
        self.plano_h = Plane(Point3D(0, 1, 0), Point3D(0, 0, 0), Point3D(1, 0, 0))

        self.plano_v_bordes = (Segment3D(Point3D(500, 0, 500), Point3D(-500, 0, 500)),
                               Segment3D(Point3D(-500, 0, 500), Point3D(-500, 0, -500)),
                               Segment3D(Point3D(-500, 0, -500), Point3D(500, 0, -500)),
                               Segment3D(Point3D(500, 0, -500), Point3D(500, 0, 500)))

        self.plano_h_bordes = (Segment3D(Point3D(500, 500, 0), Point3D(-500, 500, 0)),
                               Segment3D(Point3D(-500, 500, 0), Point3D(-500, -500, 0)),
                               Segment3D(Point3D(-500, -500, 0), Point3D(500, -500, 0)),
                               Segment3D(Point3D(500, -500, 0), Point3D(500, 500, 0)))

    def cambiar_color(self):
        color_dialog = QColorDialog()
        color = color_dialog.getColor(options=QColorDialog.ShowAlphaChannel)
        if color.isValid():
            self.color = color.getRgb()

    def context_menu(self):
        self.menu.exec_(QCursor.pos())


class Punto(EntidadGeometrica):
    def __init__(self, internal_id: int, nombre: str, do: int, alejamiento: int, cota: int):
        EntidadGeometrica.__init__(self, internal_id, QLabel(f"{nombre}({do}, {alejamiento}, {cota})"))

        self.borrar.triggered.connect(lambda: main_app.borrar_punto(self.id))
        self.x = do
        self.y = cota
        self.z = alejamiento
        self.nombre = nombre
        self.coords = (self.x, self.z, self.y)


class Recta(EntidadGeometrica):
    def __init__(self, internal_id: int, nombre: str, p1: Punto, p2: Punto):
        nombre = QLabel(f"{nombre}({p1.nombre}, {p2.nombre})")
        EntidadGeometrica.__init__(self, internal_id, nombre)

        self.recta = Line(Point3D(p1.coords), Point3D(p2.coords))
        self.p1 = (p1.coords[0], p1.coords[2], p1.coords[1])
        self.p2 = (p2.coords[0], p2.coords[2], p2.coords[1])

        self.nombre = nombre
        self.contenida_pv = False
        self.contenida_ph = False

        self.borrar.triggered.connect(lambda: main_app.borrar_recta(self.id))

        self.ver_traza_horizontal = QAction("Traza en PH")
        self.ver_traza_vertical = QAction("Traza en PV")
        self.ver_traza_horizontal.setCheckable(True)
        self.ver_traza_vertical.setCheckable(True)
        self.ver_traza_horizontal.setChecked(True)
        self.ver_traza_vertical.setChecked(True)
        self.menu.addAction(self.ver_traza_horizontal)
        self.menu.addAction(self.ver_traza_vertical)

        self.infinita = QAction("Infinita")
        self.infinita.setCheckable(True)
        self.infinita.setChecked(True)
        self.menu.addAction(self.infinita)

        self.extremos = self.extremos()
        self.extremos_I = [i for i in self.extremos if i[1] >= 0 and i[2] >= 0]

        self.traza_v = self.calcular_traza_v()
        if self.traza_v:
            self.traza_v = (self.traza_v[0], self.traza_v[2], self.traza_v[1])
            if self.traza_v[0] > 500 or self.traza_v[1] > 500:
                self.ver_traza_vertical.setCheckable(False)
                self.ver_traza_vertical.setDisabled(True)
        else:
            self.ver_traza_vertical.setCheckable(False)
            self.ver_traza_vertical.setDisabled(True)

        self.traza_h = self.calcular_traza_h()
        if self.traza_h:
            self.traza_h = (self.traza_h[0], self.traza_h[2], self.traza_h[1])
            if self.traza_h[0] > 500 or self.traza_h[2] > 500:
                self.ver_traza_horizontal.setCheckable(False)
                self.ver_traza_horizontal.setDisabled(True)
        else:
            self.ver_traza_horizontal.setCheckable(False)
            self.ver_traza_horizontal.setDisabled(True)

    def extremos(self):
        intersecciones = []
        for i in range(6):
            interseccion = intersection(self.recta, self.planos[i])
            if interseccion:
                intersecciones.append(interseccion[0])
            else:
                intersecciones.append((501, 501, 501))  # Valores inventados para que no sirva la interseccion
        buenos = []
        if -500 < intersecciones[1][0] < 500 and -500 < intersecciones[1][2] < 500:
            buenos.append(intersecciones[1])
        if -500 < intersecciones[4][0] < 500 and -500 < intersecciones[4][2] < 500:
            buenos.append(intersecciones[4])
        if -500 <= intersecciones[0][0] <= 500 and -500 <= intersecciones[0][1] <= 500:
            buenos.append(intersecciones[0])
        if -500 < intersecciones[2][1] < 500 and -500 < intersecciones[2][2] < 500:
            buenos.append(intersecciones[2])
        if -500 <= intersecciones[3][0] <= 500 and -500 <= intersecciones[3][1] <= 500:
            buenos.append(intersecciones[3])
        if -500 < intersecciones[5][1] < 500 and -500 < intersecciones[5][2] < 500:
            buenos.append(intersecciones[5])
        if 500 == abs(intersecciones[2][1]):
            buenos.append(intersecciones[2])
        if 500 == abs(intersecciones[5][1]):
            buenos.append(intersecciones[5])
        buenos = [tuple([p.x, p.z, p.y]) for p in buenos]
        return buenos

    def calcular_traza_h(self):
        traza_h = intersection(self.recta, self.plano_h)
        if traza_h:
            if not isinstance(traza_h[0], Line3D) and traza_h[0]:
                traza_h = tuple(traza_h[0])
                return traza_h
            else:
                self.contenida_ph = True
        return False

    def calcular_traza_v(self):
        traza_v = intersection(self.recta, self.plano_v)
        if traza_v:
            if not isinstance(traza_v[0], Line3D) and traza_v[0]:
                traza_v = tuple(traza_v[0])
                return traza_v
            else:
                self.contenida_pv = True
        return False


class Plano(EntidadGeometrica):
    def __init__(self, internal_id: int, nombre: str, p1: Punto, p2: Punto, p3: Punto):
        EntidadGeometrica.__init__(self, internal_id, QLabel(f"{nombre}({p1.nombre}, {p2.nombre}, {p3.nombre})"))

        self.plano = Plane(Point3D(p1.coords), Point3D(p2.coords), Point3D(p3.coords))
        self.vector_normal = self.plano.normal_vector
        self.nombre = QLabel(f"{nombre}({p1.nombre}, {p2.nombre}, {p3.nombre})")
        self.p1 = (p1.coords[0], p1.coords[2], p1.coords[1])
        self.p2 = (p2.coords[0], p2.coords[2], p2.coords[1])
        self.p3 = (p3.coords[0], p3.coords[2], p3.coords[1])

        self.borrar.triggered.connect(lambda: main_app.borrar_plano(self.id))

        self.color = (0.6, 0.6, 0.15, 0.6)
        self.editar_color = QAction("Color")
        self.menu.addAction(self.editar_color)
        self.editar_color.triggered.connect(self.cambiar_color)

        self.puntos = self.limites(self.p1, self.p2, self.p3)

        self.ver_traza_horizontal = QAction("Traza en PH")
        self.ver_traza_vertical = QAction("Traza en PV")
        self.ver_traza_horizontal.setCheckable(True)
        self.ver_traza_vertical.setCheckable(True)
        self.ver_traza_horizontal.setChecked(True)
        self.ver_traza_vertical.setChecked(True)
        self.menu.addAction(self.ver_traza_horizontal)
        self.menu.addAction(self.ver_traza_vertical)

        self.traza_v = self.calcular_traza_v()
        self.traza_h = self.calcular_traza_h()

        if not self.traza_v:
            self.ver_traza_vertical.setChecked(False)
            self.ver_traza_vertical.setCheckable(False)

        if not self.traza_h:
            self.ver_traza_horizontal.setChecked(False)
            self.ver_traza_horizontal.setCheckable(False)

    def limites(self, p1: tuple, p2: tuple, p3: tuple):
        plano = Plane(Point3D(p1), Point3D(p2), Point3D(p3))
        buenos = []

        for i in range(12):
            inter = intersection(plano, self.aristas[i])
            if inter:
                if not isinstance(inter[0], Segment3D):
                    buenos.append((int(inter[0][0]), int(inter[0][1]), int(inter[0][2])))

        for i in range(8):
            inter = intersection(plano, self.vertices[i])
            if inter:
                buenos.append((int(inter[0][0]), int(inter[0][1]), int(inter[0][2])))

        buenos = list(set(buenos))
        if len(buenos) == 3:
            return buenos

        elif 4 <= len(buenos) <= 6:
            vector = plano.normal_vector
            proyectados = []
            # Perfil
            if vector[1] == vector[2] == 0:
                for i in buenos:
                    proyectados.append((i[1], i[2]))
            # Vertical
            elif vector[0] == vector[1] == 0:
                proyectante = self.planos[0]
                for i in buenos:
                    proyectau = proyectante.projection(i)
                    proyectados.append((proyectau[0], proyectau[1]))

            # Horizontal
            else:
                proyectante = self.planos[1]
                for i in buenos:
                    proyectau = proyectante.projection(i)
                    proyectados.append((proyectau[0], proyectau[2]))

            angulos = []
            for i in proyectados:
                angulos.append(atan2(i[0], i[1]))

            juntados = sorted(zip(angulos, buenos))
            ordenados = [i[1] for i in juntados]

            return ordenados

    def calcular_traza_h(self):
        if self.vector_normal[0] == 0 and self.vector_normal[1] == 0:
            return False
        else:
            trazas = []
            for i in range(4):
                if not len(trazas) == 2:
                    interseccion = intersection(self.plano, self.plano_h_bordes[i])
                    if interseccion and not isinstance(interseccion[0], Segment3D):
                        trazas.append((interseccion[0][0], interseccion[0][2], interseccion[0][1]))
            trazas = list(set(trazas))
            if len(trazas) == 1:
                return False
            else:
                return trazas

    def calcular_traza_v(self):
        if self.vector_normal[0] == 0 and self.vector_normal[2] == 0:
            return False
        else:
            trazas = []
            for i in range(4):
                if not len(trazas) == 2:
                    interseccion = intersection(self.plano, self.plano_v_bordes[i])
                    if interseccion and not isinstance(interseccion[0], Segment3D):
                        trazas.append((interseccion[0][0], interseccion[0][2], interseccion[0][1]))
            trazas = list(set(trazas))
            if len(trazas) == 1:
                return False
            else:
                return trazas


class Renderizador(QOpenGLWidget):
    def __init__(self):
        QOpenGLWidget.__init__(self)
        self.desviacion_x = 0
        self.desviacion_y = 0
        self.desviacion_z = 0
        self.theta = 405
        self.phi = 45
        self.zoom_1 = 150
        self.zoom_2 = -150
        self.x = sin(radians(self.theta)) * cos(radians(self.phi)) + self.desviacion_x
        self.z = sin(radians(self.theta)) * sin(radians(self.phi)) + self.desviacion_z
        self.y = cos(radians(self.theta)) + self.desviacion_y
        self.vertices_vertical_arriba = ((500, 500, 0), (-500, 500, 0), (-500, 0, 0), (500, 0, 0))
        self.vertices_vertical_debajo = ((500, 0, 0), (-500, 0, 0), (-500, -500, 0), (500, -500, 0))
        self.vertices_horizontal_delante = ((500, 0, 0), (500, 0, 500), (-500, 0, 500), (-500, 0, 0))
        self.vertices_horizontal_detras = ((500, 0, 0), (500, 0, -500), (-500, 0, -500), (-500, 0, 0))
        self.vertices_borde_vertical = ((500, 500, 0), (500, -500, 0), (-500, -500, 0), (-500, 500, 0))
        self.vertices_borde_horizontal = ((500, 0, 500), (-500, 0, 500), (-500, 0, -500), (500, 0, -500))

    def sizeHint(self):
        return QSize(600, 600)

    def resizeEvent(self, event):
        if self.width() > self.height():
            self.resize(self.height(), self.height())
        elif self.height() > self.width():
            self.resize(self.width(), self.width())
        QOpenGLWidget.resizeEvent(self, event)

    def recalcular_posicion(self):
        self.x = sin(radians(self.theta)) * cos(radians(self.phi)) + self.desviacion_x
        self.z = sin(radians(self.theta)) * sin(radians(self.phi)) + self.desviacion_z
        self.y = cos(radians(self.theta)) + self.desviacion_y
        gluLookAt(self.x, self.y, self.z, self.desviacion_x, self.desviacion_y, self.desviacion_z, 0, 1, 0)
        main_app.actualizar()
        self.update()

    def ver_alzado(self):
        self.phi = 90
        self.theta = 450
        self.recalcular_posicion()

    def ver_planta(self):
        self.phi = 90
        self.theta = 360
        self.recalcular_posicion()

    def ver_perfil(self):
        self.phi = 0
        self.theta = 450
        self.recalcular_posicion()

    def ver_reset(self):
        self.theta = 405
        self.phi = 45
        self.zoom_1 = 150
        self.zoom_2 = -150
        self.desviacion_x = 0
        self.desviacion_y = 0
        self.desviacion_z = 0
        self.recalcular_posicion()

    def plano_vertical_arriba(self):
        glColor(0.1, 1, 0.1, 0.5)
        for vertex in range(4):
            glVertex(self.vertices_vertical_arriba[vertex])

    def plano_vertical_debajo(self):
        glColor(0.1, 1, 0.1, 0.5)
        for vertex in range(4):
            glVertex(self.vertices_vertical_debajo[vertex])

    def plano_horizontal_delante(self):
        glColor(1, 0.1, 0.1, 0.5)
        for vertex in range(4):
            glVertex(self.vertices_horizontal_delante[vertex])

    def plano_horizontal_detras(self):
        glColor(1, 0.1, 0.1, 0.5)
        for vertex in range(4):
            glVertex(self.vertices_horizontal_detras[vertex])

    def bordes_vertical(self):
        if main_app.ajustes.ver_plano_vertical.isChecked():
            glLineWidth(1)
            glColor(0.1, 1, 0.1, 0.5)
            glBegin(GL_LINE_LOOP)
            for vertex in range(4):
                glVertex(self.vertices_borde_vertical[vertex])
            glEnd()

    def bordes_horizontal(self):
        if main_app.ajustes.ver_plano_horizontal.isChecked():
            glLineWidth(1)
            glColor(1, 0.1, 0.1, 0.5)
            glBegin(GL_LINE_LOOP)
            for vertex in range(4):
                glVertex(self.vertices_borde_horizontal[vertex])
            glEnd()

    def planos_proyectantes(self):
        vertical = main_app.ajustes.ver_plano_vertical.isChecked()
        horizontal = main_app.ajustes.ver_plano_horizontal.isChecked()
        if vertical or horizontal:
            glEnable(GL_BLEND)
            glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
            glDepthMask(GL_FALSE)
            glBegin(GL_QUADS)
            # TODO
            if self.y == self.z == 0:
                self.bordes_horizontal()
                self.bordes_vertical()
            elif y == 0:
                pass
            elif z == 0:
                pass
            else:
                pass

            glEnd()
            glDepthMask(GL_TRUE)
            glDisable(GL_BLEND)

    @staticmethod
    def dibujar_ejes():
        glLineWidth(3)
        glBegin(GL_LINES)
        # X ROJO
        glColor(1, 0, 0)
        glVertex(0, 0, 0)
        glVertex(10, 0, 0)
        # Y VERDE
        glColor(0, 1, 0)
        glVertex(0, 0, 0)
        glVertex(0, 10, 0)
        # Z AZUL
        glColor(0, 0, 1)
        glVertex(0, 0, 0)
        glVertex(0, 0, 10)
        glEnd()

    @staticmethod
    def dibujar_puntos():
        for i in range(main_app.lista_puntos.count()):
            punto = main_app.lista_puntos.itemWidget(main_app.lista_puntos.item(i))
            if punto.render.isChecked():
                glColor(punto.color)
                glPointSize(4)
                glEnable(GL_POINT_SMOOTH)
                glBegin(GL_POINTS)
                glVertex(punto.x, punto.y, punto.z)
                glEnd()

    @staticmethod
    def dibujar_rectas():
        for i in range(main_app.lista_rectas.count()):
            recta = main_app.lista_rectas.itemWidget(main_app.lista_rectas.item(i))
            if recta.render.isChecked():
                glColor(recta.color)
                glLineWidth(2)
                glBegin(GL_LINES)
                if recta.infinita.isChecked():
                    glVertex(recta.extremos[0])
                    glVertex(recta.extremos[1])
                else:
                    glVertex(recta.p1)
                    glVertex(recta.p2)
                glEnd()
                if main_app.ajustes.ver_rectas_trazas_horizontales.isChecked():
                    if recta.traza_h and recta.ver_traza_horizontal.isChecked():
                        if recta.traza_h[0] < 500 and recta.traza_h[2] < 500:
                            glColor(1, 0, 0, 0)
                            glBegin(GL_POINTS)
                            glVertex(recta.traza_h)
                            glEnd()
                if main_app.ajustes.ver_rectas_trazas_verticales.isChecked():
                    if recta.traza_v and recta.ver_traza_vertical.isChecked():
                        if recta.traza_v[0] < 500 and recta.traza_v[1] < 500:
                            glColor(0, 1, 0, 0)
                            glBegin(GL_POINTS)
                            glVertex(recta.traza_v)
                            glEnd()

    @staticmethod
    def dibujar_planos():
        for i in range(main_app.lista_planos.count()):
            plano = main_app.lista_planos.itemWidget(main_app.lista_planos.item(i))
            if plano.render.isChecked():
                glEnable(GL_BLEND)
                glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
                glDepthMask(GL_FALSE)

                if plano.render.isChecked():
                    glBegin(GL_TRIANGLE_FAN)
                    glColor(plano.color)
                    for j in plano.puntos:
                        glVertex(j[0], j[1], j[2])
                    glEnd()
                glDepthMask(GL_TRUE)
                glDisable(GL_BLEND)
                glColor(0, 0, 0, 0)
                if plano.ver_traza_vertical.isChecked():
                    glBegin(GL_LINES)
                    glVertex(plano.traza_v[0])
                    glVertex(plano.traza_v[1])
                    glEnd()
                if plano.ver_traza_horizontal.isChecked():
                    glBegin(GL_LINES)
                    glVertex(plano.traza_h[0])
                    glVertex(plano.traza_h[1])
                    glEnd()

    def initializeGL(self):
        glEnable(GL_DEPTH_TEST)

    def paintGL(self):
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        glOrtho(self.zoom_1, self.zoom_2, self.zoom_2, self.zoom_1, -5000, 5000)
        glMatrixMode(GL_MODELVIEW)
        glClearColor(1, 1, 1, 0)
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glLoadIdentity()
        arriba = 1
        if self.theta == 360:
            arriba = -1
        gluLookAt(self.x, self.y, self.z, self.desviacion_x, self.desviacion_y, self.desviacion_z, 0, arriba, 0)
        self.planos_proyectantes()
        if main_app.ajustes.ver_puntos.isChecked():
            self.dibujar_puntos()
        if main_app.ajustes.ver_rectas.isChecked():
            self.dibujar_rectas()
        if main_app.ajustes.ver_planos.isChecked():
            self.dibujar_planos()
        if main_app.ajustes.ver_ejes.isChecked():
            self.dibujar_ejes()
        self.update()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_W:
            self.theta -= 5
        elif event.key() == Qt.Key_A:
            self.phi -= 5
        elif event.key() == Qt.Key_S:
            self.theta += 5
        elif event.key() == Qt.Key_D:
            self.phi += 5
        elif event.key() == Qt.Key_Q:
            self.desviacion_z += 1
        elif event.key() == Qt.Key_E:
            self.desviacion_z -= 1
        elif event.key() == Qt.Key_Left:
            self.desviacion_x += 1
        elif event.key() == Qt.Key_Up:
            self.desviacion_y += 1
        elif event.key() == Qt.Key_Right:
            self.desviacion_x -= 1
        elif event.key() == Qt.Key_Down:
            self.desviacion_y -= 1
        elif event.key() == Qt.Key_1:
            self.ver_alzado()
        elif event.key() == Qt.Key_2:
            self.ver_planta()
        elif event.key() == Qt.Key_3:
            self.ver_perfil()
        elif event.key() == Qt.Key_R:
            self.ver_reset()
        elif event.key() == Qt.Key_Minus:
            self.zoom_1 += 10
            self.zoom_2 -= 10
        elif event.key() == Qt.Key_Plus:
            self.zoom_1 -= 10
            self.zoom_2 += 10
        if self.theta < 360:
            self.theta = 360
        if self.theta > 540:
            self.theta = 540
        if self.phi >= 360:
            self.phi -= 360
        if self.phi < 0:
            self.phi += 360
        if self.zoom_1 < 10:
            self.zoom_1 = 10
        if self.zoom_2 > -10:
            self.zoom_2 = -10
        self.x = sin(radians(self.theta)) * cos(radians(self.phi)) + self.desviacion_x
        self.z = sin(radians(self.theta)) * sin(radians(self.phi)) + self.desviacion_z
        self.y = cos(radians(self.theta)) + self.desviacion_y

        main_app.actualizar()
        self.update()
        QOpenGLWidget.keyPressEvent(self, event)


class Diedrico(QWidget):
    def __init__(self):
        QWidget.__init__(self)

        negro = QColor(0, 0, 0)
        rojo = QColor(255, 103, 69)
        verde = QColor(0, 255, 0)
        azul = QColor(50, 100, 255)
        azul_oscuro = QColor(10, 50, 140)

        self.pen_linea_tierra = QPen(negro)
        self.pen_linea_tierra.setWidth(1)

        self.pen_punto_prima = QPen(QColor(201, 10, 0), 3)
        self.pen_punto_prima2 = QPen(QColor(8, 207, 41), 3)

        self.pen_recta_prima = QPen(rojo, 3, Qt.DotLine)
        self.pen_recta_prima.setDashPattern([1, 3])
        self.pen_recta_prima2 = QPen(verde, 3, Qt.DotLine)
        self.pen_recta_prima2.setDashPattern([1, 3])

        self.pen_recta_prima_continuo = QPen(rojo, 3)
        self.pen_recta_prima2_continuo = QPen(verde, 3)
        self.pen_trazas = QPen(Qt.black, 3)

        self.pen_prima3 = QPen(Qt.black, 3)

        self.pen_plano_prima = QPen(azul, 4)
        self.pen_plano_prima2 = QPen(azul_oscuro, 4)

    def sizeHint(self):
        return QSize(10, 10)

    def paintEvent(self, event):
        qp = QPainter(self)
        qp.setRenderHint(QPainter.Antialiasing)
        self.elementos_estaticos(qp)
        qp.translate(500, 500)
        qp.scale(-1, -1)
        if main_app.ver_rectas.checkState():
            self.dibujar_rectas(qp)
        if main_app.ver_puntos.checkState():
            self.dibujar_puntos(qp)
        if main_app.ver_planos.checkState():
            self.dibujar_planos(qp)
        self.update()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Plus:
            self.zoom_in()
        if event.key() == Qt.Key_Minus:
            self.zoom_out()
        if event.key() == Qt.Key_R:
            main_app.vista.setTransform(QTransform())

    @staticmethod
    def zoom_in():
        scale_tr = QTransform()
        scale_tr.scale(1.2, 1.2)
        tr = main_app.vista.transform() * scale_tr
        main_app.vista.setTransform(tr)

    @staticmethod
    def zoom_out():
        scale_tr = QTransform()
        scale_tr.scale(1.2, 1.2)
        scale_inverted, invertible = scale_tr.inverted()
        if invertible:
            tr = main_app.vista.transform() * scale_inverted
            main_app.vista.setTransform(tr)

    def elementos_estaticos(self, qp):
        qp.setPen(self.pen_linea_tierra)
        qp.drawRect(0, 0, 1000, 1000)  # Marco

        qp.drawLine(5, 500, 995, 500)  # LT

        qp.drawLine(5, 505, 15, 505)  # Raya 1
        qp.drawLine(985, 505, 995, 505)  # Raya 2
        qp.drawLine(500, 5, 500, 995)  # Raya PP

    def dibujar_puntos(self, qp):
        for i in range(main_app.lista_puntos.count()):
            punto = main_app.lista_puntos.itemWidget(main_app.lista_puntos.item(i))
            if punto.render.isChecked():
                self.punto_prima(qp, punto)
                self.punto_prima2(qp, punto)
                if main_app.tercera_proyeccion.checkState():
                    self.punto_prima3(qp, punto)

    def punto_prima(self, qp, punto):
        qp.setPen(self.pen_punto_prima)
        qp.drawPoint(punto.x, -punto.z)

    def punto_prima2(self, qp, punto):
        qp.setPen(self.pen_punto_prima2)
        qp.drawPoint(punto.x, punto.y)

    def punto_prima3(self, qp, punto):
        qp.setPen(self.pen_prima3)
        qp.drawPoint(-punto.z, punto.y)

    def dibujar_rectas(self, qp):
        for i in range(main_app.lista_rectas.count()):
            recta = main_app.lista_rectas.itemWidget(main_app.lista_rectas.item(i))
            if recta.render.isChecked():

                if recta.infinita.isChecked():
                    extremos = recta.extremos
                    # Ninguna traza
                    if not recta.traza_v and not recta.traza_h and len(recta.extremos_I) == 2:
                        # Recta en PH
                        if recta.contenida_ph and not recta.contenida_pv:
                            self.dibujar_continuo(qp, recta.extremos_I[0], recta.extremos_I[1])

                        # Recta en PV
                        elif not recta.contenida_ph and recta.contenida_pv:
                            self.dibujar_continuo(qp, recta.extremos_I[0], recta.extremos_I[1])

                        # Trazas en LT
                        elif recta.extremos[0][1:] == recta.extremos[1][1:] == (0, 0):
                            self.dibujar_continuo(qp, [500, 0, 0], [-500, 0, 0])

                        # 1er cuadrante
                        else:
                            self.dibujar_continuo(qp, recta.extremos_I[0], recta.extremos_I[1])

                    # Una traza en PH
                    elif recta.traza_h and not recta.traza_v:
                        # Trazas en PH
                        if recta.extremos[0][2] == 0 and recta.extremos[1][2] == 0:
                            inicio = recta.traza_h
                            fin = recta.extremos_I[0]
                            self.dibujar_continuo(qp, inicio, fin)
                        else:
                            inicio = recta.traza_h
                            fin = recta.extremos_I[0]
                            self.dibujar_continuo(qp, inicio, fin)

                    # Una traza en PV
                    elif not recta.traza_h and recta.traza_v:
                        # Trazas en PV
                        if recta.extremos[0][1] == 0 and recta.extremos[1][1] == 0:
                            inicio = recta.traza_v
                            fin = recta.extremos_I[0]
                            self.dibujar_continuo(qp, inicio, fin)
                        # elif recta.traza_v[2] > 0:
                        else:
                            inicio = recta.traza_v
                            fin = recta.extremos_I[0]
                            self.dibujar_continuo(qp, inicio, fin)

                    # Dos trazas
                    elif recta.traza_v and recta.traza_h:
                        # Trazas en LT
                        if recta.traza_h == recta.traza_v:
                            inicio = recta.traza_h
                            fin = recta.extremos_I[0]
                            self.dibujar_continuo(qp, inicio, fin)
                        # 010
                        if recta.traza_h[2] > 0 and recta.traza_v[1] > 0:
                            inicio = recta.traza_v
                            fin = recta.traza_h
                            self.dibujar_continuo(qp, inicio, fin)
                        # 001
                        elif recta.traza_h[2] < 0 < recta.traza_v[1]:
                            inicio = recta.traza_v
                            fin = recta.extremos_I[0]
                            self.dibujar_continuo(qp, inicio, fin)
                        # 100
                        elif recta.traza_h[2] > 0 > recta.traza_v[1]:
                            inicio = recta.traza_h
                            fin = recta.extremos_I[0]
                            self.dibujar_continuo(qp, inicio, fin)
                else:
                    extremos = (recta.p1, recta.p2)

                    extremos_i = []
                    if extremos[0][1] >= 0 and extremos[0][2] >= 0:
                        extremos_i.append(extremos[0])
                    if extremos[1][1] >= 0 and extremos[1][2] >= 0:
                        extremos_i.append(extremos[1])

                    if len(extremos_i) == 2:
                        self.dibujar_continuo(qp, extremos[0], extremos[1])

                    else:
                        if recta.traza_v:
                            if recta.traza_v[2] >= 0:
                                self.dibujar_continuo(qp, extremos[0], recta.traza_v)

                        elif recta.traza_h:
                            if recta.traza_h[1] >= 0:
                                self.dibujar_continuo(qp, extremos[0], recta.traza_h)

                # Dibuja en discontínuo
                qp.setPen(self.pen_recta_prima)
                self.recta_prima(qp, extremos)
                qp.setPen(self.pen_recta_prima2)
                self.recta_prima2(qp, extremos)

                # Tercera proyección
                if main_app.tercera_proyeccion.checkState():
                    qp.setPen(self.pen_prima3)
                    self.recta_prima3(qp, extremos)

                self.dibujar_trazas_recta(qp, recta)

    def dibujar_continuo(self, qp, inicio, fin):
        # Intercambio de ejes para arreglar sistema de coordenadas
        qp.setPen(self.pen_recta_prima_continuo)
        self.recta_prima(qp, (inicio, fin))
        qp.setPen(self.pen_recta_prima2_continuo)
        self.recta_prima2(qp, (inicio, fin))

    @staticmethod
    def recta_prima(qp, extremos):
        x0 = int(extremos[0][0])
        x = int(extremos[1][0])
        y0 = int(-extremos[0][2])
        y = int(-extremos[1][2])
        if not (x0 == x and y0 == y):
            qp.drawLine(x0, y0, x, y)

    @staticmethod
    def recta_prima2(qp, extremos):
        x0 = int(extremos[0][0])
        x = int(extremos[1][0])
        y0 = int(extremos[0][1])
        y = int(extremos[1][1])
        if not (x0 == x and y0 == y):
            qp.drawLine(x0, y0, x, y)

    @staticmethod
    def recta_prima3(qp, extremos):
        x0 = int(-extremos[0][2])
        x = int(-extremos[1][2])
        y0 = int(extremos[0][1])
        y = int(extremos[1][1])
        qp.drawLine(x0, y0, x, y)

    def dibujar_trazas_recta(self, qp, recta):
        qp.setPen(self.pen_trazas)
        if recta.infinita.isChecked():
            if recta.traza_h and recta.ver_traza_horizontal.isChecked():
                qp.drawPoint(int(recta.traza_h[0]), int(-recta.traza_h[2]))  # V "
                qp.drawPoint(int(recta.traza_h[0]), 0)  # V '
            if recta.traza_v and recta.ver_traza_vertical.isChecked():
                qp.drawPoint(int(recta.traza_v[0]), int(recta.traza_v[1]))  # H '
                qp.drawPoint(int(recta.traza_v[0]), 0)  # H "

    def dibujar_planos(self, qp):
        for i in range(main_app.lista_planos.count()):
            plano = main_app.lista_planos.itemWidget(main_app.lista_planos.item(i))
            if plano.render.isChecked():
                if plano.traza_h:
                    qp.setPen(self.pen_plano_prima)
                    self.recta_prima(qp, plano.traza_h)
                if plano.traza_v:
                    qp.setPen(self.pen_plano_prima2)
                    self.recta_prima2(qp, plano.traza_v)


class Ajustes(QMainWindow):
    def __init__(self):
        QMainWindow.__init__(self)
        self.setFixedSize(420, 135)
        fuente = QFont()
        fuente.setPointSize(12)
        widget_central = QWidget(self)

        ajustes = QLabel(widget_central)
        ajustes.setGeometry(10, 10, 40, 16)
        ajustes.setText("Ajustes:")

        puntos = QLabel(widget_central)
        puntos.setText("Puntos:")
        puntos.setGeometry(10, 90, 37, 16)
        rectas = QLabel(widget_central)
        rectas.setText("Rectas")
        rectas.setGeometry(140, 10, 41, 16)
        planos = QLabel(widget_central)
        planos.setText("Planos")
        planos.setGeometry(280, 10, 35, 16)

        self.ver_plano_horizontal = QCheckBox(widget_central)
        self.ver_plano_horizontal.setText("Ver plano horizontal")
        self.ver_plano_horizontal.setChecked(True)
        self.ver_plano_horizontal.setGeometry(10, 70, 118, 17)

        self.ver_plano_vertical = QCheckBox(widget_central)
        self.ver_plano_vertical.setText("Ver plano vertical")
        self.ver_plano_vertical.setChecked(True)
        self.ver_plano_vertical.setGeometry(10, 50, 106, 17)

        self.ver_ejes = QCheckBox(widget_central)
        self.ver_ejes.setText("Ver ejes")
        self.ver_ejes.setChecked(True)
        self.ver_ejes.setGeometry(10, 30, 62, 17)

        self.ver_puntos = QCheckBox(widget_central)
        self.ver_puntos.setText("Ver puntos")
        self.ver_puntos.setChecked(True)
        self.ver_puntos.setGeometry(10, 110, 75, 17)

        self.ver_rectas = QCheckBox(widget_central)
        self.ver_rectas.setText("Ver rectas")
        self.ver_rectas.setChecked(True)
        self.ver_rectas.setGeometry(140, 30, 133, 17)

        self.ver_planos = QCheckBox(widget_central)
        self.ver_planos.setText("Ver planos")
        self.ver_planos.setChecked(True)
        self.ver_planos.setGeometry(280, 30, 73, 17)

        self.ver_rectas_trazas_verticales = QCheckBox(widget_central)
        self.ver_rectas_trazas_verticales.setChecked(True)
        self.ver_rectas_trazas_verticales.setText("Ver trazas verticales")
        self.ver_rectas_trazas_verticales.setGeometry(140, 70, 121, 17)

        self.ver_rectas_trazas_horizontales = QCheckBox(widget_central)
        self.ver_rectas_trazas_horizontales.setChecked(True)
        self.ver_rectas_trazas_horizontales.setGeometry(140, 50, 129, 17)
        self.ver_rectas_trazas_horizontales.setText("Ver trazas horizontales")

        self.ver_planos_trazas_verticales = QCheckBox(widget_central)
        self.ver_planos_trazas_verticales.setChecked(True)
        self.ver_planos_trazas_verticales.setGeometry(280, 70, 121, 17)
        self.ver_planos_trazas_verticales.setText("Ver trazas verticales")
        self.ver_planos_trazas_horizontales = QCheckBox(widget_central)
        self.ver_planos_trazas_horizontales.setChecked(True)
        self.ver_planos_trazas_horizontales.setText("Ver trazas horizontales")
        self.ver_planos_trazas_horizontales.setGeometry(280, 50, 129, 17)

        self.setWindowTitle("Ajustes")
        self.setCentralWidget(widget_central)


class Ventana(QMainWindow):
    def __init__(self):
        QMainWindow.__init__(self)
        self.showMaximized()
        widget_central = QWidget()

        self.renderizador = Renderizador()
        self.renderizador.setFocusPolicy(Qt.ClickFocus)
        dock_renderizador = QDockWidget("Renderizador")
        dock_renderizador.setWidget(self.renderizador)
        dock_renderizador.setFeatures(QDockWidget.DockWidgetMovable)
        self.addDockWidget(Qt.LeftDockWidgetArea, dock_renderizador)

        scene = QGraphicsScene()
        self.vista = QGraphicsView(scene)

        self.diedrico = Diedrico()
        self.diedrico.setFocusPolicy(Qt.ClickFocus)
        self.diedrico.setFixedSize(1000, 1000)
        scene.addWidget(self.diedrico)

        dock_diedrico = QDockWidget("Diédrico")
        dock_diedrico.setFeatures(QDockWidget.DockWidgetMovable)
        self.addDockWidget(Qt.RightDockWidgetArea, dock_diedrico)
        dock_diedrico.setWidget(self.vista)

        fuente = QFont("Arial")
        fuente.setPointSize(10)

        frame = QFrame(widget_central)
        frame.setLineWidth(3)

        label = QLabel(frame)
        label.setGeometry(QRect(10, 10, 91, 16))
        label.setFont(fuente)
        label_2 = QLabel(frame)
        label_2.setGeometry(QRect(10, 30, 71, 16))
        label_2.setFont(fuente)
        self.label_3 = QLabel(frame)
        self.label_3.setGeometry(QRect(110, 30, 151, 20))
        self.label_3.setFont(fuente)

        self.label_6 = QLabel(frame)
        self.label_6.setGeometry(QRect(10, 50, 111, 16))
        self.label_6.setFont(fuente)
        self.label_7 = QLabel(frame)
        self.label_7.setGeometry(QRect(130, 50, 130, 16))
        self.label_7.setFont(fuente)
        label_8 = QLabel(frame)
        label_8.setGeometry(QRect(10, 70, 91, 16))
        label_8.setFont(fuente)
        label_9 = QLabel(frame)
        label_9.setGeometry(QRect(10, 120, 91, 16))
        label_9.setFont(fuente)
        label_10 = QLabel(frame)
        label_10.setGeometry(QRect(170, 120, 91, 16))
        label_10.setFont(fuente)
        label_11 = QLabel(frame)
        label_11.setGeometry(QRect(330, 120, 91, 16))
        label_11.setFont(fuente)
        label_12 = QLabel(frame)
        label_12.setGeometry(QRect(10, 140, 91, 16))
        label_13 = QLabel(frame)
        label_13.setGeometry(QRect(10, 160, 91, 16))
        label_14 = QLabel(frame)
        label_14.setGeometry(QRect(10, 180, 91, 16))
        label_15 = QLabel(frame)
        label_15.setGeometry(QRect(10, 200, 91, 16))
        label_16 = QLabel(frame)
        label_16.setGeometry(QRect(170, 140, 51, 16))
        label_17 = QLabel(frame)
        label_17.setGeometry(QRect(170, 160, 51, 16))
        label_18 = QLabel(frame)
        label_18.setGeometry(QRect(170, 180, 91, 21))
        label_19 = QLabel(frame)
        label_19.setGeometry(QRect(330, 140, 51, 16))
        label_20 = QLabel(frame)
        label_20.setGeometry(QRect(330, 160, 51, 16))
        label_21 = QLabel(frame)
        label_21.setGeometry(QRect(330, 200, 91, 21))
        label_22 = QLabel(frame)
        label_22.setGeometry(QRect(330, 180, 51, 16))

        boton_r = QPushButton(frame)
        boton_r.setGeometry(QRect(10, 90, 81, 23))
        boton_r.clicked.connect(self.renderizador.ver_reset)
        boton_alzado = QPushButton(frame)
        boton_alzado.setGeometry(QRect(100, 90, 81, 23))
        boton_alzado.clicked.connect(self.renderizador.ver_alzado)
        boton_planta = QPushButton(frame)
        boton_planta.setGeometry(QRect(190, 90, 81, 23))
        boton_planta.clicked.connect(self.renderizador.ver_planta)
        boton_perfil = QPushButton(frame)
        boton_perfil.setGeometry(QRect(280, 90, 81, 23))
        boton_perfil.clicked.connect(self.renderizador.ver_perfil)
        boton_punto = QPushButton(frame)
        boton_punto.setGeometry(QRect(10, 250, 151, 21))
        boton_punto.clicked.connect(self.crear_punto)
        boton_recta = QPushButton(frame)
        boton_recta.setGeometry(QRect(170, 229, 151, 21))
        boton_recta.clicked.connect(self.crear_recta)
        boton_plano = QPushButton(frame)
        boton_plano.setGeometry(QRect(330, 250, 151, 21))
        boton_plano.clicked.connect(self.crear_plano)

        self.valor_do = QSpinBox(frame)
        self.valor_do.setGeometry(QRect(110, 140, 51, 20))
        self.valor_do.setRange(-500, 500)
        self.valor_a = QSpinBox(frame)
        self.valor_a.setGeometry(QRect(110, 160, 51, 20))
        self.valor_a.setRange(-500, 500)
        self.valor_c = QSpinBox(frame)
        self.valor_c.setGeometry(QRect(110, 180, 51, 20))
        self.valor_c.setRange(-500, 500)
        self.punto_1 = QComboBox(frame)
        self.punto_1.setGeometry(QRect(230, 140, 91, 22))
        self.punto_2 = QComboBox(frame)
        self.punto_2.setGeometry(QRect(230, 160, 91, 21))
        self.punto_plano = QComboBox(frame)
        self.punto_plano.setGeometry(QRect(380, 140, 91, 22))
        self.punto_plano2 = QComboBox(frame)
        self.punto_plano2.setGeometry(QRect(380, 160, 91, 22))
        self.punto_plano3 = QComboBox(frame)
        self.punto_plano3.setGeometry(QRect(380, 180, 91, 22))

        self.punto_nombre = QPlainTextEdit(frame)
        self.punto_nombre.setGeometry(QRect(10, 220, 151, 25))
        self.recta_nombre = QPlainTextEdit(frame)
        self.recta_nombre.setGeometry(QRect(170, 200, 151, 25))
        self.plano_nombre = QPlainTextEdit(frame)
        self.plano_nombre.setGeometry(QRect(330, 220, 151, 25))

        self.tercera_proyeccion = QCheckBox(dock_diedrico)
        self.tercera_proyeccion.setGeometry(QRect(58, 3, 111, 17))
        self.ver_puntos = QCheckBox(dock_diedrico)
        self.ver_puntos.setGeometry(QRect(172, 3, 61, 17))
        self.ver_puntos.setChecked(True)
        self.ver_rectas = QCheckBox(dock_diedrico)
        self.ver_rectas.setGeometry(QRect(230, 3, 61, 17))
        self.ver_rectas.setChecked(True)
        self.ver_planos = QCheckBox(dock_diedrico)
        self.ver_planos.setGeometry(QRect(288, 3, 70, 17))
        self.ver_planos.setChecked(True)

        label.setText("Información:")
        label_2.setText("Posición:")
        self.label_3.setText("Primer cuadrante")
        self.label_6.setText("Ángulo vertical:")
        self.label_7.setText("Ángulo horizontal:")
        label_8.setText("Vista:")
        boton_r.setText("Reset (R)")
        boton_alzado.setText("Alzado (1) ''")
        boton_planta.setText("Planta (2) '")
        boton_perfil.setText("Perfil (3) '''")
        label_9.setText("Crear puntos:")
        label_10.setText("Crear rectas:")
        label_11.setText("Crear planos:")
        label_12.setText("Distancia al origen:")
        label_13.setText("Alejamiento:")
        label_14.setText("Cota:")
        label_15.setText("Nombre:")
        boton_punto.setText("Crear")
        boton_recta.setText("Crear")
        boton_plano.setText("Crear")
        label_16.setText("Punto 1:")
        label_17.setText("Punto 2:")
        label_18.setText("Nombre:")
        label_19.setText("Punto 1:")
        label_20.setText("Punto 2:")
        label_21.setText("Nombre:")
        label_22.setText("Punto 3:")
        self.tercera_proyeccion.setText("Tercera proyección")
        self.ver_puntos.setText("Puntos")
        self.ver_rectas.setText("Rectas")
        self.ver_planos.setText("Planos")

        ajustes = QPushButton(frame)
        ajustes.setGeometry(QRect(370, 90, 81, 23))
        ajustes.setText("Ajustes")
        self.ajustes = Ajustes()
        ajustes.clicked.connect(self.ajustes.show)

        widget_punto = QWidget(frame)
        widget_punto.setGeometry(QRect(10, 271, 151, 211))
        vertical_punto = QVBoxLayout(widget_punto)
        vertical_punto.setContentsMargins(0, 0, 0, 0)
        self.lista_puntos = QListWidget(widget_punto)
        vertical_punto.addWidget(self.lista_puntos)

        widget_recta = QWidget(frame)
        widget_recta.setGeometry(QRect(170, 250, 151, 231))
        vertical_recta = QVBoxLayout(widget_recta)
        vertical_recta.setContentsMargins(0, 0, 0, 0)
        self.lista_rectas = QListWidget(widget_recta)
        vertical_recta.addWidget(self.lista_rectas)

        widget_planos = QWidget(frame)
        widget_planos.setGeometry(QRect(330, 271, 151, 211))
        vertical_planos = QVBoxLayout(widget_planos)
        vertical_planos.setContentsMargins(0, 0, 0, 0)
        self.lista_planos = QListWidget(widget_planos)
        vertical_planos.addWidget(self.lista_planos)

        self.puntero_puntos = 15
        self.puntero_rectas = 17
        self.puntero_planos = 0
        self.id_punto = 1
        self.id_recta = 1
        self.id_plano = 1

        self.opciones = []
        self.v = (Point3D(500, 500, 500), Point3D(-500, 500, 500), Point3D(-500, -500, 500),
                  Point3D(500, -500, 500), Point3D(500, 500, -500), Point3D(-500, 500, -500),
                  Point3D(-500, -500, -500), Point3D(500, -500, -500))

        self.p = (Plane(self.v[0], self.v[1], self.v[2]), Plane(self.v[0], self.v[1], self.v[5]),
                  Plane(self.v[0], self.v[4], self.v[7]), Plane(self.v[4], self.v[5], self.v[7]),
                  Plane(self.v[2], self.v[3], self.v[7]), Plane(self.v[1], self.v[2], self.v[5]))

        self.a = (Segment3D(self.v[0], self.v[1]), Segment3D(self.v[1], self.v[2]),
                  Segment3D(self.v[2], self.v[3]), Segment3D(self.v[3], self.v[0]),
                  Segment3D(self.v[0], self.v[4]), Segment3D(self.v[1], self.v[5]),
                  Segment3D(self.v[2], self.v[6]), Segment3D(self.v[3], self.v[7]),
                  Segment3D(self.v[4], self.v[5]), Segment3D(self.v[5], self.v[6]),
                  Segment3D(self.v[6], self.v[7]), Segment3D(self.v[7], self.v[4]))

        self.greek_alphabet = (u'\u03B1', u'\u03B2', u'\u03B3', u'\u03B4', u'\u03B5', u'\u03B6', u'\u03B7', u'\u03B8',
                               u'\u03B9', u'\u03BA', u'\u03BB', u'\u03BC', u'\u03BD', u'\u03BE', u'\u03BF', u'\u03C0',
                               u'\u03C1', u'\u03C3', u'\u03C4', u'\u03C5', u'\u03C6', u'\u03C7', u'\u03C8', u'\u03C9')

        self.actualizar()
        self.setWindowTitle("Dibujo técnico")
        self.setCentralWidget(frame)

    def elegir_puntos_recta(self):
        self.punto_1.clear()
        self.punto_2.clear()
        for i in range(self.lista_puntos.count()):
            self.punto_1.addItem(self.lista_puntos.itemWidget(self.lista_puntos.item(i)).nombre)
            self.punto_2.addItem(self.lista_puntos.itemWidget(self.lista_puntos.item(i)).nombre)

    def elegir_puntos_plano(self):
        self.punto_plano.clear()
        self.punto_plano2.clear()
        self.punto_plano3.clear()
        for i in range(self.lista_puntos.count()):
            self.punto_plano.addItem(self.lista_puntos.itemWidget(self.lista_puntos.item(i)).nombre)
            self.punto_plano2.addItem(self.lista_puntos.itemWidget(self.lista_puntos.item(i)).nombre)
            self.punto_plano3.addItem(self.lista_puntos.itemWidget(self.lista_puntos.item(i)).nombre)

    def actualizar(self):
        self.label_6.setText("Ángulo vertical: " + str(self.renderizador.theta - 360))
        self.label_7.setText("Ángulo horizontal: " + str(self.renderizador.phi))

        y = round(self.renderizador.y, 2)
        z = round(self.renderizador.z, 2)

        if z == 0 and y == 0:
            self.label_3.setText("Línea de tierra")
        elif z == 0:
            if y > 0:
                self.label_3.setText("Plano vertical positivo")
            else:
                self.label_3.setText("Plano vertical negativo")
        elif y == 0:
            if z > 0:
                self.label_3.setText("Plano horizontal positivo")
            else:
                self.label_3.setText("Plano horizontal negativo")
        elif z > 0:
            if y > 0:
                self.label_3.setText("Primer cuadrante")
            else:
                self.label_3.setText("Cuarto cuadrante")
        else:
            if y > 0:
                self.label_3.setText("Segundo cuadrante")
            else:
                self.label_3.setText("Tercer cuadrante")

    def crear_punto(self):
        nombre = self.punto_nombre.toPlainText()

        # Evita que el puntero supere la longitud de la lista
        if self.puntero_puntos == len(ascii_uppercase):
            self.puntero_puntos = 0
        # Genera nombres genéricos si no se provee uno
        if nombre == "":
            nombre = ascii_uppercase[self.puntero_puntos]
            self.puntero_puntos += 1
        # Evita nombres duplicados
        for i in range(self.lista_puntos.count()):
            if self.lista_puntos.itemWidget(self.lista_puntos.item(i)).nombre == nombre:
                nombre = ascii_uppercase[self.puntero_puntos]
                self.puntero_puntos += 1
                break

        # Add placeholder item to List
        item = QListWidgetItem()
        self.lista_puntos.addItem(item)
        # Create Custom Widget
        punto = Punto(self.id_punto, nombre, self.valor_do.value(), self.valor_a.value(), self.valor_c.value())
        self.id_punto += 1
        item.setSizeHint(punto.minimumSizeHint())
        # Set the custom_row widget to be displayed within the placeholder Item
        self.lista_puntos.setItemWidget(item, punto)

        self.elegir_puntos_recta()
        self.elegir_puntos_plano()

    def crear_recta(self):
        punto1 = self.punto_1.currentText()
        punto2 = self.punto_2.currentText()
        nombre = self.recta_nombre.toPlainText()
        for i in range(self.lista_puntos.count()):
            if self.lista_puntos.itemWidget(self.lista_puntos.item(i)).nombre == punto1:
                punto1 = self.lista_puntos.itemWidget(self.lista_puntos.item(i))
            if self.lista_puntos.itemWidget(self.lista_puntos.item(i)).nombre == punto2:
                punto2 = self.lista_puntos.itemWidget(self.lista_puntos.item(i))
        if not punto1 and not punto2:
            QMessageBox.about(self, "Error al crear la recta",
                              "Debes crear al menos dos puntos y seleccionarlos para crear la recta")
        elif punto1.coords == punto2.coords:
            QMessageBox.about(self, "Error al crear la recta",
                              "La recta debe ser creada a partir de dos puntos no coincidentes")
        else:
            if self.puntero_rectas == len(ascii_lowercase):  # Evita que el puntero supere la longitud de la lista
                self.puntero_rectas = 0

            if nombre == "":  # Genera nombres genéricos si no se provee uno
                nombre = ascii_lowercase[self.puntero_rectas]
                self.puntero_rectas += 1

            for i in range(self.lista_rectas.count()):  # Evita nombres duplicados
                if self.lista_rectas.itemWidget(self.lista_rectas.item(i)).nombre == nombre:
                    nombre = ascii_lowercase[self.puntero_rectas]
                    self.puntero_rectas += 1
                    break

            # Add placeholder item to List
            item = QListWidgetItem()
            self.lista_rectas.addItem(item)
            # Create Custom Widget
            recta = Recta(self.id_recta, nombre, punto1, punto2)
            self.id_recta += 1
            item.setSizeHint(recta.minimumSizeHint())
            # Set the custom_row widget to be displayed within the placeholder Item
            self.lista_rectas.setItemWidget(item, recta)

            self.id_recta += 1

    def crear_plano(self):
        punto1 = self.punto_plano.currentText()
        punto2 = self.punto_plano2.currentText()
        punto3 = self.punto_plano3.currentText()
        nombre = self.plano_nombre.toPlainText()

        for i in range(self.lista_puntos.count()):
            if self.lista_puntos.itemWidget(self.lista_puntos.item(i)).nombre == punto1:
                punto1 = self.lista_puntos.itemWidget(self.lista_puntos.item(i))
            if self.lista_puntos.itemWidget(self.lista_puntos.item(i)).nombre == punto2:
                punto2 = self.lista_puntos.itemWidget(self.lista_puntos.item(i))
            if self.lista_puntos.itemWidget(self.lista_puntos.item(i)).nombre == punto3:
                punto3 = self.lista_puntos.itemWidget(self.lista_puntos.item(i))

        if not punto1 and not punto2 and not punto3:
            QMessageBox.about(self, "Error al crear el plano",
                              "Debes crear al menos tres puntos y seleccionarlos para crear el plano")

        elif len({punto1.coords, punto2.coords, punto3.coords}) < 3:
            QMessageBox.about(self, "Error al crear el plano",
                              "Dos de los puntos proporcionados son coincidentes")
        elif Point3D.is_collinear(Point3D(punto1.coords), Point3D(punto2.coords), Point3D(punto3.coords)):
            QMessageBox.about(self, "Error al crear el plano",
                              "El plano debe ser creado por tres puntos no alineados")

        else:
            # Evita que el puntero supere la longitud de la lista
            if self.puntero_planos == len(self.greek_alphabet):
                self.puntero_planos = 0

            # Genera nombres genéricos si no se provee uno
            if nombre == "":
                nombre = self.greek_alphabet[self.puntero_planos]
                self.puntero_planos += 1

            for i in range(self.lista_planos.count()):  # Evita nombres duplicados
                if self.lista_planos.itemWidget(self.lista_planos.item(i)).nombre == nombre:
                    nombre = self.greek_alphabet[self.puntero_planos]
                    self.puntero_planos += 1
                    break

            # Add placeholder item to List
            item = QListWidgetItem()
            self.lista_planos.addItem(item)
            # Create Custom Widget
            plano = Plano(self.id_plano, nombre, punto1, punto2, punto3)
            item.setSizeHint(plano.minimumSizeHint())
            # Set the custom_row widget to be displayed within the placeholder Item
            self.lista_planos.setItemWidget(item, plano)

            self.id_plano += 1

    def borrar_punto(self, idd):
        for indx in range(self.lista_puntos.count()):
            item = self.lista_puntos.item(indx)
            widget = self.lista_puntos.itemWidget(item)
            if widget.id == idd:
                self.lista_puntos.takeItem(self.lista_puntos.row(item))
                break
        self.elegir_puntos_recta()
        self.elegir_puntos_plano()

    def borrar_recta(self, idd):
        for indx in range(self.lista_rectas.count()):
            item = self.lista_rectas.item(indx)
            widget = self.lista_rectas.itemWidget(item)
            if widget.id == idd:
                self.lista_rectas.takeItem(self.lista_rectas.row(item))
                break

    def borrar_plano(self, idd):
        for indx in range(self.lista_planos.count()):
            item = self.lista_planos.item(indx)
            widget = self.lista_planos.itemWidget(item)
            if widget.id == idd:
                self.lista_planos.takeItem(self.lista_planos.row(item))
                break


if __name__ == "__main__":
    MainEvent = QApplication([])
    main_app = Ventana()
    main_app.diedrico.zoom_out()
    main_app.diedrico.zoom_out()
    main_app.show()
    MainEvent.exec()
