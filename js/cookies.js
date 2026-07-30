/* Banner de consentimiento de cookies — Artroscopia.org */
(function(){
  var CLAVE = 'consentimiento-cookies';
  function elegir(valor){
    try{ localStorage.setItem(CLAVE, valor); }catch(e){}
    var b = document.getElementById('banner-cookies');
    if(b){ b.parentNode.removeChild(b); }
    if(valor === 'aceptadas'){
      window.cookiesAceptadas = true;
      document.dispatchEvent(new Event('cookies-aceptadas'));
    }
  }
  var previa = null;
  try{ previa = localStorage.getItem(CLAVE); }catch(e){}
  if(previa === 'aceptadas'){
    window.cookiesAceptadas = true;
    document.dispatchEvent(new Event('cookies-aceptadas'));
    return;
  }
  if(previa === 'rechazadas'){ return; }

  var banner = document.createElement('div');
  banner.id = 'banner-cookies';
  banner.setAttribute('role','dialog');
  banner.setAttribute('aria-label','Aviso de cookies');
  banner.innerHTML =
    '<div class="banner-cookies-texto">' +
    'Utilizamos cookies de analítica (Google Analytics) para entender cómo se usa la web, solo si las aceptas, además del almacenamiento técnico imprescindible para recordar tu elección. No cedemos tus datos a terceros con fines comerciales. ' +
    'Consulta la <a href="/politica-de-privacidad/">política de privacidad</a> y la <a href="/cookies/">política de cookies</a>.' +
    '</div>' +
    '<div class="banner-cookies-botones">' +
    '<button type="button" id="cookies-rechazar">Rechazar</button>' +
    '<button type="button" id="cookies-aceptar">Aceptar</button>' +
    '</div>';
  document.body.appendChild(banner);
  document.getElementById('cookies-aceptar').addEventListener('click', function(){ elegir('aceptadas'); });
  document.getElementById('cookies-rechazar').addEventListener('click', function(){ elegir('rechazadas'); });
})();
