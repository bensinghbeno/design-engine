import cv2
img = cv2.imread("/home/ben/Pictures/p1.jpg")  # or use any image
cv2.imshow("Test", img)
cv2.waitKey(0)
cv2.destroyAllWindows()

