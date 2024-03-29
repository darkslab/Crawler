from pathlib import Path

from setuptools import find_packages, setup

long_description: str = (Path(__file__).parent.resolve() / "README.md").read_text(
    encoding="utf-8"
)
setup(
    name="crawler",
    version="0.0.0",
    description="A Web Crawler",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/darkslab/Crawler",
    author="Darkhan Baimyrza",
    author_email="darkhan@baimyrza.com",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Build Tools",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3 :: Only",
        "Programming Language :: Python :: 3.8",
    ],
    keywords="crawler",
    package_dir={"": "src"},
    packages=find_packages(where="src"),
    python_requires=">=3.8, <4",
    install_requires=[
        "click==7.1.2",
        "aiohttp==3.8.1",
        "yarl==1.7.2",
    ],
    entry_points={
        "console_scripts": [
            "crawler=crawler:cli",
        ],
    },
)
