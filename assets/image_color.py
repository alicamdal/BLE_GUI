import cv2
import numpy as np


img = cv2.imread("triangle_resized.png")
hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)

gray_low = np.array([0,0,0])
gray_up = np.array([150,150,150])

mask = cv2.inRange(hsv, gray_low, gray_up)

img[mask > 0] = (0,255,0)

 
cv2.imwrite("triangle_green_up.png", img)
cv2.imshow("test", img)
cv2.waitKey(0)