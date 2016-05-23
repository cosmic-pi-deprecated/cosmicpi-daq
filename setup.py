from setuptools import setup, find_packages

setup(
    name="cosmicpi",
    version="0.0.1",
    author="Julian Lewis <lewis.julian@gmail.com>, Justin Lewis Salmon <justin.lewis.salmon@cern.ch>",
    description="Package for acquiring data from an Arduino via USB serial on a Raspberry Pi",
    license="GPLv2+",
    url="https://github.com/CosmicPi/cosmicpi-daq",
    packages=find_packages(),
    zip_safe=False,
    include_package_data=True,
    install_requires=['pika', 'netifaces', 'blessings', 'cliff'],
    entry_points={
        "console_scripts": {
            "cosmicpi = cosmicpi:main",
            "cosmicpi-cli = cosmicpi:cli"
        }
    }
)
