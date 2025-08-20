#!/bin/bash
# Start display components for Pi Analytics Dashboard

# Start matchbox window manager (no decorations, no cursor)
matchbox-window-manager -use_titlebar no -use_cursor no &
sleep 2

# Start surf browser in fullscreen
exec surf -F http://localhost:80