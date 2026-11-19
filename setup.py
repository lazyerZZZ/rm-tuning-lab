from setuptools import setup

setup(
    name="rm_tuning_lab",
    version="0.1.0",
    packages=["rm_tuning_lab"],
    data_files=[
        ("share/ament_index/resource_index/packages", ["resource/rm_tuning_lab"]),
        ("share/rm_tuning_lab", ["package.xml"]),
        ("share/rm_tuning_lab/launch", ["launch/lesson.launch.py"]),
    ],
    entry_points={"console_scripts": ["tuning_node = rm_tuning_lab.node:main"]},
)
