from torch import nn
import torch
import torch.nn.functional as F
import math


class EmbedFFNN(nn.Module):
    """
        The EmbedFFNN model represents the superclass of all models,
        containing embedding layers to reduce the input dimensionality
    """
    def __init__(self, feature_dict, device, embedding_dim, enable_cuda):
        super(EmbedFFNN, self).__init__()

        # Embedding layers
        self.embedding_dim = embedding_dim
        self.embedding_layers = []
        for i in range(3, 36):
            self.embedding_layers.append(
                nn.Embedding(len(feature_dict[str(i)]), embedding_dim)
            )
        self.embedding_layers = nn.ModuleList(self.embedding_layers)

        if enable_cuda:
            for i in range(33):
                self.embedding_layers[i] = self.embedding_layers[i].to(device)

    def forward(self, x):
        raise NotImplementedError()


class SmallEmbedFFNN(EmbedFFNN):
    """
         The SmallEmbedFFNN model consist of the following layers
            - Embedding layers (embedding_dim)
            - Linear layer (35*embedding_dim -> 512)
            - Dropout layer (probability p)
            - ReLU layer
            - Linear layer (512 -> 256)
            - Dropout layer (probability p)
            - ReLU layer
            - Linear layer (256 -> 1)
            - Softmax layer
    """
    def __init__(self, feature_dict, device, embedding_dim, hidden_dim, enable_cuda, dropout, **kwargs):
        super(SmallEmbedFFNN, self).__init__(feature_dict, device, embedding_dim, enable_cuda)
        self.linear1 = nn.Linear(35 * embedding_dim, 512)
        self.linear2 = nn.Linear(512, 256)
        self.linear3 = nn.Linear(256, 1)
        self.relu = nn.ReLU()
        self.softmax = nn.Softmax(dim=1)
        self.dropout = dropout

    def forward(self, x, p=None):
        if p is None: p = self.dropout
        batch_dim, pool_size, _ = x.shape
        input = []
        for i in range(35):
            if i < 2:
                tensor = x[:, :, i].unsqueeze(2)
                tensor = tensor.repeat(1, 1, self.embedding_dim)
                input.append(tensor)
            else:
                tensor = self.embedding_layers[i-2](x[:, :, i].long())
                input.append(tensor)

        out = torch.cat(input, dim=2)
        out = F.dropout(self.linear1(out), p=p)
        out = self.relu(out)
        out = F.dropout(self.linear2(out), p=p)
        out = self.relu(out)
        out = self.linear3(out)

        return self.softmax(out)


class LargeEmbedFFNN(EmbedFFNN):
    """
          The LargeEmbedFFNN model consist of the following layers
             - Embedding layers (embedding_dim)
             - Linear layer (35*embedding_dim -> 2048)
             - Dropout layer (probability p)
             - ReLU layer
             - Linear layer (2048 -> 1024)
             - Dropout layer (probability p)
             - ReLU layer
             - Linear layer (1024 -> 256)
             - Dropout layer (probability p)
             - ReLU layer
             - Linear layer (256 -> 1)
             - Softmax layer
    """
    def __init__(self, feature_dict, device, embedding_dim, hidden_dim, enable_cuda, dropout, **kwargs):
        super(LargeEmbedFFNN, self).__init__(feature_dict, device, embedding_dim, enable_cuda)
        self.linear1 = nn.Linear(35 * embedding_dim, 2048)
        self.linear2 = nn.Linear(2048, 1024)
        self.linear3 = nn.Linear(1024, 256)
        self.linear4 = nn.Linear(256, 1)
        self.relu = nn.ReLU()
        self.softmax = nn.Softmax(dim=1)
        self.dropout = dropout

    def forward(self, x, p=None):
        if p is None: p = self.dropout
        batch_dim, pool_size, _ = x.shape
        input = []
        for i in range(35):
            if i < 2:
                tensor = x[:, :, i].unsqueeze(2)
                tensor = tensor.repeat(1, 1, self.embedding_dim)
                input.append(tensor)
            else:
                tensor = self.embedding_layers[i-2](x[:, :, i].long())
                input.append(tensor)

        out = torch.cat(input, dim=2)
        out = F.dropout(self.linear1(out), p=p)
        out = self.relu(out)
        out = F.dropout(self.linear2(out), p=p)
        out = self.relu(out)
        out = F.dropout(self.linear3(out), p=p)
        out = self.relu(out)
        out = self.linear4(out)

        return self.softmax(out)


