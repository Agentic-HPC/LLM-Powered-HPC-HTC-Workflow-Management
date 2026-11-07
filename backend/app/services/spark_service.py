"""
Real Apache Spark session management.

This replaces the earlier hand-rolled map/shuffle/reduce simulation with an
actual PySpark SparkSession. By default it runs in local mode
(`local[*]` - uses every core on the machine the backend runs on), which is
a genuine Spark execution engine, not a simulation - it has its own
catalyst optimizer, real task scheduling, and real (not fabricated) stage
timings.

To point this at a real multi-node Spark cluster instead of local mode,
set SPARK_MASTER_URL (e.g. spark://spark-master:7077) in .env - no code
changes needed, `get_spark_session()` reads it from settings.
"""
import atexit
import threading
from typing import Optional

try:
    from pyspark.sql import SparkSession
except ImportError:
    SparkSession = None

from app.core.config import settings

_spark_session: Optional[SparkSession] = None
_lock = threading.Lock()


def get_spark_session() -> SparkSession:
    """Lazily create (once) and return the shared SparkSession."""
    global _spark_session
    if SparkSession is None:
        raise RuntimeError("pyspark is not installed. Please install requirements.txt to run Spark jobs.")

    if _spark_session is not None:
        return _spark_session

    with _lock:
        if _spark_session is None:
            builder = (
                SparkSession.builder.appName("hpc-htc-ai-platform")
                .master(settings.SPARK_MASTER_URL)
                .config("spark.driver.memory", settings.SPARK_DRIVER_MEMORY)
                .config("spark.driver.bindAddress", "127.0.0.1")
                .config("spark.driver.host", "127.0.0.1")
                .config("spark.sql.shuffle.partitions", str(settings.SPARK_SHUFFLE_PARTITIONS))
                .config("spark.ui.showConsoleProgress", "false")
            )
            _spark_session = builder.getOrCreate()
            _spark_session.sparkContext.setLogLevel("WARN")
    return _spark_session


def stop_spark_session() -> None:
    global _spark_session
    if _spark_session is not None:
        _spark_session.stop()
        _spark_session = None


atexit.register(stop_spark_session)
