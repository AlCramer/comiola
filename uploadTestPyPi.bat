py setup.py sdist bdist_wheel
py -m twine upload -u __token__ -p pypi-AgENdGVzdC5weXBpLm9yZwIkZDYxMTM3Y2EtZTBhMC00Mjg3LWE5MTAtMGUzOWUwMTFjMzRlAAIleyJwZXJtaXNzaW9ucyI6ICJ1c2VyIiwgInZlcnNpb24iOiAxfQAABiAtLpgfjZlwapkmawjd4Ck3jYmcqkk2iVjvUOtKAhKMsQ --repository testpypi dist/*

