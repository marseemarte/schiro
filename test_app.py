"""
Tests básicos para GATTO
Uso: pytest test_app.py -v
"""
try:
    import pytest
except Exception:
    # Minimal shim so editors/linters don't error out when pytest isn't installed.
    class _PytestShim:
        def fixture(self, *args, **kwargs):
            def decorator(f):
                return f
            return decorator
        def main(self, args=None):
            return None
    pytest = _PytestShim()
import json
from app import app

@pytest.fixture
def client():
    """Crea un cliente de test"""
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

def test_home_page(client):
    """Verifica que la página de inicio carga"""
    response = client.get('/')
    assert response.status_code == 200
    assert b'GATTO' in response.data

def test_buscar_vacio(client):
    """Verifica que una búsqueda vacía redirija"""
    response = client.post('/buscar', data={'duda': ''})
    assert response.status_code == 302  # Redirect

def test_buscar_muy_corta(client):
    """Verifica que una búsqueda muy corta redirija"""
    response = client.post('/buscar', data={'duda': 'ab'})
    assert response.status_code == 302  # Redirect

def test_buscar_muy_larga(client):
    """Verifica que una búsqueda muy larga redirija"""
    duda = 'a' * 501
    response = client.post('/buscar', data={'duda': duda})
    assert response.status_code == 302  # Redirect

def test_test_page_default(client):
    """Verifica que la página de test carga con valores por defecto"""
    response = client.get('/test')
    assert response.status_code == 200

def test_test_page_materia(client):
    """Verifica que se puede acceder a diferentes materias"""
    for materia in ['Inglés', 'PDL', 'Cs. Naturales']:
        response = client.get(f'/test?materia={materia}')
        assert response.status_code == 200
def test_test_page_nivel(client):
    """Verifica que se puede acceder a diferentes niveles"""
    for nivel in ['facil', 'intermedio', 'desafiante']:
        response = client.get(f'/test?nivel={nivel}')
        assert response.status_code == 200

if __name__ == '__main__':
    pytest.main([__file__, '-v'])
