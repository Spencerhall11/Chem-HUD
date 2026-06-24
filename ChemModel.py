import torch
import torch.nn as nn

alphabet = "0123456789()abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ "
num_classes = len(alphabet)+1

class ChemModel(nn.Module):
    def __init__(self,num_classes):
        super(ChemModel,self).__init__()

        self.cnn = nn.Sequential(
            nn.Conv2d(3, 32, kernel_size=3, padding=1), nn.ReLU(), nn.MaxPool2d(2),
            nn.Conv2d(32, 64, kernel_size=3, padding=1), nn.ReLU(), nn.MaxPool2d(2),
            nn.Conv2d(64, 128, kernel_size=3, padding=1), nn.ReLU(),
            nn.Conv2d(128, 128, kernel_size=3, padding=1), nn.ReLU(), nn.MaxPool2d((2, 1))
        )

        self.rnn = nn.LSTM(512, 256, bidirectional=True, batch_first=False)

        self.fc = nn.Linear(512, num_classes)

    def forward(self, x):
        
        features = self.cnn(x) 

        
        b, c, h, w = features.size()
      
        features = features.view(b, c * h, w) 
        
        features = features.permute(2, 0, 1)

        
        out, _ = self.rnn(features)

       
        out = self.fc(out)
        
        return out.log_softmax(2)