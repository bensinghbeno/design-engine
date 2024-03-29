import numpy as np
import matplotlib.pyplot as plt

X = np.array(([3,5], [5,1], [10,2]), dtype=float)

y = np.array(([75], [82], [93]), dtype=float)


X = X/np.amax(X, axis=0)
y = y/100 #Max test score is 100


print X
print y


class Neural_Network(object):
    def __init__(self):
        #Define Hyperparameters
        self.inputLayerSize = 2
        self.outputLayerSize = 1
        self.hiddenLayerSize = 3

        #Weights (parameters)
        self.W1 = np.random.randn(self.inputLayerSize, self.hiddenLayerSize)
        self.W2 = np.random.randn(self.hiddenLayerSize, self.outputLayerSize)

    def forward(self, X):
        #Propagate inputs though network
        self.z2 = np.dot(X, self.W1)
        self.a2 = self.sigmoid(self.z2)
        self.z3 = np.dot(self.a2, self.W2)
        yHat = self.sigmoid(self.z3)
        return yHat

    def sigmoid(self, z):
        #Apply sigmoid activation function to scalar, vector, or matrix
        return 1/(1+np.exp(-z))


nn = Neural_Network()

yhat = nn.forward(X)
print("yhat : \n %s"%yhat)



