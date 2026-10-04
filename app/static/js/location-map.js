/* خريطة Leaflet محلية: تعرض موقع المواطن وتتيح سحبه وتحديث الوصف تلقائيًا. */
(function () {
  'use strict';

  function initMap(options) {
    var containerId  = options.containerId;
    var latInputId   = options.latInputId;
    var lngInputId   = options.lngInputId;
    var descInputId  = options.descInputId;
    var gpsButtonId  = options.gpsButtonId;
    var statusId     = options.statusId;

    var container = document.getElementById(containerId);
    if (!container || typeof L === 'undefined') { return; }

    var defaultLat = 28.0339;   // الجزائر — مركز تقريبي
    var defaultLng = 1.6596;
    var defaultZoom = 5;

    var map = L.map(container, { zoomControl: true }).setView([defaultLat, defaultLng], defaultZoom);

    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      maxZoom: 19,
      attribution: '&copy; مساهمو OpenStreetMap'
    }).addTo(map);

    var marker = null;

    function setStatus(text) {
      var el = document.getElementById(statusId);
      if (el) { el.textContent = text || ''; }
    }

    function reverseGeocode(lat, lng) {
      var url = 'https://nominatim.openstreetmap.org/reverse?format=jsonv2&accept-language=ar&lat=' +
                encodeURIComponent(lat) + '&lon=' + encodeURIComponent(lng);
      fetch(url, { headers: { 'Accept': 'application/json' } })
        .then(function (r) { return r.ok ? r.json() : null; })
        .then(function (data) {
          if (!data || !data.display_name) { return; }
          var el = document.getElementById(descInputId);
          if (el && !el.value.trim()) {
            el.value = data.display_name.slice(0, 255);
          }
        })
        .catch(function () { /* تجاهل */ });
    }

    function placeMarker(lat, lng, fromUser) {
      if (marker) {
        marker.setLatLng([lat, lng]);
      } else {
        marker = L.marker([lat, lng], { draggable: true }).addTo(map);
        marker.on('dragend', function () {
          var p = marker.getLatLng();
          updateInputs(p.lat, p.lng);
          reverseGeocode(p.lat, p.lng);
        });
      }
      map.setView([lat, lng], 16);
      updateInputs(lat, lng);
      if (fromUser) { reverseGeocode(lat, lng); }
    }

    function updateInputs(lat, lng) {
      var la = document.getElementById(latInputId);
      var ln = document.getElementById(lngInputId);
      if (la) { la.value = Number(lat).toFixed(6); }
      if (ln) { ln.value = Number(lng).toFixed(6); }
    }

    // النقر على الخريطة يضع/ينقل الدبوس
    map.on('click', function (e) {
      placeMarker(e.latlng.lat, e.latlng.lng, true);
      setStatus('تم تحديد الموقع على الخريطة.');
    });

    // زر "تحديد موقعي"
    var gpsBtn = document.getElementById(gpsButtonId);
    if (gpsBtn && navigator.geolocation) {
      gpsBtn.addEventListener('click', function () {
        setStatus('جارٍ تحديد موقعك…');
        navigator.geolocation.getCurrentPosition(function (pos) {
          placeMarker(pos.coords.latitude, pos.coords.longitude, true);
          setStatus('تم تحديد موقعك.');
        }, function () {
          setStatus('تعذّر تحديد موقعك. يمكنك اختيار الموقع على الخريطة.');
        }, { enableHighAccuracy: true, timeout: 10000 });
      });
    } else if (gpsBtn) {
      gpsBtn.disabled = true;
    }

    // إن كانت هناك إحداثيات معبّأة سابقًا (بعد خطأ تحقق)، اعرضها.
    var existingLat = parseFloat((document.getElementById(latInputId) || {}).value);
    var existingLng = parseFloat((document.getElementById(lngInputId) || {}).value);
    if (!isNaN(existingLat) && !isNaN(existingLng) && existingLat && existingLng) {
      placeMarker(existingLat, existingLng, false);
    }
  }

  window.AHMINI_map = { init: initMap };
})();