import math

from tensorflow.keras.datasets import mnist
import numpy as np

EPSILON = 0.001
class ANN:

    def initialize_parameters(self, layer_dims: list) -> dict:
        """
        Initializes random parameters for each layer in the model.
        :param layer_dims: List contains the shape of each layer, including input and output layer.
         For example, the cell number 1 represents the shape of the first hidden layer.
        :return: Dictionary contains parameters for each layer after initialization.
        """
        self.n_layers = len(layer_dims) - 1
        b = np.zeros(len(layer_dims))
        params = {}
        for i in range(1, len(layer_dims)):
            params[f'w{i}'] = np.random.randn(layer_dims[i], layer_dims[i - 1]) \
                              * np.sqrt(2 / layer_dims[i - 1])  # in order to help relu with convergence.
            params[f'b{i}'] = np.random.randn(layer_dims[i], 1)
        return params

    def linear_forward(self, A, W, b):
        """
        Description: Implement the linear part of a layer's forward propagation.

        input:
            A – the activations of the previous layer
            W – the weight matrix of the current layer (of shape [size of current layer, size of previous layer])
            B – the bias vector of the current layer (of shape [size of current layer, 1])

        Output:
            Z – the linear component of the activation function (i.e., the value before applying the non-linear function)
            linear_cache – a dictionary containing A, W, b (stored for making the backpropagation easier to compute)

        """
        # Dot product result in output vector than add biases
        Z = np.dot(W, A) + b
        linear_cache = {'A': A, 'W': W, 'b': b}
        return Z, linear_cache

    def softmax(self, Z):
        """
        Input:
            Z – the linear component of the activation function

        Output:
            A – the activations of the layer
            activation_cache – returns Z, which will be useful for the backpropagation
        """
        Z = Z - np.max(Z, axis=0)
        exp_z = np.exp(Z)
        return exp_z / np.sum(exp_z, axis=0), Z

    def relu(self, Z):
        """
        Input:
            Z – the linear component of the activation function

        Output:
            A – the activations of the layer
            activation_cache – returns Z, which will be useful for the backpropagation
        """
        activation_cache = Z
        relu_func = np.vectorize(lambda x: x if x > 0 else 0)
        return relu_func(Z), activation_cache

    def linear_activation_forward(self, A_prev, W, B, activation):
        """
        Description:
        Implement the forward propagation for the LINEAR->ACTIVATION layer

        Input:
            A_prev – activations of the previous layer
            W – the weights' matrix of the current layer
            B – the bias vector of the current layer
            Activation – the activation function to be used (a string, either “softmax” or “relu”)

        Output:
            A – the activations of the current layer
            cache – a joint dictionary containing both linear_cache and activation_cache

        """
        Z, linear_cache = self.linear_forward(A_prev, W, B)
        if activation == 'relu':
            Z, activation_cache = self.relu(Z)
        else:  # softmax
            Z, activation_cache = self.softmax(Z)
        linear_cache['Z'] = activation_cache
        return Z, linear_cache

    def L_model_forward(self, X, parameters, use_batchnorm=False):
        """
        Description:
            Implement forward propagation for the [LINEAR->RELU]*(L-1)->LINEAR->SOFTMAX computation

        Input:
            X – the data, numpy array of shape (input size, number of examples)
            parameters – the initialized W and b parameters of each layer
            use_batchnorm - a boolean flag used to determine whether to apply batchnorm after the activation (note that this option needs to be set to “false” in Section 3 and “true” in Section 4).

        Output:
            AL – the last post-activation value
            caches – a list of all the cache objects generated by the linear_forward function

        """
        A_prev = X
        cache = []
        for layer_index in range(1, self.n_layers):
            w_i = parameters[f'w{layer_index}']
            b_i = parameters[f'b{layer_index}']
            A_prev, cache_i = self.linear_activation_forward(A_prev, w_i, b_i, 'relu')
            cache.append(cache_i)
        # output layer wasn't part of the main loop
        w_output = parameters[f'w{self.n_layers}']
        b_output = parameters[f'b{self.n_layers}']
        z_output, cache_output = self.linear_activation_forward(A_prev, w_output, b_output, 'softmax')
        cache.append(cache_output)
        return z_output, cache

    def compute_cost(self, AL, Y):
        """
        Description:
            Implement the cost function defined by equation. The requested cost function is categorical cross-entropy loss. The formula is as follows :
            cost=-1/m*∑_1^m▒∑_1^C▒〖y_i  log⁡〖(y ̂)〗 〗, where y_i is one for the true class (“ground-truth”) and y ̂ is the softmax-adjusted prediction (this link provides a good overview).

        Input:
            AL – probability vector corresponding to your label predictions, shape (num_of_classes, number of examples)
            Y – the labels vector (i.e. the ground truth)

        Output:
            cost – the cross-entropy cost
        """
        y_pred = np.log(AL[Y > 0])
        cost = -(y_pred * Y).sum() * (1 / AL.shape[1])
        return cost

    def apply_batchnorm(self, A):
        """
        Description:
            performs batchnorm on the received activation values of a given layer.

        Input:
            A - the activation values of a given layer

        output:
            NA - the normalized activation values, based on the formula learned in class

        """
        mu = A.mean(1)
        sigma = ((A.T - mu).T ** 2).mean(1)
        z_i = ((A.T - mu) / np.sqrt(sigma + np.finfo(float).eps)).T
        return z_i

    def linear_backward(self, dZ, cache):
        """
        description:
                Implements the linear part of the backward propagation process for a single layer

        Input:
            dZ – the gradient of the cost with respect to the linear output of the current layer (layer l)
            cache – tuple of values (A_prev, W, b) coming from the forward propagation in the current layer

        Output:
            dA_prev -- Gradient of the cost with respect to the activation (of the previous layer l-1), same shape as A_prev
            dW -- Gradient of the cost with respect to W (current layer l), same shape as W
            db -- Gradient of the cost with respect to b (current layer l), same shape as b
        """
        m = cache['A'].shape[1]
        dW = (1 / m) * np.dot(dZ, cache['A'].T)  # A[i-1]
        db = (1 / m) * dZ.sum(1)
        dA_prev = np.dot(cache['W'].T, dZ)
        return dA_prev, dW, db

    def relu_backward(self, dA, activation_cache):
        """
        Description:
            Implements backward propagation for a ReLU unit

        Input:
            dA – the post-activation gradient
            activation_cache – contains Z (stored during the forward propagation)

        Output:
            dZ – gradient of the cost with respect to Z

        """
        Z = activation_cache['Z']
        d_relu = np.vectorize(lambda x: 1 if x > 0 else 0)
        dZ = d_relu(Z)
        return dA * dZ

    def softmax_backward(self, dA, activation_cache):
        """
        Description:
            Implements backward propagation for a softmax unit

        Input:
            dA – the post-activation gradient
            activation_cache – contains Z (stored during the forward propagation)

        Output:
            dZ – gradient of the cost with respect to Z
        """
        Z = activation_cache['Z']
        Y = activation_cache['Y']
        A, _ = self.softmax(Z)
        return A - Y  # L_model_backward sends AL which is enough for AL - Y but we created A from Z

    def linear_activation_backward(self, dA, cache, activation):
        """
        Description: linear_activation_backward is the function that computes the activation backward propagation
         for a single layer (layer l)
        :param dA:
        :param cache:
        :param activation:
        :return: the gradient of the cost with respect to the activation of the current layer
        """
        if activation == 'relu':
            dZ = self.relu_backward(dA, cache)
        else:  # softmax
            dZ = self.softmax_backward(dA, cache)
        return self.linear_backward(dZ, cache)

    def L_model_backward(self, AL, Y, caches):
        """
        Description:
            Implement the backward propagation process for the entire network.

        Some comments:
            the backpropagation for the softmax function should be done only once as only the output layers uses it and the RELU should be done iteratively over all the remaining layers of the network.

        Input:
            AL - the probabilities vector, the output of the forward propagation (L_model_forward)
            Y - the true labels vector (the "ground truth" - true classifications)
            Caches - list of caches containing for each layer: a) the linear cache; b) the activation cache

        Output:
            Grads - a dictionary with the gradients
                         grads["dA" + str(l)] = ...
                         grads["dW" + str(l)] = ...
                         grads["db" + str(l)] = ...

        """
        index = self.n_layers - 1
        grads = {}
        caches[index]['Y'] = Y
        cache = caches[index]
        dA_prev, dW, db = self.linear_activation_backward(AL, cache, 'softmax')
        grads[f'dA{self.n_layers}'] = dA_prev
        grads[f'dW{self.n_layers}'] = dW
        grads[f'db{self.n_layers}'] = db
        for i in range(1, index + 1):
            cache = caches[index - i]
            dA_prev, dW, db = self.linear_activation_backward(dA_prev, cache, 'relu')
            grads[f'dA{self.n_layers - i}'] = dA_prev
            grads[f'dW{self.n_layers - i}'] = dW
            grads[f'db{self.n_layers - i}'] = db
        return grads

    def update_parameters(self, parameters, grads, learning_rate):
        """
        Description:
            Updates parameters using gradient descent

        Input:
            parameters – a python dictionary containing the DNN architecture’s parameters
            grads – a python dictionary containing the gradients (generated by L_model_backward)
            learning_rate – the learning rate used to update the parameters (the “alpha”)

        Output:
           parameters – the updated values of the parameters object provided as input

        """
        layers_dim = int(len(parameters) / 2)
        for layer in range(1, layers_dim + 1):
            parameters[f'w{layer}'] -= learning_rate * grads[f'dW{layer}']
            parameters[f'b{layer}'] -= learning_rate * grads[f'db{layer}'].reshape(-1, 1)
        return parameters

    def L_layer_model(self, X, Y, layers_dims, learning_rate, num_iterations, batch_size):
        """
        Description:
            Implements a L-layer neural network. All layers but the last should have the ReLU activation function,
            and the final layer will apply the softmax activation function.
            The size of the output layer should be equal to the number of labels in the data.
             Please select a batch size that enables your code to run well (i.e. no memory overflows while still running relatively fast).
        Input:
            X – the input data, a numpy array of shape (height*width , number_of_examples)
            Comment: since the input is in grayscale we only have height and width, otherwise it would have been height*width*3
            Y – the “real” labels of the data, a vector of shape (num_of_classes, number of examples)
            Layer_dims – a list containing the dimensions of each layer, including the input
            batch_size – the number of examples in a single training batch.

        Output:
            parameters – the parameters learnt by the system during the training (the same parameters that were updated in the update_parameters function).
            costs – the values of the cost function (calculated by the compute_cost function). One value is to be saved after each 100 training iterations (e.g. 3000 iterations -> 30 values).

        """
        prev_val_acc = np.inf
        converged = False
        num_classes = len(np.unique(Y))
        training_step = 0
        ind = np.arange(X.shape[1])
        np.random.shuffle(ind)
        X_validation = X[:, ind[:int(np.ceil(0.2 * X.shape[1]))]]
        Y_validation = Y[:, ind[:int(np.ceil(0.2 * X.shape[1]))]]

        X_train = X[:, ind[int(np.ceil(0.2 * X.shape[1])):]]
        Y_train = Y[:, ind[int(np.ceil(0.2 * X.shape[1])):]]

        params = self.initialize_parameters(layers_dims)
        history = []
        accuracy_history = []
        for epoch in range(num_iterations):
            if converged:
                print(f"Converged at epoch {epoch} out of {num_iterations}")
                self.print_overall_accuracy(params,X_validation=X_validation, Y_validation=Y_validation,
                                            X_train=X_train, Y_train=Y_train)
                break
            for index in range(0, X_train.shape[1], batch_size):
                batch_x = X_train[:, index:min(index + batch_size, X_train.shape[1])]
                batch_y = Y_train[:, index:min(index + batch_size, Y_train.shape[1])]
                z_output, cache = self.L_model_forward(batch_x, params, False)
                if (index / 500) % 100 == 0:
                    acc = self.predict(X_validation, Y_validation, params)
                    cost = self.compute_cost(z_output, batch_y)
                    if np.absolute((prev_val_acc - acc)) < EPSILON:
                        converged = True
                        break
                    prev_val_acc = acc

                    history.append(cost)
                    accuracy_history.append(acc)
                    print(f"{training_step} Training Step - Accuracy = {acc}, cost = {cost}")
                    training_step += 1
                grads = self.L_model_backward(z_output, batch_y, cache)
                params = self.update_parameters(params, grads, learning_rate)
        return params, history

    def predict(self, X, Y, parameters):
        """
        Description:
            The function receives an input data and the true labels and calculates the accuracy of the trained neural network on the data.

        Input:
            X – the input data, a numpy array of shape (height*width, number_of_examples)
            Y – the “real” labels of the data, a vector of shape (num_of_classes, number of examples)
            Parameters – a python dictionary containing the DNN architecture’s parameters

        Output:
            accuracy – the accuracy measure of the neural net on the provided data (i.e. the percentage of the samples for which the correct label receives the hughest confidence score). Use the softmax function to normalize the output values.

        """
        y_preds, cache = self.L_model_forward(X, parameters, False)
        a = np.argmax(y_preds, axis=0)
        y = np.argmax(Y, axis=0)
        acc = np.sum(np.equal(y, a)) / len(y)
        return acc

    def print_overall_accuracy(self,params, **kwargs):
        """
        Description: The function receives the parameters of the trained neural network and the validation data and prints the accuracy of the trained neural network on the validation data.
        :param params:
        :param kwargs:
        :return:
        """
        if 'X_train' in kwargs and 'Y_train' in kwargs:
            X_train = kwargs['X_train']
            Y_train = kwargs['Y_train']
            print(f"Training accuracy: {self.predict(X_train, Y_train, params)}")
        if 'X_validation' in kwargs and 'Y_validation' in kwargs:
            X_validation = kwargs['X_validation']
            Y_validation = kwargs['Y_validation']
            print(f"Validation accuracy: {self.predict(X_validation, Y_validation, params)}")
        if 'X_test' in kwargs and 'Y_test' in kwargs:
            X_test = kwargs['X_test']
            Y_test = kwargs['Y_test']
            print(f"Test accuracy: {self.predict(X_test, Y_test, params)}")


