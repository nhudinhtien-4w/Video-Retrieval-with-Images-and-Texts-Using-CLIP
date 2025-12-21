"""Script test load model L14"""
import torch
from configs import MODEL_CONFIGS
from utils.faiss_service import FaissService
from utils.query_processing import Translation

print("="*50)
print("TEST LOAD MODEL L14 (ID 6)")
print("="*50)

# Init translator
print("\n1. Init Translator...")
translator = Translation(from_lang='vi', to_lang='en', mode='google')

# Get L14 config
config = MODEL_CONFIGS[6]
print(f"\n2. Config:")
print(f"   - Name: {config['name']}")
print(f"   - Type: {config['type']}")
print(f"   - Model Key: {config['model_key']}")
print(f"   - Pretrained: {config.get('pretrained', 'None')}")
print(f"   - Bin Path: {config['bin_path']}")
print(f"   - JSON Path: {config['json_path']}")

# Try to load
print(f"\n3. Loading FaissService...")
try:
    service = FaissService(
        bin_path=config["bin_path"],
        json_path=config["json_path"],
        model_type=config["type"],
        model_name=config["model_key"],
        device="cuda" if torch.cuda.is_available() else "cpu",
        translator=translator,
        pretrained=config.get("pretrained")
    )
    print("✅ SUCCESS! Model loaded successfully.")
    print(f"   - Index size: {service.index.ntotal}")
    print(f"   - ID map size: {len(service.id_map)}")
    
    # Test search
    print("\n4. Testing text search...")
    results = service.text_search("a person walking", k=5)
    print(f"   - Found {len(results)} results")
    if results:
        print(f"   - Top result: {results[0]}")
        
except Exception as e:
    print(f"❌ FAILED: {e}")
    import traceback
    traceback.print_exc()
