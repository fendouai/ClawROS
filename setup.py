from setuptools import setup, find_packages

package_name = 'clawros'

setup(
    name=package_name,
    version='0.1.0',
    packages=find_packages(where='src'),
    package_dir={'': 'src'},
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        ('share/' + package_name + '/config', ['config/clawros_config.yaml']),
        ('share/' + package_name + '/launch', ['src/launch/clawros_bridge.launch.py']),
    ],
    install_requires=[
        'setuptools',
        'pyyaml>=6.0',
        'pydantic>=2.0.0',
    ],
    zip_safe=True,
    maintainer='ClawROS Team',
    maintainer_email='clawros@example.com',
    description='ClawROS - Bridge between OpenClaw AI and ROS',
    license='MIT',
    tests_require=['pytest', 'pytest-cov', 'pytest-mock'],
    entry_points={
        'console_scripts': [
            'clawros_bridge_node = clawros_node:main',
        ],
    },
)
