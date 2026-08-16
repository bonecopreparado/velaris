import QtQuick 2.15
import calamares.slideshow 1.0

Presentation {
    id: presentation

    Slide {
        anchors.fill: parent

        Image {
            anchors.fill: parent
            source: "file:///usr/share/wallpapers/velaris/contents/images/velaris_desktop.png"
            fillMode: Image.PreserveAspectCrop
            smooth: true
        }

        Rectangle {
            anchors.fill: parent
            color: "#b30d1b2a"
        }

        Column {
            width: parent.width * 0.82
            spacing: 18
            anchors.centerIn: parent

            Image {
                width: Math.min(220, parent.width * 0.45)
                height: width
                anchors.horizontalCenter: parent.horizontalCenter
                source: "logo.png"
                fillMode: Image.PreserveAspectFit
                smooth: true
                mipmap: true
            }

            Text {
                width: parent.width
                text: qsTr("Installing Velaris")
                color: "#ffffff"
                font.pixelSize: 28
                font.bold: true
                horizontalAlignment: Text.AlignHCenter
            }

            Text {
                width: parent.width
                text: qsTr("Preparing a fast, stable, and ready-to-use system.")
                color: "#d7e8ff"
                font.pixelSize: 16
                wrapMode: Text.WordWrap
                horizontalAlignment: Text.AlignHCenter
            }

            Text {
                width: parent.width
                text: qsTr("Arch Linux  •  KDE Plasma  •  Kernel CachyOS")
                color: "#78b7ff"
                font.pixelSize: 14
                horizontalAlignment: Text.AlignHCenter
            }
        }
    }

    function onActivate() {
        presentation.currentSlide = 0;
    }

    function onLeave() {
    }
}
