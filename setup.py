from setuptools import setup, find_packages

setup(
    name="weather-cli",
    version="1.0.0",
    packages=find_packages(),
    install_requires=[
        'requests>=2.31.0',
        'pytz>=2023.3',
        'matplotlib>=3.7.1',
        'pandas>=2.0.0',
        'folium>=0.14.0',
        'branca>=0.6.0'
    ],
    entry_points={
        'console_scripts': [
            'weather-cli=app:main',
        ],
    },
    author="Ramandeep Singh",
    author_email="ramansingh.it42@gmail.com",
    description="A comprehensive command-line weather application with premium features",
    long_description=open('README.md').read(),
    long_description_content_type="text/markdown",
    keywords="weather, cli, forecast, maps, premium",
    url="https://github.com/r123singh/weather-cli",
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: End Users/Desktop",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
    ],
    python_requires=">=3.8",
)

if __name__ == "__main__":
    setup() 