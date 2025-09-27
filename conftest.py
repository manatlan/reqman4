import os

def pytest_sessionstart(session):
    os.environ["USER"]="me"