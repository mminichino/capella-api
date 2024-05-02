from setuptools import setup, find_packages
import libcapella
from pathlib import Path
this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text()

setup(
    name='libcapella',
    version=libcapella.__version__,
    packages=find_packages(exclude=['tests']),
    url='https://github.com/mminichino/libcapella',
    license='MIT License',
    author='Michael Minichino',
    python_requires='>=3.8',
    install_requires=[
        "attrs>=23.1.0",
        "restfull>=1.0.5"
    ],
    author_email='info@unix.us.com',
    description='Couchbase Capella API Utility',
    long_description=long_description,
    long_description_content_type='text/markdown',
    keywords=["couchbase", "capella", "api"],
    classifiers=[
          "Development Status :: 5 - Production/Stable",
          "License :: OSI Approved :: MIT License",
          "Intended Audience :: Developers",
          "Operating System :: OS Independent",
          "Programming Language :: Python",
          "Programming Language :: Python :: 3",
          "Topic :: Software Development :: Libraries",
          "Topic :: Software Development :: Libraries :: Python Modules"],
)
