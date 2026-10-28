import time
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from ml.clustering import cluster_products

t0 = time.time()
res = cluster_products(k=3, save_to_db=True)
t1 = time.time()
print(f"Clustering complete in {t1 - t0:.2f}s! Products: {len(res['scatter_points'])}, Silhouette: {res['silhouette_score']}")
