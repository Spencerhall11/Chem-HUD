import torch
import torch.optim as optim
from torch.utils.data import Dataset, DataLoader
from PIL import Image
import os
import numpy as np
import torchvision.transforms as T
from ChemModel import ChemModel, alphabet, num_classes

class ChemDataset(Dataset):
    def __init__(self, root_dir, label_file):
        self.root_dir = root_dir
        with open(label_file, 'r') as f:
            self.labels = [line.strip().split('\t') for line in f]
        self.char_to_int = {char: i + 1 for i, char in enumerate(alphabet)}
        
        self.transform = T.Compose([
            T.Resize((32, 128)), 
            T.ToTensor(),
        ])

    def __len__(self):
        return len(self.labels)

    def __getitem__(self, idx):
        fname, formula = self.labels[idx]
        img = Image.open(os.path.join(self.root_dir, fname)).convert('RGB')
        
        # Apply the transform instead of manual numpy conversion
        img_tensor = self.transform(img)
        
        target = torch.tensor([self.char_to_int[c] for c in formula], dtype=torch.long)
        return img_tensor, target
    

def chem_collate_fn(batch):
    images, targets = zip(*batch)
    images = torch.stack(images, 0)
    return images, targets

def train(resume=True):
    device = torch.device("cuda")
    model = ChemModel(num_classes).to(device)
    optimizer = optim.Adam(model.parameters(), lr=0.0001)
    criterion = torch.nn.CTCLoss(blank=0)
    
    checkpoint_path = "latest_checkpoint.pth"
    start_epoch = 0

    if resume and os.path.exists(checkpoint_path):
        print(f"Loading checkpoint: {checkpoint_path}")
        checkpoint = torch.load(checkpoint_path)
        model.load_state_dict(checkpoint['model_state'])
        optimizer.load_state_dict(checkpoint['optimizer_state'])
        start_epoch = checkpoint['epoch'] + 1
        print(f"Resuming from Epoch {start_epoch}")

    dataset = ChemDataset("E:\\ChemHUD\\TrainingData", "E:\\ChemHUD\\TrainingData\\labels.txt")
    
    dataloader = DataLoader(
        dataset, 
        batch_size=32, 
        shuffle=True, 
        collate_fn=chem_collate_fn
    )

    model.train()

    try:
        for epoch in range(start_epoch, 20):
            print(f"\n--- Epoch {epoch} ---")
            for i, (images, targets) in enumerate(dataloader):
             
                images = images.to(device)
                
                preds = model(images) # [Time, Batch, Classes]

                steps, current_batch, _ = preds.shape

         
                input_lengths = torch.full(
                    (current_batch,), 
                    steps, 
                    dtype=torch.long, 
                    device='cpu'
                )
               
                target_lengths = torch.tensor(
                    [len(t) for t in targets[:current_batch]], 
                    dtype=torch.long, 
                    device='cpu'
                )
                
                targets_flat = torch.cat(targets[:current_batch]).to(device)

               
                if target_lengths.size(0) != current_batch:
                    continue

                loss = criterion(preds, targets_flat, input_lengths, target_lengths)

                optimizer.zero_grad()
                loss.backward()
                optimizer.step()

                if i % 10 == 0:
                    print(f"Batch {i} | Loss: {loss.item():.4f}          ", end='\r')

       
            print(f"\nEpoch {epoch} complete. Saving...")
            torch.save({
                'epoch': epoch,
                'model_state': model.state_dict(),
                'optimizer_state': optimizer.state_dict(),
            }, checkpoint_path)

    except KeyboardInterrupt:
        print("\nTraining manually stopped. You can resume later by running the script again.")

if __name__ == "__main__":
    train(resume=True)