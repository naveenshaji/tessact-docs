# Screenshot treatment

Composites raw app screenshots onto the macOS-wallpaper style used across the docs
(`images/admin/*-live-v2.jpg`, `images/livestream/`, `images/ai-search/`).

Usage:

```
python3 treat.py <input.png> <output.jpg>            # desktop mode: 1600x1000 canvas
python3 treat.py <input.png> <output.jpg> compact    # compact mode: canvas hugs the window (strips/close-ups)
python3 treat.py bg                                  # rebuild the wallpaper canvas from an admin-v2 image
```

Requires Pillow, numpy, and opencv-python.
