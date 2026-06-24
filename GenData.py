import os
import random
from PIL import Image, ImageDraw, ImageFont

DATASET_PATH = "E:\\ChemHUD\\TrainingData"
elements = ["H", "He", "Li", "Be", "B", "C", "N", "O", "F", "Ne", "Na", "Mg", "Al", "Si", "P", "S", "Cl"]

def generate_advanced_formula():
    """Generates realistic formulas including polyatomic groups."""
    num_elements = random.randint(1, 3)
    formula = ""
    
    # 25% chance for a polyatomic group like (OH)2
    if random.random() < 0.25:
        sub_elements = random.randint(1, 2)
        group = "".join([f"{random.choice(elements)}{random.randint(1, 4) if random.random() > 0.5 else ''}" for _ in range(sub_elements)])
        formula = f"({group}){random.randint(2, 4)}"
    else:
        for _ in range(num_elements):
            el = random.choice(elements)
            count = random.randint(1, 10)
            formula += f"{el}{count if count > 1 else ''}"
    return formula

def create_training_image(text, filename):
    # Dark HUD-style background (0-50 range)
    bg_color = (random.randint(10, 40),) * 3 
    img = Image.new('RGB', (300, 300), color=bg_color)
    d = ImageDraw.Draw(img)
    
    try:
        # Using Consolas because it's standard for tech/HUDs
        font = ImageFont.truetype("C:\\Windows\\Fonts\\consola.ttf", 45)
    except:
        font = ImageFont.load_default()

    # Random HUD colors: Cyan, Lime, or White
    text_color = random.choice([(0, 255, 255), (0, 255, 0), (255, 255, 255)])
    
    # Random jitter so the model doesn't just learn a single pixel position
    pos = (50 + random.randint(-15, 15), 130 + random.randint(-15, 15))
    
    d.text(pos, text, fill=text_color, font=font)
    img.save(os.path.join(DATASET_PATH, filename))

# Create directory
if not os.path.exists(DATASET_PATH):
    os.makedirs(DATASET_PATH)

print(f"Generating 50,000 samples to {DATASET_PATH}...")
with open(os.path.join(DATASET_PATH, "labels.txt"), "w") as f_label:
    for i in range(50000):
        formula = generate_advanced_formula()
        fname = f"chem_{i}.png"
        create_training_image(formula, fname)
        f_label.write(f"{fname}\t{formula}\n")
        
        if i % 1000 == 0:
            print(f"Progress: {i}/50000")