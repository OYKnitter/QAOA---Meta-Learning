import numpy as np
import torch

import netket as nk
from netket.layer import SumOutput
from netket.layer import FullyConnected
from netket.layer import Lncosh, Relu, Tanh
from netket.hilbert import Spin
from netket.graph import Hypercube
from netket.machine import FFNN
from netket.layer import ConvolutionalHypercube


def build_model_netket(cf, hilbert):
    if cf.model_name == "rbm":
        model = nk.machine.RbmSpin(alpha=cf.width, hilbert=hilbert)
    elif cf.model_name == "rbm_real":
        model = nk.machine.RbmSpinReal(alpha=cf.width, hilbert=hilbert)
    elif cf.model_name == "mlp":
        input_size = np.prod(cf.input_size)
        if cf.activation == "tanh":
            ACT = Tanh
        elif cf.activation == "relu":
            ACT = Relu
        else:
            raise("Specify activation function.")
        layers = []
        if cf.depth == 1:
            layers.append(FullyConnected(input_size=input_size,output_size=input_size,use_bias=True))
        elif cf.depth == 2:
            layers.append(FullyConnected(input_size=input_size,output_size=input_size*cf.width,use_bias=True))
            layers.append(ACT(input_size=input_size*cf.width))
            layers.append(FullyConnected(input_size=input_size*cf.width,output_size=input_size,use_bias=True))
        else:
            layers.append(FullyConnected(input_size=input_size,output_size=input_size*cf.width,use_bias=True))
            layers.append(ACT(input_size=input_size*cf.width))
            for layer in range(cf.depth-2):
                layers.append(FullyConnected(input_size=input_size*cf.width,output_size=input_size*cf.width,use_bias=True))
                layers.append(ACT(input_size=input_size*cf.width))
            layers.append(FullyConnected(input_size=input_size*cf.width,output_size=input_size,use_bias=True))
        layers.append(Lncosh(input_size=input_size))
        layers.append(SumOutput(input_size=input_size))
        layers = tuple(layers)
        model = FFNN(hilbert, layers)
    elif cf.model_name == "conv_net":
        input_size = cf.input_size
        dim = len(input_size)
        length = input_size[0]
        assert dim == 2
        assert input_size[0] == input_size[1]
        layers = (ConvolutionalHypercube(length=length, n_dim=dim, input_channels=1, output_channels=1, stride=1, kernel_length=3, use_bias=True),
                  FullyConnected(input_size=np.prod(input_size),output_size=np.prod(input_size),use_bias=True),
                  Lncosh(input_size=np.prod(input_size)),
                  SumOutput(input_size=np.prod(input_size)))
        model = FFNN(hilbert, layers)
    return model


def load_model(cf, model, loadpath):
    if cf.num_gpu<2:
        bad_state_dict = torch.load(loadpath,map_location='cpu')
        correct_state_dict = {re.sub(r'^module\.', '', k): v for k, v in
                                bad_state_dict.items()}
        model.load_state_dict(correct_state_dict)
    else:
        model.load_state_dict(torch.load(loadpath))
    model.eval()
    model.zero_grad()
    return model

