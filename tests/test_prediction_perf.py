import time
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from ml.predictor import predict_price_for_product

t0 = time.time()
res = predict_price_for_product(1, save_to_db=True)
t1 = time.time()
print("Result keys:", list(res.keys()))
print("Result:", res)
