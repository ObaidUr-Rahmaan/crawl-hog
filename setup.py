from setuptools import setup, find_packages

# Read version from crawlhog/__init__.py
with open('crawlhog/__init__.py', 'r') as f:
    for line in f:
        if line.startswith('__version__'):
            version = line.split('=')[1].strip().strip('"\'')
            break

# Read README.md for long description
with open('README.md', 'r') as f:
    long_description = f.read()

setup(
    name='crawlhog',
    version=version,
    description='A robust documentation web scraper',
    long_description=long_description,
    long_description_content_type='text/markdown',
    author='Your Name',
    author_email='your.email@example.com',
    url='https://github.com/yourusername/crawlhog',
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        'click>=8.0.0',
        'firecrawl-py>=1.11.0',
        'python-dotenv>=1.0.0',
    ],
    entry_points={
        'console_scripts': [
            'chog=crawlhog.cli.main:cli',
        ],
    },
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Console',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.11',
        'Topic :: Documentation',
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
        'Topic :: Software Development :: Documentation',
    ],
    python_requires='>=3.11',
) 