etup(
        name='jstatutree',
        version='0.0.1',
        description='Tree structure classes for JStatute XML Document',
        long_description=readme,
        author='Kazuya Fujioka',
        author_email='fukknkaz@gmail.com',
        url='https://github.com/Arten013/jstatutree',
        license=license,
        packages=find_packages(exclude=('test',)),
        install_requires=['numpy', 'plyvel']
)
