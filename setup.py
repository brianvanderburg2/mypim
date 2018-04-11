from setuptools import setup, find_packages()

setup(
    name='mrbavii_mypim',
    version='0.1',
    description='A simple web-based PIM',
    url='',
    author='Brian Allen Vanderburg II',
    license='MIT',
    packages=find_packages(),
    zip_safe=False,
    install_package_data=True,
    entry_points = {
        'console_scripts': [
            'mrbavii-mypim = mrbavii_mypim.main:main'
        ]
    }
)
