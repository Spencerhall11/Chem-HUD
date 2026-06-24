import mmap
import time
import torch
import torch.nn.functional as F
import numpy as np
import sys
import cv2
from ChemModel import ChemModel, alphabet, num_classes

#constants with C++ eye matching
BUFFER_NAME = "Global\\ChemHUD_FrameBuffer"
WIDTH, HEIGHT = 300, 300
CHANNELS = 4  # BGRA
BUFFER_SIZE = WIDTH * HEIGHT * CHANNELS


def decode_ctc(preds, int_to_char):
  
    arg_maxes = torch.argmax(preds, dim=2).squeeze(1)
    decode = []
    for i in range(len(arg_maxes)):
        idx = arg_maxes[i].item()
        if idx != 0: # Ignore blank
            if i == 0 or idx != arg_maxes[i-1].item():
                decode.append(int_to_char[idx])
    return "".join(decode)



def run_nerve():
    device = torch.device("cuda")
    
    
    model = ChemModel(num_classes).to(device)
    checkpoint = torch.load("latest_checkpoint.pth", map_location=device)
    model.load_state_dict(checkpoint['model_state'])
    model.eval()
    
    int_to_char = {i + 1: char for i, char in enumerate(alphabet)}
    last_formula = ""

    try:
        shm = mmap.mmap(-1, BUFFER_SIZE, tagname=BUFFER_NAME, access=mmap.ACCESS_READ)
        print("--- Nerve Connected to Eye ---", file=sys.stderr) # Use stderr for logs
    except FileNotFoundError:
        print("Error: Eye is not running.", file=sys.stderr)
        return

    try:
        while True:
            
            img_np = np.frombuffer(shm, dtype=np.uint8).reshape((HEIGHT, WIDTH, CHANNELS))

            view = cv2.cvtColor(img_np, cv2.COLOR_BGRA2BGR)
            cv2.imshow("Eye Feed", view)
            cv2.waitKey(1)
            
           
            frame_tensor = torch.from_numpy(img_np.copy()).to(device)
            
            img_rgb = frame_tensor[:, :, :3].flip(-1).permute(2, 0, 1).float() / 255.0
            input_batch = F.interpolate(img_rgb.unsqueeze(0), size=(32, 128))

           
            with torch.no_grad():
                preds = model(input_batch)
                formula = decode_ctc(preds, int_to_char)

            
            if formula and formula != last_formula:
                print(formula) 
                sys.stdout.flush() 
                last_formula = formula

            time.sleep(0.03) 

    except KeyboardInterrupt:
        shm.close()
        print("\nNerve detached.", file=sys.stderr)

if __name__ == "__main__":
    run_nerve()