from setuptools import setup, find_packages

with open("requirements.txt") as f:
    install_requires = f.read().strip().split("\n")

setup(
    name="salon",  
    version="0.0.1",
    description="Salon Management App",
    author="ITQAN",
    author_email="info@itqan-kw.net",
    packages=find_packages(),
    zip_safe=False,
    include_package_data=True,
    install_requires=install_requires
)