class TinyEmbedFFNN(EmbedFFNN):
    """
         The TinyEmbedFFNN model consist of the following layers
            - Embedding layers (embedding_dim)
            - Linear layer (35*embedding_dim -> 256)
            - Dropout layer (probability p)
            - ReLU layer
            - Linear layer (256 -> 1)
            - Softmax layer
    """
    def __init__(self, feature_dict, device, embedding_dim, hidden_dim, enable_cuda, dropout, **kwargs):
        super(TinyEmbedFFNN, self).__init__(feature_dict, device, embedding_dim, enable_cuda)
        self.linear1 = nn.Linear(35 * embedding_dim, 256)
        self.linear2 = nn.Linear(256, 1)
        self.relu = nn.ReLU()
        self.softmax = nn.Softmax(dim=1)
        self.dropout = dropout 

    def forward(self, x, p=None):
        if p is None: p = self.dropout
        batch_dim, pool_size, _ = x.shape
        input = []
        for i in range(35):
            if i < 2:
                tensor = x[:, :, i].unsqueeze(2)
                tensor = tensor.repeat(1, 1, self.embedding_dim)
                input.append(tensor)
            else:
                tensor = self.embedding_layers[i-2](x[:, :, i].long())
                input.append(tensor)

        out = torch.cat(input, dim=2)
        out = F.dropout(self.linear1(out), p=p)
        out = self.relu(out)
        out = self.linear2(out)

        return self.softmax(out)


class SparseFFNN(nn.Module):
    """
         The SparseFFNN model consist of the following layers
            - Linear layer (n_features -> 32)
            - ReLU layer
            - Linear layer (32 -> 1)
            - Softmax layer
    """
    def __init__(self, n_features):
        super(SparseFFNN, self).__init__()

        self.linear1 = nn.Linear(n_features, 32, bias=True)
        self.linear2 = nn.Linear(32, 1, bias=True)
        self.relu = nn.ReLU()
        self.softmax = nn.Softmax(dim=1)

    def forward(self, feature_vector, p=None):
        out = self.linear1(feature_vector)
        out = self.relu(out)
        out = self.linear2(out)
        probability = self.softmax(out)

        return probability


class SparseLinear(nn.Module):
    """
         The SparseLinear model consist of the following layers
            - Linear layer (n_features -> 1)
            - Softmax layer
    """
    def __init__(self, n_features):
        super(SparseLinear, self).__init__()

        self.linear = nn.Linear(n_features, 1, bias=False)
        self.softmax = nn.Softmax(dim=1)

    def forward(self, feature_vector, p=None):
        score = self.linear(feature_vector)
        probability = self.softmax(score)

        return probability



class CrossLayer(nn.Module):
    """
         The CrossLayer is based on the paper:
         Deep & Cross Network for Ad Click Predictions by Wang et al. (2017), which explains this structure in detail.
    """
    def __init__(self, dim):
        super(CrossLayer, self).__init__()
        self.weight = nn.Linear(dim, 1, bias=False)
        self.bias = nn.Linear(dim, 1).bias

    def forward(self, x, x_0):
        correlated = self.weight(x)
        correlated.transpose(1, 2)
        x_0 = x_0.unsqueeze(3)
        correlated = torch.einsum('ijkl,ijl->ijk', (x_0, correlated))

        return correlated + self.bias + x

class CrossNetwork(EmbedFFNN):
    """
         The CrossNetwork model is based on the paper:
         Deep & Cross Network for Ad Click Predictions by Wang et al. (2017), which explains this structure in detail.
    """
    def __init__(self, feature_dict, device, embedding_dim, hidden_dim, enable_cuda, **kwargs):
        super(CrossNetwork, self).__init__(feature_dict, device, embedding_dim, enable_cuda)
        
        # Cross Network
        self.cross_layer1 = CrossLayer(embedding_dim*35)
        self.cross_layer2 = CrossLayer(embedding_dim*35)
        self.cross_layer3 = CrossLayer(embedding_dim*35)

        # Regular Deep Neural Network
        self.dnn_layer1 = nn.Linear(35 * embedding_dim, 1024)
        self.dnn_layer2 = nn.Linear(1024, 768)
        self.dnn_layer3 = nn.Linear(768, 512)
        self.relu = nn.ReLU()
        self.final_layer = nn.Linear(512 + embedding_dim*35, 1)
        self.softmax = nn.Softmax(dim=1)

    def forward(self, x):
        batch_dim, pool_size, _ = x.shape
        embedded = []
        for i in range(35):
            if i < 2:
                tensor = x[:, :, i].unsqueeze(2)
                tensor = tensor.repeat(1, 1, self.embedding_dim)
                embedded.append(tensor)
            else:
                tensor = self.embedding_layers[i-2](x[:, :, i].long())
                embedded.append(tensor)
        embedded = torch.cat(embedded, dim=2)
        x_0 = embedded
        x = self.cross_layer1(x_0, x_0)
        x = self.cross_layer2(x, x_0)
        x_cross = self.cross_layer3(x, x_0)
        
        x = self.relu(self.dnn_layer1(x_0))
        x = self.relu(self.dnn_layer2(x))
        x_dnn = self.relu(self.dnn_layer3(x))

        out = self.final_layer(torch.cat((x_cross, x_dnn), dim=2))

        return self.softmax(out)

