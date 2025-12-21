MODEL_CONFIGS = {
    # --- ID 1: bigG-14 LAION ---
    1: {
        "enabled": False,
        "name": "bigG-14-LAION",
        "type": "open_clip",
        "model_key": "hf-hub:laion/CLIP-ViT-bigG-14-laion2B-39B-b160k",
        "bin_path": "data/bin/bigg14_laion.bin",
        "json_path": "data/index/path_index_clip.json"
    },

    # --- ID 2: bigG-14 DataComp ---
    2: {
        "enabled": False,
        "name": "bigG-14-DataComp",
        "type": "open_clip",
        "model_key": "hf-hub:UCSC-VLAA/ViT-bigG-14-CLIPA-datacomp1B",
        "bin_path": "data/bin/bigg14_datacomp.bin",
        "json_path": "data/index/path_index_clip.json"
    },

    # --- ID 3: g-14 LAION ---
    3: {
        "enabled": False,
        "name": "g-14-LAION",
        "type": "open_clip",
        "model_key": "hf-hub:laion/CLIP-ViT-g-14-laion2B-s34B-b88K",
        "bin_path": "data/bin/g14_laion.bin",
        "json_path": "data/index/path_index_clip.json"
    },

    # --- ID 4: H-14 QuickGELU ---
    4: {
        "enabled": False,
        "name": "H-14-QuickGELU",
        "type": "open_clip",
        "model_key": "ViT-H-14-378-quickgelu",
        "bin_path": "data/bin/h14_quickgelu.bin",
        "json_path": "data/index/path_index_clip.json"
    },

    # --- ID 5: H-14 Apple ---
    5: {
        "enabled": False,
        "name": "H-14-Apple",
        "type": "open_clip",
        "model_key": "hf-hub:apple/DFN5B-CLIP-ViT-H-14-378",
        "bin_path": "data/bin/h14_apple.bin",
        "json_path": "data/index/path_index_clip.json"
    },

    # --- ID 6: ViT-L/14 (Model xịn) ---
    6: {
        "enabled": True,
        "name": "ViT-L/14",
        "type": "open_clip",
        "model_key": "ViT-L-14-336",
        "pretrained": "openai",
        "bin_path": "data/bin/l14.bin",
        "json_path": "data/index/path_index_clip.json"
    },

    # --- ID 7: ViT-B/32 (Nhẹ nhất - Default) ---
    7: {
        "enabled": False, # <--- Đang bật cái này để test
        "name": "ViT-B/32",
        "type": "openai",
        "model_key": "ViT-B/32",
        "bin_path": "data/bin/b32.bin",
        "json_path": "data/index/path_index_clip.json"
    }
}