def convert_to_onehot_vector(Y):
    """
    Description: convert the labels to one hot vector
    :param Y: Vector of labels
    :return: Y_onehot: One hot vector of labels
    """
    Y_oneHot = np.zeros((10, len(Y)))
    Y_oneHot[Y, np.arange(len(Y))] = 1
    return Y_oneHot


def load_data():
    """
    Loads the MNIST Dataset
    :return:  train_X, test_X, train_y, test_y
    """
    (train_X, train_y), (test_X, test_y) = mnist.load_data()
    train_X = train_X.reshape(train_X.shape[0], int(train_X.shape[1] * train_X.shape[2])).T / 255
    test_X = test_X.reshape(test_X.shape[0], int(test_X.shape[1] * test_X.shape[2])).T / 255
    train_y = convert_to_onehot_vector(train_y)
    test_y = convert_to_onehot_vector(test_y)
    return train_X, test_X, train_y, test_y


net = ANN()
train_X, test_X, train_y, test_y = load_data()
print(train_X.shape)
params, history = net.L_layer_model(X=train_X, Y=train_y, layers_dims=[784, 20, 7, 5, 10], learning_rate=0.009,
                                    num_iterations=30, batch_size=128)
print(history)
print(net.print_overall_accuracy(params, X_test=test_X, Y_test=test_y))
