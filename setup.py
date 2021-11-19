""" Setup.py for packaging log-anomaly-detector as library """
from setuptools import setup, find_packages

long_description = "Log Anomaly Detection - Machine learning to detect abnormal events logs"


REQUIRED_PKG = [
    "Click",
    "elasticsearch5",
    "gensim==3.8.1",
    "matplotlib",
    "Cython==0.29.24",
    "numpy",
    "pandas",
    "prometheus_client",
    "Flask==1.0.4",
    "scikit-learn==1.0.1",
    "scipy",
    "tqdm",
    "SQLAlchemy",
    "PyMySQL",
    "pyyaml",
    "scikit-image",
    "sompy @ git+https://github.com/sevamoo/SOMPY.git",
    "boto3",
    "pyyaml",
    "numba",
    "kafka-python",
    "jaeger-client",
    "opentracing_instrumentation",
    "prometheus_flask_exporter",
    "gunicorn==19.9.0",
    "flask_sqlalchemy",
    "tornado==5.1.1",
    "pymongo==3.12.1",
]

setup(
    name="log-anomaly-detector",
    version="1.0.4",
    py_modules=['app'],
    packages=find_packages(),
    setup_requires=["pytest-runner"],
    tests_require=[
        "pytest",
        "pytest-sugar",
        "pytest-xdist"],
    zip_safe=False,
    classifiers=(
        "Development Status :: 1 - Planning",
        "Natural Language :: English",
        "Programming Language :: Python :: 3.8",
    ),
    python_requires=">3.5",
    url="https://github.com/AICoE/log-anomaly-detector",
    author="Zak Hassan",
    author_email="zak.hassan@redhat.com",
    description="Log anomaly detector for streaming logs",
    long_description=long_description,
    long_description_content_type="text/markdown",
    dependency_links=[
	"git+https://github.com/sevamoo/SOMPY.git",
    ],
    install_requires=REQUIRED_PKG,
    entry_points="""
        [console_scripts]
        log-anomaly-detector=app:cli
    """,
)
