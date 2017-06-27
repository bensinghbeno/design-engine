from sklearn.datasets import load_digits
digits = load_digits()
import matplotlib.pyplot as plt 
plt.gray() 
plt.matshow(digits.images[7]) 
plt.show() 
