import subprocess
from fractions import Fraction

  
ffprobePath = "ffprobe"


def runFfprobe(cmd):
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out, err = proc.communicate()
    if proc.returncode != 0:
        raise RuntimeError(f"ffprobe error: {err.decode()}")
    return out.decode().strip()


def framesToTimecode(frameCount, frameRate):
    totalSeconds = frameCount / frameRate
    h = int(totalSeconds // 3600)
    m = int((totalSeconds % 3600) // 60)
    s = int(totalSeconds % 60)

    # Account for rounding errors
    f = int((totalSeconds - int(totalSeconds)) * frameRate)
    if f >= int(frameRate):
        f = int(frameRate) - 1

    return f"{h:02}:{m:02}:{s:02}:{f:02}"


def getStartTimeCode(videoPath):
    timecodeCmd = [
        ffprobePath, "-v", "error",
        "-select_streams", "v:0",
        "-show_entries", "stream_tags=timecode",
        "-of", "default=nokey=1:noprint_wrappers=1",
        videoPath
    ]
    startTc = runFfprobe(timecodeCmd)

    return startTc


def getVideoDuration(videoPath):
    # Get duration (in seconds)
    durationCmd = [
        ffprobePath, "-v", "error",
        "-show_entries", "format=duration",
        "-of", "default=nokey=1:noprint_wrappers=1",
        videoPath
    ]
    durationSec = float(runFfprobe(durationCmd))

    return durationSec


def getFrameRate(videoPath):
    framerateCmd = [
        ffprobePath, "-v", "error",
        "-select_streams", "v:0",
        "-show_entries", "stream=r_frame_rate",
        "-of", "default=nokey=1:noprint_wrappers=1",
        videoPath
    ]
    frameRate = float(Fraction(runFfprobe(framerateCmd)))
    return frameRate


def getVideoTimeCode(path):
    # Get SMPTE start timecode
    startTc = getStartTimeCode(path)
    if not startTc:
        return None, None

    durationSec = getVideoDuration(path)
    frameRate = getFrameRate(path)

    # Normalize timecode (handle drop-frame with semicolon)
    dropFrame = False
    if ";" in startTc:
        dropFrame = True
        startTc = startTc.replace(";", ":")

    # Determine frame count for start and end of video
    h, m, s, f = map(int, startTc.split(":"))
    totalStartFrames = int((h * 3600 + m * 60 + s) * frameRate + f)
    totalEndFrames = totalStartFrames + int(durationSec * frameRate)

    endTc = framesToTimecode(totalEndFrames, frameRate)
    if dropFrame:
        startTc = f"{h}:{m:02}:{s:02};{f:02}"

        h, m, s, f = map(int, endTc.split(":"))
        endTc = f"{h}:{m:02}:{s:02};{f:02}"

    return startTc, endTc
