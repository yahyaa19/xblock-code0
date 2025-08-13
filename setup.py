"""Setup for advanced-coding-xblock"""

import os
from setuptools import setup, find_packages

def package_data(pkg, roots):
    """Generic function to find package_data"""
    data = []
    for root in roots:
        for dirname, _, files in os.walk(os.path.join(pkg, root)):
            for fname in files:
                data.append(os.path.relpath(os.path.join(dirname, fname), pkg))
    return {pkg: data}

setup(
    name='advanced-coding-xblock',
    version='1.0.0',
    description='Advanced Coding Assessment XBlock with Monaco Editor and Judge0 Integration',
    long_description=open('README.md', encoding='utf-8').read() if os.path.exists('README.md') else '',
    long_description_content_type='text/markdown',
    author='Your Name',
    author_email='your.email@example.com',
    url='https://github.com/yourusername/advanced-coding-xblock',
    license='Apache 2.0',
    packages=find_packages(),
    include_package_data=True,
    zip_safe=False,
    keywords='openedx xblock coding assessment monaco judge0',
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Education',
        'License :: OSI Approved :: Apache Software License',
        'Natural Language :: English',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
    ],
    entry_points={
        'xblock.v1': [
            'advanced_coding = advanced_coding:AdvancedCodingXBlock',
        ]
    },
    package_data=package_data("advanced_coding", ["static", "templates"]),
    install_requires=[
        'XBlock>=1.0.0',
        'xblock-utils',
        'web-fragments',
        'requests>=2.25.0',
        'bleach>=3.0.0',
        'python-dateutil',
        'pytz',
        'jsonschema>=3.0.0',
        'markdown>=3.0.0',
        'pygments>=2.0.0',
    ],
    extras_require={
        'dev': [
            'pytest>=6.0.0',
            'pytest-cov>=2.0.0',
            'pytest-django>=4.0.0',
            'mock>=3.0.0',
            'factory-boy>=3.0.0',
            'freezegun>=1.0.0',
            'responses>=0.10.0',
        ]
    },
    python_requires='>=3.8',
)
