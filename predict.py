import torch
import torch.nn as nn
from PIL import Image
import torchvision.transforms as T
import os
from ChemModel import ChemModel, alphabet, num_classes


device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
model = ChemModel(num_classes).to(device)


checkpoint_path = "latest_checkpoint.pth"
if os.path.exists(checkpoint_path):
    checkpoint = torch.load(checkpoint_path, map_location=device)
    
    model.load_state_dict(checkpoint['model_state'])
    print(f"Successfully loaded model from epoch {checkpoint['epoch']}")
else:
    print(f"Error: {checkpoint_path} not found!")

model.eval()


int_to_char = {i + 1: char for i, char in enumerate(alphabet)}

def predict_formula(image_path):

    img = Image.open(image_path).convert('RGB')
    transform = T.Compose([
        T.Resize((32, 128)),
        T.ToTensor(),
    ])
    
    img_tensor = transform(img).unsqueeze(0).to(device)

    with torch.no_grad():
        preds = model(img_tensor) 

    arg_maxes = torch.argmax(preds, dim=2).squeeze(1)
    
    
    decoded_chars = []
    for i in range(len(arg_maxes)):
        char_idx = arg_maxes[i].item()
        if char_idx != 0: # 0 is the CTC blank
            if i == 0 or char_idx != arg_maxes[i-1].item():
                decoded_chars.append(int_to_char[char_idx])
    
    return "".join(decoded_chars)

sample_img = "TrainingData/chem_0.png"
if os.path.exists(sample_img):
    result = predict_formula(sample_img)
    print(f"\nImage: {sample_img}")
    print(f"Predicted Formula: {result}")
else:
    print(f"Sample image {sample_img} not found.")



print("\n--- Running Inference Test ---")
for i in range(5):
    test_path = f"TrainingData/chem_{i}.png"
    if os.path.exists(test_path):
        result = predict_formula(test_path)
        print(f"Image: chem_{i}.png | Predicted: {result}")