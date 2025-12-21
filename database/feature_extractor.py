import open_clip
import torch
import numpy as np
from PIL import Image

class FeatureExtractor:
    def __init__(self, model_name='ViT-B-32', pretrained='laion2b_s34b_b79k', device=None):
        self.device = device if device else ('cuda' if torch.cuda.is_available() else 'cpu')
        print(f"Loading model {model_name} on {self.device}...")
        
        self.model, _, self.preprocess = open_clip.create_model_and_transforms(model_name, pretrained=pretrained)
        self.model.to(self.device)
        self.model.eval()
        self.tokenizer = open_clip.get_tokenizer(model_name)

    def encode_image(self, image_path):
        """Chuyển ảnh thành vector"""
        try:
            image = self.preprocess(Image.open(image_path)).unsqueeze(0).to(self.device)
            with torch.no_grad():
                features = self.model.encode_image(image)
                # Quan trọng: Normalize để dùng Cosine Similarity (IP trong Milvus)
                features /= features.norm(dim=-1, keepdim=True)
            return features.cpu().numpy().flatten().tolist()
        except Exception as e:
            print(f"Error processing {image_path}: {e}")
            return None

    def encode_text(self, text):
        """Chuyển text thành vector"""
        with torch.no_grad():
            text_tokens = self.tokenizer([text]).to(self.device)
            features = self.model.encode_text(text_tokens)
            features /= features.norm(dim=-1, keepdim=True)
        return features.cpu().numpy().flatten().tolist()
    
    def get_dim(self):
        dummy_text = self.tokenizer(["test"]).to(self.device)
        with torch.no_grad():
            dim = self.model.encode_text(dummy_text).shape[-1]
        return dim