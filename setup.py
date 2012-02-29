from setuptools import setup, find_packages

setup(
    name="hermes-chat",
    packages=find_packages(),
    version="0.1.0",
    author="Matt Long",
    license="BSD",
    author_email="matt@mattlong.org",
    url="https://github.com/mattlong/hermes",
    description="A simple python-based group chat server built on XMPP.",
    long_description="A simple python-based group chat server built on XMPP. Hermes lets you easily manage chatrooms for friends or colleagues.",
    install_requires=['xmpppy>=0.5.0rc1'],
    zip_safe=False,
    include_package_data=True,
    classifiers=[
        'Programming Language :: Python',
        'Programming Language :: Python :: 2',
        'Operating System :: Unix',
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'Intended Audience :: System Administrators',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ],
)
