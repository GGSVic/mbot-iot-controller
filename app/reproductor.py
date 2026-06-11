# Standard Library
import os
import time
from pathlib import Path

# Third-Party Libraries
import eyed3
import pygame
import pyrebase

# Hardware
from board import SCL, SDA
import busio
import adafruit_ssd1306

# Image Processing
from PIL import Image, ImageDraw, ImageFont

# GUI
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtGui import QIcon, QPixmap

# -----------------------------------------------------------------------------
# OLED Display Initialization
# -----------------------------------------------------------------------------
#
# Initializes the SSD1306 OLED display connected through I2C.
# The display was used to provide real-time feedback to the user,
# including information such as the currently selected song.
#

i2c = busio.I2C(SCL, SDA)
disp = adafruit_ssd1306.SSD1306_I2C(128, 64, i2c)
disp.fill(0)
disp.show()
width = disp.width
height = disp.height

# -----------------------------------------------------------------------------
# Firebase Initialization
# -----------------------------------------------------------------------------
#
# Configure and establish the connection with the Firebase
# Realtime Database used for communication between the
# desktop application and the embedded devices.
#

# Firebase project credentials
config = {
    "apiKey": "AIzaSyBMHJxkLAUbJneLDtkdPXEZMq45TpXAdBE",
    "authDomain": "sp32-5f852.firebaseapp.com",
    "projectId": "sp32-5f852",
    "storageBucket": "sp32-5f852.appspot.com",
    "messagingSenderId": "725191069368",
    "appId": "1:725191069368:web:7eb768e8a20defb6c76e4d",
    "measurementId": "G-JEF8STBLC1",
    "databaseURL": "https://sp32-5f852-default-rtdb.firebaseio.com",
}

# Attempt to connect to Firebase until a valid
# connection is established.
connected = False
while not connected : 
    try: 
        firebase = pyrebase.initialize_app(config)
        db = firebase.database()
        connected = True
        print("Conexion exitosa")
    except Exception as e : 
        print ("Error al conectar la base de datos")
        print ("\nReintentando...")
        time.sleep(3)

# -----------------------------------------------------------------------------
# Application Resources
# -----------------------------------------------------------------------------

script_dir = Path(__file__).resolve().parent
assets_imgs = script_dir + "/assets/images"
assets_songs = script_dir + "/assets/songs"

# Main Application Window
# -----------------------------------------------------------------------------
#
# Defines the graphical user interface used to control the
# MBot and interact with the integrated MP3 player.
#
# The interface was developed using PyQt5 and includes:
# - Multimedia controls
# - Song selection
# - Robot movement controls
# - Firebase integration
#

