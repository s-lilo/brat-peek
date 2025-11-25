from setuptools import setup
from pathlib import Path


def read_reqs():
    p = Path(__file__).with_name('requirements.txt')
    if not p.exists():
        return []
    lines = [l.strip() for l in p.read_text(encoding='utf-8').splitlines()]
    reqs = [l for l in lines if l and not l.startswith('#')]
    # requirements.txt may include a header or fenced block; try to clean common artifacts
    reqs = [r for r in reqs if not r.startswith('```')]
    return reqs


HERE = Path(__file__).parent
readme = ''
if (HERE / 'README.md').exists():
    readme = (HERE / 'README.md').read_text(encoding='utf-8')

setup(
    name='brat-peek',
    version='0.1.0',
    description='Simple utilities to read/write brat standoff files (peek module)',
    long_description=readme,
    long_description_content_type='text/markdown',
    url='https://github.com/s-lilo/brat-peek',
    author='Salvador Lima López',
    license='MIT',
    py_modules=[
        'peek',
        'ann_structure',
        'rwsl',
        'metrics',
        'stats',
        'txt',
    ],
    install_requires=read_reqs(),
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
    ],
)
