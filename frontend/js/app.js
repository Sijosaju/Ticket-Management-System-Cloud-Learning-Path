const API = window.APP_CONFIG.API_URL;
const token = () => localStorage.getItem('token');
const user  = () => JSON.parse(localStorage.getItem('user') || 'null');

async function api(path, options = {}) {
  const r = await fetch(API + path, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...(token() ? { Authorization: `Bearer ${token()}` } : {}),
      ...(options.headers || {}),
    },
  });
  const data = r.status === 204 ? {} : await r.json();
  if (!r.ok) throw Error(data.error || 'Request failed');
  return data;
}

function nav() {
  const u = user();
  document.querySelector('#nav').innerHTML = `
    <b>Ticket<span>ly</span></b>
    <a href="index.html">Home</a>
    <a href="events.html">Events</a>
    ${u
      ? `<a href="bookings.html">My Bookings</a>
         ${u.role === 'admin' ? '<a href="admin.html">Admin</a>' : ''}
         <span style="color:var(--muted);font-size:.8rem">Hi, ${u.name || u.email}</span>
         <a href="#" onclick="logout()" style="color:var(--accent);font-size:.82rem;font-weight:600">Logout</a>`
      : `<a href="login.html">Login</a>
         <a class="nav-cta" href="register.html">Sign up free</a>`
    }`;
}

function logout() { localStorage.clear(); location.href = 'index.html'; }

function showMessage(msg, isError = true) {
  const el = document.querySelector('#message');
  if (!el) return;
  el.innerHTML = `<p class="notice${isError ? '' : ' success'}">${msg}</p>`;
  if (!isError) setTimeout(() => { el.innerHTML = ''; }, 4000);
}

function showError(e) { showMessage(e.message, true); }

const EMOJI = { Music: '🎵', Concert: '🎸', Sports: '⚽', Tech: '💻', Food: '🍔', Art: '🎨', Comedy: '😂', Conference: '🎤', Default: '🎟️' };

function categoryEmoji(cat) {
  if (!cat) return EMOJI.Default;
  const k = Object.keys(EMOJI).find(k => cat.toLowerCase().includes(k.toLowerCase()));
  return k ? EMOJI[k] : EMOJI.Default;
}

function fmtDate(d) {
  if (!d) return '';
  return new Date(d + 'T00:00:00').toLocaleDateString('en-US', { weekday: 'short', month: 'short', day: 'numeric', year: 'numeric' });
}

function fmtDateShort(d) {
  if (!d) return { day: '--', mon: '---' };
  const dt = new Date(d + 'T00:00:00');
  return {
    day: dt.getDate(),
    mon: dt.toLocaleDateString('en-US', { month: 'short' }).toUpperCase(),
  };
}

function fmtTime(t) {
  if (!t) return '';
  const [h, m] = t.split(':');
  const dt = new Date(); dt.setHours(+h, +m);
  return dt.toLocaleTimeString('en-US', { hour: 'numeric', minute: '2-digit' });
}

function eventCard(e, featured = false) {
  const imgHtml = e.image_url
    ? `<img src="${e.image_url}" alt="${e.title}" loading="lazy">`
    : `<div class="card-img-placeholder">${categoryEmoji(e.category)}</div>`;

  const minPrice = e.min_price != null ? `From $${Number(e.min_price).toFixed(2)}` : 'View tickets';

  if (featured) {
    return `
      <article class="card card-featured">
        <div class="card-img-wrap">
          ${imgHtml}
          <span class="card-category">${e.category || 'Event'}</span>
        </div>
        <div class="card-body">
          <div style="display:flex;gap:.5rem;margin-bottom:.5rem">
            <span style="font-size:.75rem;font-weight:700;color:var(--accent);text-transform:uppercase;letter-spacing:.06em">⭐ Featured</span>
          </div>
          <h3 style="font-size:1.5rem;margin-bottom:.75rem">${e.title}</h3>
          <div class="card-meta">
            <span>📅 ${fmtDate(e.event_date)}</span>
            <span>🕐 ${fmtTime(e.event_time)}</span>
            <span>📍 ${e.location}</span>
          </div>
          <div class="card-footer" style="margin-top:1.5rem">
            <span class="card-price">${minPrice}</span>
            <a class="button" href="event-details.html?id=${e.id}">Get tickets →</a>
          </div>
        </div>
      </article>`;
  }

  return `
    <article class="card">
      <div class="card-img-wrap">
        ${imgHtml}
        <span class="card-category">${e.category || 'Event'}</span>
      </div>
      <div class="card-body">
        <h3>${e.title}</h3>
        <div class="card-meta">
          <span>📅 ${fmtDate(e.event_date)}</span>
          <span>🕐 ${fmtTime(e.event_time)}</span>
          <span>📍 ${e.location}</span>
        </div>
        <div class="card-footer">
          <span class="card-price">${minPrice}</span>
          <a class="button" href="event-details.html?id=${e.id}">View →</a>
        </div>
      </div>
    </article>`;
}

document.addEventListener('DOMContentLoaded', nav);