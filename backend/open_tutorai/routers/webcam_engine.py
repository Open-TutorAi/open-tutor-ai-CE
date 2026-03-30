import cv2, mediapipe as mp, numpy as np, threading, time, logging
logger = logging.getLogger("webcam_engine")
_latest_score = 0.5
_running = False
_thread = None
_lock = threading.Lock()
LEFT_EYE=[362,385,387,263,373,380]; RIGHT_EYE=[33,160,158,133,153,144]
LEFT_IRIS=[474,475,476,477]; RIGHT_IRIS=[469,470,471,472]

def _ear(lm,idx):
    pts=[(lm[i].x,lm[i].y) for i in idx]
    A=np.linalg.norm(np.array(pts[1])-np.array(pts[5]))
    B=np.linalg.norm(np.array(pts[2])-np.array(pts[4]))
    C=np.linalg.norm(np.array(pts[0])-np.array(pts[3]))
    return (A+B)/(2.0*C+1e-6)

def _compute(frame):
    rgb=cv2.cvtColor(frame,cv2.COLOR_BGR2RGB)
    with mp.solutions.face_mesh.FaceMesh(static_image_mode=False,max_num_faces=1,refine_landmarks=True,min_detection_confidence=0.5) as fm:
        r=fm.process(rgb)
    if not r.multi_face_landmarks: return 0.1
    lm=r.multi_face_landmarks[0].landmark
    ear=(_ear(lm,LEFT_EYE)+_ear(lm,RIGHT_EYE))/2
    eye=min(1.0,max(0.0,(ear-0.15)/0.20))
    dev=(abs(np.mean([lm[i].x for i in LEFT_IRIS])-np.mean([lm[i].x for i in LEFT_EYE]))+
         abs(np.mean([lm[i].x for i in RIGHT_IRIS])-np.mean([lm[i].x for i in RIGHT_EYE])))
    gaze=min(1.0,max(0.0,1.0-dev*20.0))
    smile=min(1.0,max(0.0,(abs(lm[291].x-lm[61].x)/(abs(lm[14].y-lm[13].y)+1e-6)-2.0)/8.0))
    return round(0.40*eye+0.35*gaze+0.25*smile,3)

def _run():
    global _latest_score,_running
    cap=cv2.VideoCapture(0)
    if not cap.isOpened(): print("[Webcam] Cannot open camera"); _running=False; return
    print("[Webcam] Camera started",flush=True)
    while _running:
        ret,frame=cap.read()
        if ret:
            try:
                s=_compute(frame)
                with _lock: _latest_score=s
                print(f"[Webcam] video_score={s}",flush=True)
            except Exception as e: logger.error(f"[Webcam] {e}")
        time.sleep(3)
    cap.release()

def start():
    global _running,_thread
    if _running: return
    _running=True; _thread=threading.Thread(target=_run,daemon=True); _thread.start()

def stop():
    global _running; _running=False

def get_score() -> float:
    with _lock: return _latest_score