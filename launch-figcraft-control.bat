@echo off
echo Starting FigCraft with loopback control port 47800...
start "" "C:\Program Files\ArtCraft\FigCraft\figcraft.exe" --control 47800 "%~dp0design\kamartha-design.figcraft"

