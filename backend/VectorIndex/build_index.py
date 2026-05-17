"""
Script to build FAISS vector index from images stored in the database.

Usage:
    cd backend
    python VectorIndex/build_index.py

This script:
1. Connects to PostgreSQL database
2. Fetches all image records
3. Extracts 512-dim embeddings using the loaded SiameseMetricModel
4. Builds FAISS IndexFlatIP index
5. Saves index and ID mapping to VectorIndex/ directory
"""
import os
import sys
import asyncio
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from Databases.Database import engine, async_session_local
from Databases.Schema import ImagesTable
from NNModels.NeuralNetworkModel import ModelLoader, SiameseMetricModel
from NNModels.FeatureExtractor import FeatureExtractor
from VectorIndex.FAISSIndex import FAISSIndex


CHECKPOINT_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "../NNModels/PretrainedModels/final_model.pth"
)
BACKBONE_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "../../ForNNTrain/backbones/smiMIM_backbone_convnext_tiny_batch_24_final_correct.pth"
)
INDEX_DIR = os.path.dirname(os.path.abspath(__file__))


async def get_all_image_paths() -> list[tuple[int, str]]:
    """Fetch all (id, storage_path) pairs from the images table."""
    async with async_session_local() as session:
        query = select(ImagesTable.id, ImagesTable.storage_path)
        result = await session.execute(query)
        records = result.fetchall()
    return [(row[0], row[1]) for row in records]


async def build_index():
    print("=" * 60)
    print("Building FAISS Vector Index")
    print("=" * 60)

    checkpoint = os.path.normpath(CHECKPOINT_PATH)
    backbone = os.path.normpath(BACKBONE_PATH)

    if not os.path.exists(checkpoint):
        print(f"[ERROR] Checkpoint not found: {checkpoint}")
        sys.exit(1)

    print(f"\n[INFO ] Checkpoint: {checkpoint}")
    print(f"[INFO ] Backbone: {backbone}")

    model_loader = ModelLoader()
    model: SiameseMetricModel = model_loader.load(
        checkpoint_path=checkpoint,
        backbone_name="convnext_tiny",
        embedding_dim=512,
        backbone_path=backbone if os.path.exists(backbone) else None,
        device="cuda"
    )

    device = model_loader.get_device()

    extractor = FeatureExtractor()
    extractor.initialize(model=model, device=device, target_size=(224, 224))

    print("\n[INFO ] Fetching image records from database...")
    records = await get_all_image_paths()
    print(f"[INFO ] Found {len(records)} image records")

    if not records:
        print("[WARN ] No images in database. Index not built.")
        sys.exit(0)

    embeddings_list = []
    db_ids = []
    skipped = 0

    for idx, (db_id, storage_path) in enumerate(records):
        if idx % 50 == 0:
            print(f"[INFO ] Processing {idx + 1}/{len(records)}...")

        try:
            embedding = extractor.extract_from_path(storage_path)
            embeddings_list.append(embedding)
            db_ids.append(db_id)
        except Exception as e:
            print(f"[WARN ] Skipping image {db_id} ({storage_path}): {e}")
            skipped += 1

    if not embeddings_list:
        print("[ERROR ] No valid embeddings extracted. Index not built.")
        sys.exit(1)

    embeddings_array = np.array(embeddings_list, dtype=np.float32)
    print(f"\n[INFO ] Extracted {len(embeddings_array)} embeddings (skipped: {skipped})")
    print(f"[INFO ] Embedding shape: {embeddings_array.shape}")

    faiss_index = FAISSIndex()
    faiss_index.build(embeddings_array, db_ids)
    faiss_index.save(INDEX_DIR)

    print(f"\n{'=' * 60}")
    print("FAISS index built successfully!")
    print(f"  Vectors: {faiss_index.size()}")
    print(f"  Dimension: {faiss_index._dim}")
    print(f"  Saved to: {INDEX_DIR}")
    print(f"{'=' * 60}")


if __name__ == "__main__":
    asyncio.run(build_index())
