# author : wangcwangc
# time : 2021/11/25 9:59 AM
import setuptools

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

requirements = ['z3_solver >= 4.8.13.0']

setuptools.setup(
    name="smartPip",
    version="0.0.1",
    long_description=long_description,
    entry_points={
        'console_scripts': [
            'smartPip = deptree.smartPip:main',
        ],
    },
    package_dir={"": "src"},
    packages=setuptools.find_packages(where="src"),
    install_requires=requirements,
    include_package_data=True,
)
