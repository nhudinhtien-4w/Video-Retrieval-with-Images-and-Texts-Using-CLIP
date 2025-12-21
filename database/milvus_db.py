from pymilvus import (
    connections,
    utility,
    FieldSchema,
    CollectionSchema,
    DataType,
    Collection,
)
import logging

logger = logging.getLogger(__name__)

class MilvusDB:
    def __init__(self, host='localhost', port='19530', collection_name="ir_video_search", dim=512):
        self.collection = None
        self.connect(host, port)
        self.collection_name = collection_name
        self.dim = dim

    def connect(self, host, port):
        try: 
            connections.connect("default", host=host, port=port)
            logger.info("Connected to Milvus at %s:%s", host, port)
        except Exception as e:
            logger.error("Failed to connect to Milvus: %s", e)
            raise
    def create_collection(self, recreate=False):
        if recreate and utility.has_collection(self.collection_name):
            utility.drop_collection(self.collection_name)
            logger.info("Dropped existing collection: %s", self.collection_name)

        if utility.has_collection(self.collection_name):
            self.collection = Collection(self.collection_name)
            return
        
        fields = [
            FieldSchema(name="id", dtype=DataType.INT64, is_primary=True, auto_id=False),
            FieldSchema(name="video_id", dtype=DataType.VARCHAR, max_length=216), # VD: L01_V001
            FieldSchema(name="frame_id", dtype=DataType.INT64),                  # VD: 105
            FieldSchema(name="path", dtype=DataType.VARCHAR, max_length=512),    # Full path
            FieldSchema(name="embedding", dtype=DataType.FLOAT_VECTOR, dim=self.dim)
        ]

        schema = CollectionSchema(fields=fields, description="AIC Video Search Index")
        self.collection = Collection(name=self.collection_name, schema=schema)
        logger.info(f"Created collection: {self.collection_name}")

    def create_index(self):
        index_params = {
            "metric_type": "COSINE",
            "index_type": "HNSW",
            "params": {"M": 32, "efConstruction": 512}
        }
        self.collection.create_index(field_name="embedding", index_params=index_params)
        self.collection.load()
        logger.info(f"Created index on collection: {self.collection_name}")

    def insert_batch_data(self, data_batch):
        insert_data = [
            [x['id'] for x in data_batch],
            [x['video_id'] for x in data_batch],
            [x['frame_id'] for x in data_batch],
            [x['path'] for x in data_batch],
            [x['embedding'] for x in data_batch]
        ]
        self.collection.insert(insert_data)
        logger.info(f"Inserted batch of {len(data_batch)} items.")
