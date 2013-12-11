import os
import sys
if sys.version < (2, 6):
    from distutils.command import register

    def isstr((k, v)):
        return isinstance(v, basestring)

    def patch(func):
        def post_to_server(self, data, auth=None):
            for key, value in filter(isstr, data.items()):
                data[key] = value.decode('utf8')
            return func(self, data, auth)
        return post_to_server

    register.register.post_to_server = patch(register.register.post_to_server)

from setuptools import setup
import pithosfuse

def read(*rnames):
    return open(os.path.join(os.path.dirname(__file__), *rnames)).read()


setup(name='pithosfuse',
      version=pithosfuse.__version__,
      author='Chrysostomos Nanakos, Christos Stavrakakis',
      author_email='cnanakos@grnet.gr, cstavr@grnet.gr',
      description='Pithos+ filesystem using FUSE',
      long_description=read('README.md'),
      license='LGPL',
      keywords='fuse Pithos+ Pithos filesystem',
      platforms=['posix'],
      packages=['pithosfuse'],
      install_requires=['fusepy', 'kamaki'],
      entry_points = {
          'console_scripts': [
              'pithosfuse = pithosfuse.pithosfuse:main'
          ],
      },
      classifiers=[
          'Development Status :: 1 - Beta',
          'Environment :: Console',
          'License :: OSI Approved :: GNU Library or Lesser General Public License (LGPL)',
          'Operating System :: POSIX',
          'Topic :: System :: Filesystems',
      ]
     )

