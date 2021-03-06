import numpy as np
import cv2
import pandas as pd
df = pd.read_csv("points.csv")
cap = cv2.VideoCapture('slow.mp4')

# Changed the quality level here from .3 (having quality level of .3 using harris detector results in much less corners)
feature_params = dict( maxCorners = 100,
                       qualityLevel = 0.2,
                       minDistance = 7,
                       blockSize = 7,
                       useHarrisDetector = True)

lk_params = dict( winSize  = (15,15),
                  maxLevel = 2,
                  criteria = (cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, 10, 0.03))

color = np.random.randint(0,255,(100,3))

ret, old_frame = cap.read()
old_gray = cv2.cvtColor(old_frame, cv2.COLOR_BGR2GRAY)
p0 = cv2.goodFeaturesToTrack(old_gray, mask = None, **feature_params)

mask = np.zeros_like(old_frame)

index = 0

p0Copy = p0

for i in range(len(p0)):
    df[f'x{i + 1}'] = ''
    df[f'y{i + 1}'] = ''

indexesRemoved = []
while(1):
    try:
        ret,frame = cap.read()
        frame_gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    except:
        break
    # calculate optical flow using current frame and previous frame
    df.at[index, "t"] = index
    p1, st, err = cv2.calcOpticalFlowPyrLK(old_gray, frame_gray, p0, None, **lk_params)
    indexes = []
    for i in range(1, len(p1) + 1 + len(indexesRemoved)):
        if any(i == index for index in indexesRemoved):
            continue
        indexes.append([i])
    p1Copy = np.insert(p1, 0, [indexes], axis = 2)
    if len(p1Copy) != len(p0Copy):
        for i in range(0, len(p1Copy) + 1):
            if abs(np.take(p0Copy, 1, axis = 2)[i] - np.take(p1Copy, 1, axis = 2)[i]) > 7:
                indexesRemoved.append(int(np.take(p1Copy, 0, axis = 2)[i]))
                break
        p1Copy = p1
        indexes = []
        for i in range(1, len(p1) + 1 + len(indexesRemoved)):
            if any(i == index for index in indexesRemoved):
                continue
            indexes.append([i])
        p1Copy = np.insert(p1, 0, [indexes], axis = 2)
    p0Copy = p1Copy
    for i in range(len(p1Copy)):
        df.at[index, f'x{int(np.take(p1Copy, 0, axis = 2)[i])}'] = int(np.take(p1Copy, 1, axis = 2)[i])
        df.at[index, f'y{int(np.take(p1Copy, 0, axis = 2)[i])}'] = int(np.take(p1Copy, 2, axis = 2)[i])
    index += 1
    # Select good points
    # Putting try and except because once all of the corner points go out of the frame, then an error occurs here
    try:
        good_new = p1[st==1]
        good_old = p0[st==1]
    except:
        break
    # drawing the tracks
    for i,(new,old) in enumerate(zip(good_new,good_old)):
        a,b = new.ravel()
        c,d = old.ravel()
        mask = cv2.line(mask, (a,b),(c,d), color[i].tolist(), 2)
        frame = cv2.circle(frame,(a,b),5,color[i].tolist(),-1)
    img = cv2.add(frame,mask)

    cv2.imshow('frame',img)
    k = cv2.waitKey(30) & 0xff

    # Now update the previous frame and previous points
    old_gray = frame_gray.copy()
    p0 = good_new.reshape(-1,1,2)

cv2.destroyAllWindows()
cap.release()
df.to_csv("points.csv")