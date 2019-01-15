import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name='hffe',
    version='0.0.9',
    description='Implements high-frequency financial econometrics tools.',
    long_description=long_description,
    long_description_content_type="text/markdown",
    url='http://github.com/salompas/hffe',
    author='Guilherme Salome',
    author_email='guilhermesalome@gmail.com',
    license='MIT',
    packages=setuptools.find_packages(),
    zip_safe=False,
    classifiers=[
        "Programming Language :: Python :: 3.6",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
        "Operating System :: OS Independent",
        "Development Status :: 1 - Planning", ],
    install_requires=[
        "numpy >= 1.15.0",
        "pandas >= 0.23.0",
        "matplotlib >= 3.0.0",
    ],
)
