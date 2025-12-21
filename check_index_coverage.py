"""Check how many vectors in each FAISS index"""
import faiss
from pathlib import Path

bin_files = list(Path("data/bin").glob("*.bin"))

print("="*70)
print("FAISS Index Analysis")
print("="*70)

total_frames = 546821  # Total webp frames in data/clip_frame

for bin_file in sorted(bin_files):
    try:
        index = faiss.read_index(str(bin_file))
        num_vectors = index.ntotal
        dimension = index.d
        file_size_mb = bin_file.stat().st_size / (1024**2)
        
        percentage = (num_vectors / total_frames) * 100
        
        print(f"\n{bin_file.name}:")
        print(f"  Vectors: {num_vectors:,}")
        print(f"  Dimension: {dimension}")
        print(f"  File size: {file_size_mb:.1f} MB")
        print(f"  Coverage: {percentage:.1f}% of {total_frames:,} frames")
        
        if num_vectors == total_frames:
            print(f"  ✅ FULL extraction (all frames)")
        elif num_vectors > total_frames * 0.9:
            print(f"  ⚠️  Almost full ({num_vectors - total_frames:,} difference)")
        else:
            print(f"  ⚠️  PARTIAL extraction ({total_frames - num_vectors:,} frames missing)")
            
    except Exception as e:
        print(f"\n{bin_file.name}: ❌ Error - {e}")

print("\n" + "="*70)
