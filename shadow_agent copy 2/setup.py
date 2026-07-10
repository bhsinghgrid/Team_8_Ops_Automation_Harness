from setuptools import setup, find_packages

setup(
    name='shadow_agent_framework',
    version='0.1.0',
    packages=find_packages(where='src'),
    package_dir={'': 'src'},
    install_requires=[
        'langchain',
        'langchain-openai',
        'langchain-anthropic',
        'langchain-google-genai',
        'mlflow',
        'pytest',
        'pytest-asyncio',
        'ranx',
        'python-dotenv',
        'redis',
        'scipy',
        'pydantic',
    ],
)