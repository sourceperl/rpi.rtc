from setuptools import setup

setup(
    name='pyRPiRTC',
    version='0.0.2',
    license='MIT',
    url='https://github.com/sourceperl/rpi.rtc',
    platforms='any',
    py_modules=[
        'pyRPiRTC'
    ],
    scripts=[
        'scripts/ds1302_get_utc',
        'scripts/ds1302_set_utc'
    ]
)