class Ui_Reproductor(object):
    def setupUi(self, Reproductor):

        # Configre main application window 
        Reproductor.setObjectName("Reproductor")
        Reproductor.resize(520, 298)

        # Background image
        Reproductor.setStyleSheet(f"background-image: url({assets_imgs / 'FondoG.jpeg'})")
        
        self.widget = QtWidgets.QWidget(Reproductor)
        self.widget.setGeometry(QtCore.QRect(0, 10, 521, 281))
        self.widget.setAutoFillBackground(False)
        self.widget.setStyleSheet("")
        self.widget.setObjectName("widget")

        # Main controller for interface elements 
        self.formLayoutWidget = QtWidgets.QWidget(self.widget)
        self.formLayoutWidget.setGeometry(QtCore.QRect(130, 50, 110, 93))
        self.formLayoutWidget.setObjectName("formLayoutWidget")
        self.formLayout = QtWidgets.QFormLayout(self.formLayoutWidget)
        self.formLayout.setContentsMargins(0, 0, 0, 0)
        self.formLayout.setObjectName("formLayout")

        # -----------------------------------------------------------------------------
        # Song Information Panel
        # -----------------------------------------------------------------------------

        # Song title
        self.label = QtWidgets.QLabel(self.formLayoutWidget)
        font = QtGui.QFont()
        font.setFamily("Maiandra GD")
        font.setPointSize(9)
        font.setBold(True)
        font.setWeight(75)
        self.label.setFont(font)
        self.label.setAutoFillBackground(False)
        self.label.setStyleSheet("color: white")
        self.label.setObjectName("label")
        self.formLayout.setWidget(0, QtWidgets.QFormLayout.LabelRole, self.label)

        # Artist name 
        self.label_2 = QtWidgets.QLabel(self.formLayoutWidget)
        font = QtGui.QFont()
        font.setFamily("Maiandra GD")
        font.setPointSize(8)
        font.setBold(True)
        font.setWeight(75)
        self.label_2.setFont(font)
        self.label_2.setStyleSheet("color: #87CEEB")
        self.label_2.setObjectName("label_2")
        self.formLayout.setWidget(1, QtWidgets.QFormLayout.LabelRole, self.label_2)

        # Album name 
        self.label_3 = QtWidgets.QLabel(self.formLayoutWidget)
        font = QtGui.QFont()
        font.setFamily("Maiandra GD")
        font.setPointSize(7)
        font.setBold(True)
        font.setWeight(75)
        self.label_3.setFont(font)
        self.label_3.setStyleSheet("color: #87CEEB")
        self.label_3.setObjectName("label_3")
        self.formLayout.setWidget(2, QtWidgets.QFormLayout.LabelRole, self.label_3)

        # Album cover  
        self.imagen = QtWidgets.QPushButton(self.widget)
        self.imagen.setGeometry(QtCore.QRect(20, 40, 101, 101))
        self.imagen.setStyleSheet("border: none")
        self.imagen.setText("")
        icon1 = QtGui.QIcon()
        icon1.addPixmap(QtGui.QPixmap(f"{assets_imgs}/notStart.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.imagen.setIcon(icon1)
        self.imagen.setIconSize(QtCore.QSize(101, 101))
        self.imagen.setObjectName("imagen")

        # -----------------------------------------------------------------------------
        # Playback Controls
        # -----------------------------------------------------------------------------

        # Song progress slider
        # Allows the user to visualize and modify the current
        # playback position of the selected track.
        self.horizontalSlider = QtWidgets.QSlider(self.widget)
        self.horizontalSlider.setGeometry(QtCore.QRect(20, 170, 201, 22))
        self.horizontalSlider.setAutoFillBackground(False)
        self.horizontalSlider.setStyleSheet("QSlider::groove:horizontal {\n"
        "background-color:  #C0C0C0;\n"
        "height: 10px;}"
        "QSlider::handle:horizontal {\n"
        "background-color:#2F4F4F;\n"
        "width: 15px;}")
        self.horizontalSlider.setOrientation(QtCore.Qt.Horizontal)
        self.horizontalSlider.setObjectName("horizontalSlider")

        # Play / Pause button 
        self.pushButton = QtWidgets.QPushButton(self.widget)
        self.pushButton.setEnabled(True)
        self.pushButton.setGeometry(QtCore.QRect(75, 210, 40, 40))
        self.pushButton.setMouseTracking(False)
        self.pushButton.setAcceptDrops(False)
        self.pushButton.setAutoFillBackground(False)
        self.pushButton.setStyleSheet("border: none;")
        self.pushButton.setText("")

        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap(f"{assets_imgs}/play.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        
        self.pushButton.setIcon(icon)
        self.pushButton.setIconSize(QtCore.QSize(40, 40))
        self.pushButton.setCheckable(False)
        self.pushButton.setObjectName("pushButton")

        # Stop / Reset button 
        self.pushButton_2 = QtWidgets.QPushButton(self.widget)
        self.pushButton_2.setGeometry(QtCore.QRect(130, 210, 40, 40))
        self.pushButton_2.setStyleSheet("border: none")
        self.pushButton_2.setText("")

        icon2 = QtGui.QIcon()
        icon2.addPixmap(QtGui.QPixmap(f"{assets_imgs}/reset.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)

        self.pushButton_2.setIcon(icon2)
        self.pushButton_2.setIconSize(QtCore.QSize(40, 40))
        self.pushButton_2.setObjectName("pushButton_2")
        self.textBrowser = QtWidgets.QTextBrowser(self.widget)
        self.textBrowser.setGeometry(QtCore.QRect(240, 30, 241, 111))
        font = QtGui.QFont()
        font.setPointSize(8)

        # Previous track button 
        self.pushButton_3 = QtWidgets.QPushButton(self.widget)
        self.pushButton_3.setGeometry(QtCore.QRect(20, 210, 40, 40))
        self.pushButton_3.setMinimumSize(QtCore.QSize(2, 0))
        self.pushButton_3.setStyleSheet("border: none")
        self.pushButton_3.setText("")

        icon3 = QtGui.QIcon()
        icon3.addPixmap(QtGui.QPixmap(f"{assets_imgs}/back.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
      
        self.pushButton_3.setIcon(icon3)
        self.pushButton_3.setIconSize(QtCore.QSize(40, 40))
        self.pushButton_3.setObjectName("pushButton_3")

        # Next track button 
        self.pushButton_4 = QtWidgets.QPushButton(self.widget)
        self.pushButton_4.setGeometry(QtCore.QRect(185, 210, 40, 40))
        self.pushButton_4.setStyleSheet("border: none")
        self.pushButton_4.setText("")

        icon4 = QtGui.QIcon()
        icon4.addPixmap(QtGui.QPixmap(f"{assets_imgs}/next.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        
        self.pushButton_4.setIcon(icon4)
        self.pushButton_4.setIconSize(QtCore.QSize(40, 40))
        self.pushButton_4.setObjectName("pushButton_4")

        # -----------------------------------------------------------------------------
        # Robot Control Panel
        # -----------------------------------------------------------------------------

        # MBot visual representation 
        self.mbot = QtWidgets.QPushButton(self.widget)
        self.mbot.setGeometry(QtCore.QRect(250, 160, 101, 101))
        self.mbot.setStyleSheet("border: none")
        self.mbot.setText("")

        icon4 = QtGui.QIcon()
        icon4.addPixmap(QtGui.QPixmap(f"{assets_imgs}/mbot.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
      
        self.mbot.setIcon(icon4)
        self.mbot.setIconSize(QtCore.QSize(60, 60))
        self.mbot.setObjectName("pushButton_5")

        # Forward movement button 
        self.forward= QtWidgets.QPushButton(self.widget)
        self.forward.setGeometry(QtCore.QRect(423, 132, 45, 51))
        self.forward.setStyleSheet("border: none")
        self.forward.setText("")
        
        icon4 = QtGui.QIcon()
        icon4.addPixmap(QtGui.QPixmap(f"{assets_imgs}/up.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        
        self.forward.setIcon(icon4)
        self.forward.setIconSize(QtCore.QSize(45, 45))
        self.forward.setObjectName("pushButton_6")

        # Backward movement button 
        self.backward = QtWidgets.QPushButton(self.widget)
        self.backward.setGeometry(QtCore.QRect(423, 225, 45, 51))
        self.backward.setStyleSheet("border: none")
        self.backward.setText("")

        icon4 = QtGui.QIcon()
        icon4.addPixmap(QtGui.QPixmap(f"{assets_imgs}/down.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
      
        self.backward.setIcon(icon4)
        self.backward.setIconSize(QtCore.QSize(45, 45))
        self.backward.setObjectName("pushButton_7")

        # Right turn button 
        self.right = QtWidgets.QPushButton(self.widget)
        self.right.setGeometry(QtCore.QRect(460, 182, 61, 45))
        self.right.setStyleSheet("border: none")
        self.right.setText("")

        icon4 = QtGui.QIcon()
        icon4.addPixmap(QtGui.QPixmap(f"{assets_imgs}/right.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        
        self.right.setIcon(icon4)
        self.right.setIconSize(QtCore.QSize(45, 45))
        self.right.setObjectName("pushButton_8")

        # Left turn button 
        self.left = QtWidgets.QPushButton(self.widget)
        self.left.setGeometry(QtCore.QRect(368, 182, 61, 45))
        self.left.setStyleSheet("border: none")
        self.left.setText("")

        icon4 = QtGui.QIcon()
        icon4.addPixmap(QtGui.QPixmap(f"{assets_imgs}/left.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        
        self.left.setIcon(icon4)
        self.left.setIconSize(QtCore.QSize(45, 45))
        self.left.setObjectName("pushButton_8")

        # Stop button 
        self.stopM = QtWidgets.QPushButton(self.widget)
        self.stopM.setGeometry(QtCore.QRect(420, 180, 50, 50))
        self.stopM.setStyleSheet("border: none")
        self.stopM.setText("")

        icon4 = QtGui.QIcon()
        icon4.addPixmap(QtGui.QPixmap(f"{assets_imgs}/stopMBot.jpg"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
      
        self.stopM.setIcon(icon4)
        self.stopM.setIconSize(QtCore.QSize(50, 50))
        self.stopM.setObjectName("pushButton_9")

        # -----------------------------------------------------------------------------
        # Song Library Panel
        # -----------------------------------------------------------------------------

        # Song list display
        # Shows the available songs and allows direct song selection.        
        self.textBrowser.setFont(font)
        self.textBrowser.setGeometry(QtCore.QRect(240,30,241,91))
        self.textBrowser.setStyleSheet("color: white;border: none")
        self.textBrowser.setObjectName("textBrowser")
        scrollbar = self.textBrowser.verticalScrollBar()
        scrollbar.setFixedWidth(8)
        scrollbar.setStyleSheet("background-color: #87CEEB;")
        self.textBrowser.setOpenLinks(False)
        self.textBrowser.setObjectName("textBrowser")

        # Playback state variables 
        self.actualSong = 0
        self.canciones = []
        self.start = False
        self.sliderMoving = False
        self.posSlider = 0
        self.duration = 0
        self.isplaying = False

        # -----------------------------------------------------------------------------
        # User Interface Events
        # -----------------------------------------------------------------------------

        # Multimedia controls 
        self.pushButton.clicked.connect(self.play_Pause)
        self.pushButton_2.clicked.connect(self.stop)
        self.pushButton_3.clicked.connect(self.back)
        self.pushButton_4.clicked.connect(self.next)

        # Robot controls 
        self.forward.clicked.connect(self.moveMB_Forward)
        self.backward.clicked.connect(self.moveMB_Backward)
        self.right.clicked.connect(self.moveMB_Right)
        self.left.clicked.connect(self.moveMB_Left)
        self.stopM.clicked.connect(self.moveMB_Stop)

        # Song selection 
        self.textBrowser.anchorClicked.connect(self.songSelection)
        
        # Playback progress slider 
        self.horizontalSlider.sliderPressed.connect(self.stopAnimation)
        self.horizontalSlider.sliderReleased.connect(self.sliderMove)

        # -----------------------------------------------------------------------------
        # Periodic Tasks
        # -----------------------------------------------------------------------------

        # Updates the playback progress bar
        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.sliderAnimation)
        self.timer.start(1000)
        
        # Polls Firebase for remote commmands and updates 
        self.timer2 = QtCore.QTimer()
        self.timer2.timeout.connect(self.readFirebase)
        self.timer.start(1000)

        self.retranslateUi(Reproductor)
        QtCore.QMetaObject.connectSlotsByName(Reproductor)
    
    # -----------------------------------------------------------------------------
    # User Interface Initialization
    # -----------------------------------------------------------------------------
    #
    # Loads the song library and initializes the main labels.
    #
    def retranslateUi(self, Reproductor):
        _translate = QtCore.QCoreApplication.translate
        Reproductor.setWindowTitle(_translate("Reproductor", "Dialog"))
        self.label.setText(_translate("Reproductor", "Canción"))
        self.label_2.setText(_translate("Reproductor", "Artista"))
        self.label_3.setText(_translate("Reproductor", "Álbum"))

        # Agregamos las canciones al textBrowser como links:
        directorio = os.path.join(os.getcwd(), "Musica")
        archivos = os.listdir(directorio)  # Generamos una lista de los archivos
        i = 1
        for archivo in archivos:
            self.canciones.append(archivo)
            cancion = str(i) + ". " + archivo.replace(".mp3", "")
            link = f'<a href="{i}" style="text-decoration: none; color: white;">{cancion}</a>'
            self.textBrowser.append(link)
            i += 1

    # -----------------------------------------------------------------------------
    # Song Selection
    # -----------------------------------------------------------------------------
    #
    # Triggered when the user selects a song from the song list.
    #
    def songSelection(self, url):
        self.actualSong = int(url.toString()) - 1
        self.startSong()
        self.imprimeNombres()

    # -----------------------------------------------------------------------------
    # Playback Controls
    # -----------------------------------------------------------------------------
    #
    # Handles play, pause and resume operations.
    #
    def play_Pause(self):   
        if self.start == False:
            self.startSong()
            self.isplaying = True
            self.imprimeNombres()
        elif(pygame.mixer.music.get_busy() and self.isplaying == True):
            self.sliderMoving = False
            pygame.mixer.music.pause()
            self.isplaying = False
        else:
            self.sliderMoving = True
            pygame.mixer.music.unpause()
            self.isplaying = True
            self.imprimeNombres()
        self.updateBotton()

    # Stop playback and reset the player state.
    def stop(self):
        self.isplaying = False
        self.start = False
        self.sliderMoving = False
        self.actualSong = 0
        self.horizontalSlider.setValue(0)
        pygame.mixer.music.pause()
        self.updateBotton()
        _translate = QtCore.QCoreApplication.translate
        self.label.setText(_translate("Reproductor", "Pista"))
        self.label_2.setText(_translate("Reproductor", "Artista"))
        self.label_3.setText(_translate("Reproductor", "Album"))
        icon1 = QtGui.QIcon()
        icon1.addPixmap(QtGui.QPixmap(f"{assets_imgs}/notStart.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.imagen.setIcon(icon1)
        self.imagen.setIconSize(QtCore.QSize(101, 101))
        self.imagen.setObjectName("imagen")
        image2 = Image.new('1', (width, height))
        draw2 = ImageDraw.Draw(image2)
        draw2.rectangle((200,200,width,height), outline=300, fill=270)
        disp.image(image2)
        disp.show()

    # Load and play the next track in the playlist.
    def next(self):
        if self.start == True:
            if self.actualSong + 1 == len(self.canciones):
                self.actualSong = 0
            else:
                self.actualSong += 1
        self.startSong()
        self.imprimeNombres()

    # Return to the previous track or restart the current one.
    def back(self):
        if self.posSlider < 3:
            if self.actualSong == 0:
                self.actualSong = len(self.canciones) - 1
            else:
                self.actualSong -= 1
        self.startSong()
        self.imprimeNombres()

    # -----------------------------------------------------------------------------
    # Song Loading
    # -----------------------------------------------------------------------------
    #
    # Loads the selected song, updates metadata,
    # cover art and playback information.
    #
    def startSong(self):

        self.start = True
        self.sliderMoving = True
        self.posSlider = 0
        self.isplaying = True

        songName = str(self.canciones[self.actualSong])
        ruta = os.path.join(os.getcwd(), "Musica", songName)

        pygame.mixer.init()  # Starts the mixer
        pygame.mixer.music.load(ruta)
        pygame.mixer.music.play()
        audiofile = eyed3.load(ruta)
        self.updateBotton()

        lenSong = audiofile.info.time_secs # Se extraen datos
        self.horizontalSlider.setMaximum(int(lenSong))
        self.duration = lenSong

        title = str(audiofile.tag.title)
        if len(title) > 12:
            title = title[0:10] + "..."
        artist = str(audiofile.tag.artist)
        if len(artist) > 15:
            artist = artist[0:12] + "..."
        album = str(audiofile.tag.album)
        if len(album) > 15:
            album = album[0:12] + "..."

        self.label.setText(title)
        self.label_2.setText(artist)
        self.label_3.setText(album)

        if audiofile.tag.images:
            image_data = audiofile.tag.images[0].image_data
            pixmap = QPixmap()
            pixmap.loadFromData(image_data)
            self.imagen.setIcon(QIcon(pixmap))
        else:
            icon1 = QtGui.QIcon()
            icon1.addPixmap(QtGui.QPixmap(f"{assets_imgs}/unknown.jpg"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
            self.imagen.setIcon(icon1)
            self.imagen.setIconSize(QtCore.QSize(101, 101))
            self.imagen.setObjectName("imagen")
            
        self.imprimeNombres()

    # -----------------------------------------------------------------------------
    # Playback Progress Management
    # -----------------------------------------------------------------------------
    #
    # Updates the progress slider while a song is playing.
    #
    def sliderAnimation(self):
        if self.sliderMoving:
            self.horizontalSlider.setValue(self.posSlider)
            self.posSlider = self.posSlider + 1
        if self.posSlider > self.duration and self.start:
            self.posSlider = 0
            self.next()
        self.readFirebase()

    # Temporarily stop slider updates while the user drags it.
    def stopAnimation(self):
        self.sliderMoving = False

    # Seek to a new playback position selected by the user.
    def sliderMove(self):
        if(self.start):
            newPosition = self.horizontalSlider.value()
            self.horizontalSlider.setValue(newPosition)
            self.posSlider = newPosition
            pygame.mixer.music.set_pos(self.posSlider)
            self.sliderMoving = True
        else:
            self.horizontalSlider.setValue(0)

    # Update play/pause button icon according to playback state.
    def updateBotton(self):
        icon = QtGui.QIcon()
        if pygame.mixer.music.get_busy() and self.isplaying == True:
            icon.addPixmap(QtGui.QPixmap(f"{assets_imgs}/stop.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        else:
            icon.addPixmap(QtGui.QPixmap(f"{assets_imgs}/play.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.pushButton.setIcon(icon)
        self.pushButton.setIconSize(QtCore.QSize(40, 40))

    # -----------------------------------------------------------------------------
    # Robot Control Commands
    # -----------------------------------------------------------------------------
    #
    # Send movement commands to the MBot through Firebase.
    #
    def moveMB_Forward(self):
        db.child("test").update({"dir":"F"})
        db.child("test").update({"act":"Avanza hacia delante"})

    def moveMB_Backward(self):
        db.child("test").update({"dir":"B"})
        db.child("test").update({"act":"Avanza hacia atras"})

    def moveMB_Left(self):
        db.child("test").update({"dir":"L"})
        db.child("test").update({"act":"Gira hacia la izquierda"})

    def moveMB_Right(self):
        db.child("test").update({"dir":"R"})
        db.child("test").update({"act":"Gira hacia la derecha"})

    def moveMB_Stop(self):
        db.child("test").update({"dir":"S"})
        db.child("test").update({"act":"Detenido"})
    
    # -----------------------------------------------------------------------------
    # OLED Display Update
    # -----------------------------------------------------------------------------
    #
    # Updates the SSD1306 display with the current
    # song information.
    #
    def imprimeNombres(self):
        songName = str(self.canciones[self.actualSong])
        ruta = os.path.join(os.getcwd(), "Musica", songName)
        audiofile = eyed3.load(ruta)
        title = str(audiofile.tag.title)
        artist = str(audiofile.tag.artist)
        album = str(audiofile.tag.album)
        image = Image.new('1', (width, height))
        draw = ImageDraw.Draw(image)
        font = ImageFont.load_default()
        draw.rectangle((200,200,width,height), outline=300, fill=270)
        #draw.line((5,15, 100, 15), fill=270)
        #draw.line((5,50, 100, 50), fill=270)
        draw.text((5, 10), title, font=font, fill=280)
        disp.image(image)
        disp.show()
        #time.sleep(2)
        draw.text((5, 25), artist, font=font, fill=280)
        disp.image(image)
        disp.show()
        #time.sleep(2)
        draw.text((5, 40), album, font=font, fill=280)
        disp.image(image)
        disp.show()
        #time.sleep(2)

    # -----------------------------------------------------------------------------
    # Firebase Synchronization
    # -----------------------------------------------------------------------------
    #
    # Processes remote commands received from Firebase and
    # handles sensor-triggered events generated by the MBot.
    #
    def readFirebase(self):
        dataB = db.child("test").get()

        for data in dataB.each():
            if data.key() == "mp3":
                if data.val() == "Next":
                    self.next()
                   # db.child("test").update({"mp3": ""})
                elif data.val() == "Prev":
                    self.back()
                   # db.child("test").update({"mp3": ""})
                elif data.val() == "PP":
                    if(self.start == False):
                        self.startSong()
                    elif(self.isplaying == True or self.isplaying == False): 
                        self.play_Pause()
                    #db.child("test").update({"mp3": ""})
                elif data.val() == "Stop" and self.isplaying == True: 
                    self.stop()
                    #db.child("test").update({"mp3": ""})
                elif data.val() != "":
                    try: 
                        self.actualSong = int(data.val()) - 1
                        self.startSong()
                    except ValueError: 
                        pass
                db.child("test").update({"mp3": ""})
                    
            
                    
            if data.key() == "sensor":
                if data.val() == 32:
                    self.actualSong = self.actualSong -1
                    self.startSong()
                    self.moveMB_Forward()
                    time.sleep(3)
                    self.moveMB_Stop()
                    
                elif data.val() == 30:
                    self.next()
                    self.moveMB_Backward()
                    time.sleep(3)
                    self.moveMB_Stop()
                
                elif data.val() == 28:
                    self.next()
                    self.moveMB_Left()
                    time.sleep(3)
                    self.moveMB_Right()
                    time.sleep(3)
                    self.moveMB_Stop()
                    
                db.child("test").update({"sensor": ""})
       
        
# Application Entry Point        
if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    Reproductor = QtWidgets.QDialog()
    ui = Ui_Reproductor()
    ui.setupUi(Reproductor)
    Reproductor.show()
    sys.exit(app.exec_())

