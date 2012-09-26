from setuptools import setup, find_packages

from hermes import VERSION_STRING

setup(
    name="hermes",
    packages=find_packages(),
    version=VERSION_STRING,
    author="Matt Long",
    license="ISC",
    author_email="matt@mattlong.org",
    url="https://github.com/mattlong/hermes",
    description="Hermes is an extensible XMPP-based chatroom server written in Python.",
    #long_description="",
    install_requires=['xmpppy>=0.5.0rc1'],
    zip_safe=False,
    include_package_data=True,
    classifiers=[
        'Programming Language :: Python',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Operating System :: MacOS :: MacOS X',
        'Operating System :: Unix',
        'Operating System :: POSIX',
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'Intended Audience :: System Administrators',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'License :: OSI Approved :: ISC License (ISCL)',
    ],
)
