from setuptools import find_packages, setup


setup(
    name="brave-updater",
    version="1.1.0",
    description="Unofficial CLI to download and update Brave Browser from Brave-controlled release sources.",
    package_dir={"": "src"},
    packages=find_packages("src"),
    include_package_data=True,
    entry_points={
        "console_scripts": [
            "brave-updater=brave_updater.cli:main",
        ]
    },
)
