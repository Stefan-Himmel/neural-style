import torch
import torch.nn as nn

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

def conv_block(in_channels, out_channels, kernel_size, stride, activation, transpose=False):
    block = nn.Sequential()

    if transpose:
        block.add_module('DeConv', nn.ConvTranspose2d(in_channels, out_channels, kernel_size, stride, 1, output_padding=1))
    else:
        block.add_module('Conv', nn.Conv2d(in_channels, out_channels, kernel_size, stride, 1))

    block.add_module('Inst_norm', nn.InstanceNorm2d(out_channels))

    if activation == 'ReLU':
        block.add_module(activation, nn.ReLU(inplace=True))
    elif activation == 'Tanh':
        block.add_module(activation, nn.Tanh())

    return block

def res_block(in_channels, out_channels, kernel_size, stride):
    return nn.Sequential(
        conv_block(in_channels, out_channels, kernel_size, stride, 'ReLU'),
        conv_block(in_channels, out_channels, kernel_size, stride, '')
    )

class StylizationNetwork(nn.Module):
    """Custom Stylization network as specified by Huang section 3.1"""

    def __init__(self):
        super(StylizationNetwork, self).__init__()

        #  (in_channels, out_channels, kernel_size (filter), stride)
        self.conv_block_1 = conv_block(3, 16, 3, 1, 'ReLU')
        self.conv_block_2 = conv_block(16, 32, 3, 2, 'ReLU')
        self.conv_block_3 = conv_block(32, 48, 3, 2, 'ReLU')

        self.res_block_1 = res_block(48, 48, 3, 1)
        self.res_block_2 = res_block(48, 48, 3, 1)
        self.res_block_3 = res_block(48, 48, 3, 1)
        self.res_block_4 = res_block(48, 48, 3, 1)
        self.res_block_5 = res_block(48, 48, 3, 1)

        # 'deconvolutional blocks' are equivalent to transposed conv blocks
        # 0.5 stride in deconv translates to 2 stride in conv
        self.deconv_block_1 = conv_block(48, 32, 3, 2, 'ReLU', transpose=True)
        self.deconv_block_2 = conv_block(32, 16, 3, 2, 'ReLU', transpose=True)

        self.conv_block_4 = conv_block(16, 3, 3, 1, 'Tanh')

    def forward(self, content):
        conv1 = self.conv_block_1(content)
        conv2 = self.conv_block_2(conv1)
        conv3 = self.conv_block_3(conv2)
        res1 = self.res_block_1(conv3)
        res2 = self.res_block_2(res1)
        res3 = self.res_block_3(res2)
        res4 = self.res_block_4(res3)
        res5 = self.res_block_5(res4)
        deconv1 = self.deconv_block_1(res5)
        deconv2 = self.deconv_block_2(deconv1)
        conv4 = self.conv_block_4(deconv2)
        return conv4
