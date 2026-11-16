"""Movie files of the 2D tab: the prepared images of the slider positions
(output.movie) written at the frame rate of the time box, as MP4, MOV,
WebM or AVI through ffmpeg (where it is installed: PATH or the ffmpeg of
matplotlib), or as an animated GIF through Pillow."""

import shutil
import subprocess

import numpy as np
from matplotlib import rcParams

# extension: (name, ffmpeg encoder and options or None for Pillow)
FORMATS = {
    ".mp4": ("MP4 video (H.264)", ["-c:v", "libx264", "-crf", "18",
                                   "-pix_fmt", "yuv420p"]),
    ".mov": ("QuickTime video (H.264)", ["-c:v", "libx264", "-crf", "18",
                                         "-pix_fmt", "yuv420p"]),
    ".webm": ("WebM video (VP9)", ["-c:v", "libvpx-vp9", "-crf", "30",
                                   "-b:v", "0", "-pix_fmt", "yuv420p"]),
    ".avi": ("AVI video (MPEG-4)", ["-c:v", "mpeg4", "-q:v", "2",
                                    "-pix_fmt", "yuv420p"]),
    ".gif": ("Animated GIF", None),
}


def ffmpeg():
    """The ffmpeg program, or None."""
    path = rcParams.get("animation.ffmpeg_path", "ffmpeg")
    return shutil.which(path) or shutil.which("ffmpeg")


def formats():
    """[(extension, name)] of the formats that can be written here."""
    video = ffmpeg() is not None
    return [(ext, name) for ext, (name, codec) in FORMATS.items()
            if codec is None or video]


def filters():
    """The filters of the file dialog, the first format first."""
    return ";;".join("%s (*%s)" % (name, ext) for ext, name in formats())


def write(path, frames, fps):
    """Write the frames (RGBA arrays of one size, in order) as a movie
    at fps frames per second, the format from the extension of path."""
    ext = "." + path.rsplit(".", 1)[-1].lower()
    name, codec = FORMATS[ext]
    if codec is None:
        _gif(path, frames, fps)
        return
    h, w = frames[0].shape[:2]
    cmd = [ffmpeg(), "-y", "-loglevel", "error", "-f", "rawvideo",
           "-pix_fmt", "rgba", "-s", "%dx%d" % (w, h), "-r", str(fps),
           "-i", "-", "-vf", "pad=ceil(iw/2)*2:ceil(ih/2)*2:color=white"]
    proc = subprocess.Popen(cmd + codec + [path], stdin=subprocess.PIPE,
                            stderr=subprocess.PIPE)
    try:
        for f in frames:
            proc.stdin.write(np.ascontiguousarray(f).tobytes())
        proc.stdin.close()
    except BrokenPipeError:
        pass
    err = proc.stderr.read().decode(errors="replace")
    if proc.wait() != 0:
        raise OSError("ffmpeg: " + (err.strip().splitlines() or ["failed"])[
            -1])


def _gif(path, frames, fps):
    from PIL import Image
    images = [Image.fromarray(np.ascontiguousarray(f[..., :3]))
              .quantize(colors=256, method=Image.Quantize.MEDIANCUT)
              for f in frames]
    images[0].save(path, save_all=True, append_images=images[1:],
                   duration=max(int(round(1000.0 / fps)), 20), loop=0,
                   optimize=False)
