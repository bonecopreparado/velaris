import QtQuick 2.0
import calamares.slideshow 1.0

Presentation {
    id: presentation

    Slide {
        Image {
            id: background
            source: "logo.png"
            width: 200
            height: 200
            fillMode: Image.PreserveAspectFit
            anchors.centerIn: parent
        }
        Text {
            anchors.horizontalCenter: parent.horizontalCenter
            anchors.top: background.bottom
            anchors.topMargin: 20
            text: "Installing Velaris OS..."
            color: "white"
            font.pixelSize: 24
        }
        Text {
            anchors.horizontalCenter: parent.horizontalCenter
            anchors.bottom: parent.bottom
            anchors.bottomMargin: 40
            text: "Arch Linux • KDE Plasma • CachyOS Kernel"
            color: "#aaaaaa"
            font.pixelSize: 14
        }
    }
}
